r"""Analysis of the natural-data benchmarks, as fixed in PROTOCOL.md (Sections 2-5).

  evidence      per dataset and ranker: support recall and all-supporting-retrieved at the budget K
  answers       per dataset, answer model and condition: exact match and F1 (official HotpotQA
                definitions; maximum over MuSiQue's aliases)
  primary       RankGPT minus each of the five other rankers on F1, per answer model: 15 paired
                differences per dataset, simultaneous 95% intervals (paired bootstrap over
                questions, Bonferroni over the 15)
  augmentation  (gold+dist) - gold and (dist+gold) - gold per answer model, F1 and exact match,
                simultaneous 95% over the six per metric
  overhead      per ranking model and candidate count: latency, tokens, extra attempts, complete
                parses, top-K agreement and Kendall tau across input orders, support recall at K
All intervals: percentile bootstrap, 4,000 resamples, seed 20261005.

  python harness/package2/analyze_qa.py [--set confirm|pilot]
"""
import argparse
import io
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_qa as Q  # noqa: E402

B_RESAMPLES = 4000
LOCAL = ("bm25", "mmr", "bge", "e5", "minilm")


def boot_mean(values, level=0.95, seed=20261005):
    n = len(values)
    if n == 0:
        return None, None, None
    m = sum(values) / n
    rng = random.Random(seed)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(B_RESAMPLES))
    lo = means[int((1 - level) / 2 * B_RESAMPLES)]
    hi = means[min(B_RESAMPLES - 1, int((1 + level) / 2 * B_RESAMPLES))]
    return m, lo, hi


def analyze(out_dir):
    items = {json.loads(l)["id"]: json.loads(l) for l in open(Q.ND / Q.SET["items"], encoding="utf-8")}
    st = Q.load_records(out_dir / "records.jsonl")
    R = st["receipt"]
    rankings = Q.local_rankings()
    rankings.update(Q.rankgpt_rankings(st, items))
    res = {"n": {"issued": len(st["issued"]), "received": len(R),
                 "transport_failed": sum(1 for r in R.values() if r.get("transport_failed"))},
           "evidence": {}, "answers": {}, "primary": {}, "augmentation": {}, "overhead": {}, "format": {}}
    # evidence retrieval
    for ds, role in (("hotpotqa", "hotpot_rank"), ("musique", "musique_rank")):
        for rk in Q.RANKED:
            rec, alls = [], []
            for it in items.values():
                if it["role"] != role or (it["id"], rk) not in rankings:
                    continue
                sup = {i for i, p in enumerate(it["paragraphs"]) if p["supporting"]}
                top = set(rankings[(it["id"], rk)][:Q.BUDGET[ds]])
                rec.append(len(top & sup) / len(sup))
                alls.append(float(sup <= top))
            res["evidence"]["%s|%s" % (ds, rk)] = {"n": len(rec), "support_recall": boot_mean(rec),
                                                   "all_supporting": boot_mean(alls)}
    # answers
    per = defaultdict(dict)          # (role, model, cond) -> {item: (em, f1)}
    has_tag = defaultdict(lambda: [0, 0])
    for rc in R.values():
        if rc.get("kind") != "answer" or rc.get("transport_failed"):
            continue
        it = items[rc["item"]]
        em, f1, _ = Q.score(rc.get("raw_text"), it["answers"])
        per[(rc["role"], rc["model"], rc["cond"])][rc["item"]] = (em, f1)
        t = has_tag[rc["model"]]
        t[0] += 1
        t[1] += bool(Q.re.search(r"(?:final answer|answer)\s*[:\-]", rc.get("raw_text") or "", Q.re.I))
    res["format"] = {m: {"replies": v[0], "with_answer_line": v[1]} for m, v in has_tag.items()}
    for (role, m, cond), d in per.items():
        ems = [v[0] for v in d.values()]
        f1s = [v[1] for v in d.values()]
        res["answers"]["%s|%s|%s" % (role, m, cond)] = {"n": len(d), "em": boot_mean(ems), "f1": boot_mean(f1s)}
    # primary: RankGPT minus each local ranker on F1, per model; 15 per dataset, Bonferroni
    for role in ("hotpot_rank", "musique_rank"):
        for m in Q.ANSWER_MODELS:
            for rk in LOCAL:
                a, b = per.get((role, m, "rankgpt"), {}), per.get((role, m, rk), {})
                common = sorted(set(a) & set(b))
                diffs = [a[i][1] - b[i][1] for i in common]
                est, lo, hi = boot_mean(diffs, level=1 - 0.05 / 15)
                res["primary"]["%s|%s|rankgpt-%s" % (role, m, rk)] = {
                    "n": len(diffs), "estimate": est, "lower": lo, "upper": hi,
                    "verified_positive": lo is not None and lo > 0, "verified_negative": hi is not None and hi < 0}
    # augmentation: six contrasts per metric, Bonferroni
    for m in Q.ANSWER_MODELS:
        g = per.get(("hotpot_aug", m, "gold"), {})
        for cond in ("gold+dist", "dist+gold"):
            o = per.get(("hotpot_aug", m, cond), {})
            common = sorted(set(g) & set(o))
            for k, name in ((0, "em"), (1, "f1")):
                diffs = [o[i][k] - g[i][k] for i in common]
                est, lo, hi = boot_mean(diffs, level=1 - 0.05 / 6)
                res["augmentation"]["%s|%s - gold|%s" % (m, cond, name)] = {
                    "n": len(diffs), "estimate": est, "lower": lo, "upper": hi,
                    "harm_verified": hi is not None and hi < 0}
    # overhead
    for m in Q.OVERHEAD_MODELS:
        for size in Q.SIZES:
            rows = [rc for rc in R.values() if rc.get("kind") == "overhead" and rc["model"] == m
                    and rc["size"] == size and not rc.get("transport_failed")]
            if not rows:
                continue
            lat = [rc["wall_s"] for rc in rows]
            tin = [Q.toks(rc)[0] for rc in rows]
            tout = [Q.toks(rc)[1] for rc in rows]
            extra = sum(len(rc.get("attempts") or []) - 1 for rc in rows)
            complete = sum(Q.parse_ranking(rc.get("raw_text"), len(rc["pool"]))[1]["complete"] for rc in rows)
            agree, tau, rec = [], [], []
            for it_id in sorted({rc["item"] for rc in rows}):
                byo = {rc["order_idx"]: rc for rc in rows if rc["item"] == it_id}
                it = items[it_id]
                sup = {i for i, p in enumerate(it["paragraphs"]) if p["supporting"]}
                k = len(sup)
                orders = {}
                for j, rc in byo.items():
                    o, _ = Q.parse_ranking(rc.get("raw_text"), len(rc["pool"]))
                    orders[j] = [rc["pool"][x] for x in o]
                    rec.append(len(set(orders[j][:k]) & sup) / k)
                if len(orders) == 2:
                    agree.append(len(set(orders[0][:k]) & set(orders[1][:k])) / k)
                    tau.append(Q.kendall_tau(orders[0], orders[1]))
            res["overhead"]["%s|%d" % (m, size)] = {
                "requests": len(rows), "latency_s": boot_mean(lat), "input_tokens": boot_mean(tin),
                "output_tokens": boot_mean(tout), "extra_attempts": extra, "complete_parses": complete,
                "topK_agreement": boot_mean(agree), "kendall_tau": boot_mean(tau), "support_recall": boot_mean(rec)}
    return res


def ci(t, nd=2):
    if not t or t[0] is None:
        return "-"
    return "%.*f [%.*f, %.*f]" % (nd, t[0], nd, t[1], nd, t[2])


def report(res):
    L = ["requests: issued %(issued)d, received %(received)d, transport failures %(transport_failed)d" % res["n"], ""]
    L.append("EVIDENCE RETRIEVAL at the budget K (mean [95% CI]): support recall | all supporting retrieved")
    for k, v in res["evidence"].items():
        L.append("  %-18s n=%3d  %s | %s" % (k, v["n"], ci(v["support_recall"]), ci(v["all_supporting"])))
    L.append("")
    L.append("ANSWERS (mean [95% CI]): exact match | F1")
    for k in sorted(res["answers"]):
        v = res["answers"][k]
        L.append("  %-40s n=%3d  %s | %s" % (k, v["n"], ci(v["em"]), ci(v["f1"])))
    L.append("")
    L.append("PRIMARY: RankGPT minus each ranker, F1 (estimate [simultaneous 95%, 15 per dataset])")
    for k, v in res["primary"].items():
        tag = "RankGPT better" if v["verified_positive"] else ("RankGPT worse" if v["verified_negative"] else "")
        L.append("  %-40s n=%3d  %s %s" % (k, v["n"], ci((v["estimate"], v["lower"], v["upper"])), tag))
    L.append("")
    L.append("AUGMENTATION (estimate [simultaneous 95%, 6 per metric]); negative = harm")
    for k, v in res["augmentation"].items():
        L.append("  %-40s n=%3d  %s %s" % (k, v["n"], ci((v["estimate"], v["lower"], v["upper"])), "HARM" if v["harm_verified"] else ""))
    L.append("")
    L.append("OVERHEAD: latency s | input tok | output tok | extra attempts | complete parses | top-K agreement | Kendall tau | support recall")
    for k, v in res["overhead"].items():
        L.append("  %-16s %s | %s | %s | %d | %d/%d | %s | %s | %s" % (
            k, ci(v["latency_s"], 1), ci(v["input_tokens"], 0), ci(v["output_tokens"], 0), v["extra_attempts"],
            v["complete_parses"], v["requests"], ci(v["topK_agreement"]), ci(v["kendall_tau"]), ci(v["support_recall"])))
    L.append("")
    L.append("Answer-line compliance: " + "; ".join("%s %d/%d" % (m, v["with_answer_line"], v["replies"]) for m, v in res["format"].items()))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=tuple(Q.SETS), default="confirm")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    Q.SET.update(Q.SETS[a.set])
    out = Path(a.out) if a.out else Q.ND / Q.SET["out"]
    res = analyze(out)
    text = report(res)
    (out / "analysis_qa.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (out / "analysis_qa.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
