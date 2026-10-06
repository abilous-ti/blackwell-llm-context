r"""Reproduce the published natural-data numbers from the text-free exports alone.

confirm  results/package2/confirm_qa_textfree/: recomputes every entry of analysis_qa.json (evidence
         retrieval, the 60 answer cells, the 30 primary and 12 augmentation contrasts with their
         bootstrap intervals, the overhead table, answer-line compliance, request counts) with the
         functions of analyze_qa.py and run_qa.py, and compares them exactly with the shipped
         analysis_qa.json; then checks Table 12 (tab:natural), Table 13 (tab:overhead) and the figures
         quoted in Sections 4.7 and 5.9 as printed in the manuscript.
pilot    results/natural_pilot_textfree/: recomputes the PASS tables of the 2 October exploratory
         pilot (development data) and its request counts.

  python harness/package2/verify_qa_textfree.py              (reads only the exports; no network)
  python harness/package2/verify_qa_textfree.py --rebuilt    (also checks a rebuild in natural_data/:
         question, paragraph and source digests, supporting indices, and every prompt's SHA-256,
         rebuilt from the exported indices; the local rankers' orders if their file is present)
Exit status 1 on any mismatch.
"""
import hashlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import analyze_qa as A  # noqa: E402  (imports run_qa; neither reads natural_data/ at import)

Q = A.Q
EXP = ROOT / "results" / "package2" / "confirm_qa_textfree"
PIL = ROOT / "results" / "natural_pilot_textfree"
FAIL = []


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def check(ok, what):
    print("  %-4s %s" % ("ok" if ok else "FAIL", what))
    if not ok:
        FAIL.append(what)
    return ok


def r(x, step="0.01"):
    """Half-up rounding of the decimal value, as the manuscript prints (0.305 -> 0.31)."""
    return float(Decimal(repr(x)).quantize(Decimal(step), rounding=ROUND_HALF_UP))


def pct(x):
    return int(Decimal(repr(x)).scaleb(2).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def n_numbers(x):
    if isinstance(x, dict):
        return sum(n_numbers(v) for v in x.values())
    if isinstance(x, list):
        return sum(n_numbers(v) for v in x)
    return int(isinstance(x, (int, float)) and not isinstance(x, bool))


# ---- confirm: recompute analysis_qa.json ----------------------------------------------------------
def recompute(items, rankings_rows, answers, overhead):
    """analyze_qa.analyze, step for step, on the exported rows (kept in the records' order)."""
    rankings = {}
    for x in rankings_rows:
        if x["kind"] == "local":
            rankings[(x["item"], x["ranker"])] = x["order"]
        elif x["used_for_answers"]:
            rankings[(x["item"], "rankgpt")] = x["order"]
    requests = [x for x in rankings_rows if x["kind"] == "rankgpt"] + answers + overhead
    res = {"n": {"issued": len(requests), "received": len(requests),
                 "transport_failed": sum(1 for x in requests if x["transport_failed"])},
           "evidence": {}, "answers": {}, "primary": {}, "augmentation": {}, "overhead": {}, "format": {}}
    for ds, role in (("hotpotqa", "hotpot_rank"), ("musique", "musique_rank")):
        for rk in Q.RANKED:
            rec, alls = [], []
            for it in items.values():
                if it["role"] != role or (it["id"], rk) not in rankings:
                    continue
                sup = set(it["supporting"])
                top = set(rankings[(it["id"], rk)][:Q.BUDGET[ds]])
                rec.append(len(top & sup) / len(sup))
                alls.append(float(sup <= top))
            res["evidence"]["%s|%s" % (ds, rk)] = {"n": len(rec), "support_recall": A.boot_mean(rec),
                                                   "all_supporting": A.boot_mean(alls)}
    per = defaultdict(dict)
    has_tag = defaultdict(lambda: [0, 0])
    for x in answers:
        if x["transport_failed"]:
            continue
        per[(x["role"], x["model"], x["cond"])][x["item"]] = (x["em"], x["f1"])
        t = has_tag[x["model"]]
        t[0] += 1
        t[1] += x["has_answer_line"]
    res["format"] = {m: {"replies": v[0], "with_answer_line": v[1]} for m, v in has_tag.items()}
    for (role, m, cond), d in per.items():
        res["answers"]["%s|%s|%s" % (role, m, cond)] = {"n": len(d), "em": A.boot_mean([v[0] for v in d.values()]),
                                                       "f1": A.boot_mean([v[1] for v in d.values()])}
    for role in ("hotpot_rank", "musique_rank"):
        for m in Q.ANSWER_MODELS:
            for rk in A.LOCAL:
                a, b = per.get((role, m, "rankgpt"), {}), per.get((role, m, rk), {})
                common = sorted(set(a) & set(b))
                est, lo, hi = A.boot_mean([a[i][1] - b[i][1] for i in common], level=1 - 0.05 / 15)
                res["primary"]["%s|%s|rankgpt-%s" % (role, m, rk)] = {
                    "n": len(common), "estimate": est, "lower": lo, "upper": hi,
                    "verified_positive": lo is not None and lo > 0, "verified_negative": hi is not None and hi < 0}
    for m in Q.ANSWER_MODELS:
        g = per.get(("hotpot_aug", m, "gold"), {})
        for cond in ("gold+dist", "dist+gold"):
            o = per.get(("hotpot_aug", m, cond), {})
            common = sorted(set(g) & set(o))
            for k, name in ((0, "em"), (1, "f1")):
                est, lo, hi = A.boot_mean([o[i][k] - g[i][k] for i in common], level=1 - 0.05 / 6)
                res["augmentation"]["%s|%s - gold|%s" % (m, cond, name)] = {
                    "n": len(common), "estimate": est, "lower": lo, "upper": hi, "harm_verified": hi is not None and hi < 0}
    for m in Q.OVERHEAD_MODELS:
        for size in Q.SIZES:
            rows = [x for x in overhead if x["model"] == m and x["size"] == size and not x["transport_failed"]]
            if not rows:
                continue
            agree, tau, rec = [], [], []
            for it_id in sorted({x["item"] for x in rows}):
                byo = {x["order_idx"]: x for x in rows if x["item"] == it_id}
                sup = set(items[it_id]["supporting"])
                k = len(sup)
                orders = {}
                for j, x in byo.items():
                    orders[j] = x["order"]
                    rec.append(len(set(orders[j][:k]) & sup) / k)
                if len(orders) == 2:
                    agree.append(len(set(orders[0][:k]) & set(orders[1][:k])) / k)
                    tau.append(Q.kendall_tau(orders[0], orders[1]))
            res["overhead"]["%s|%d" % (m, size)] = {
                "requests": len(rows), "latency_s": A.boot_mean([x["wall_s"] for x in rows]),
                "input_tokens": A.boot_mean([x["input_tokens"] or 0 for x in rows]),
                "output_tokens": A.boot_mean([x["output_tokens"] or 0 for x in rows]),
                "extra_attempts": sum(x["attempts"] - 1 for x in rows),
                "complete_parses": sum(x["parse"]["complete"] for x in rows),
                "topK_agreement": A.boot_mean(agree), "kendall_tau": A.boot_mean(tau), "support_recall": A.boot_mean(rec)}
    return json.loads(json.dumps(res))


# Floating-point results are compared with a tolerance: summation order can differ between
# platforms and Python builds by a few units in the last place (5.3e-15 has been observed), which
# is not a difference in any reported figure.
TOL = 1e-12


def same_num(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=TOL, abs_tol=TOL)
    return a == b


def diff(a, b, path="$", out=None):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append("%s.%s missing on one side" % (path, k))
            else:
                diff(a[k], b[k], "%s.%s" % (path, k), out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, "%s[%d]" % (path, i), out)
    elif not same_num(a, b):
        out.append("%s: shipped %r, recomputed %r" % (path, a, b))
    return out


# As printed in the manuscript: Table 12 (tab:natural), columns per dataset: all found, then F1 for
# Haiku, GPT-5.5 and DeepSeek ('-' where not applicable).
TABLE12 = {
    "none":    {"hotpotqa": (None, 0.44, 0.71, 0.60), "musique": (None, 0.25, 0.47, 0.35)},
    "full":    {"hotpotqa": (None, 0.77, 0.83, 0.79), "musique": (None, 0.71, 0.80, 0.74)},
    "bm25":    {"hotpotqa": (0.23, 0.43, 0.74, 0.52), "musique": (0.13, 0.22, 0.52, 0.32)},
    "mmr":     {"hotpotqa": (0.31, 0.48, 0.74, 0.57), "musique": (0.07, 0.21, 0.54, 0.35)},
    "bge":     {"hotpotqa": (0.47, 0.54, 0.78, 0.63), "musique": (0.28, 0.37, 0.54, 0.45)},
    "e5":      {"hotpotqa": (0.43, 0.53, 0.76, 0.62), "musique": (0.32, 0.38, 0.58, 0.46)},
    "minilm":  {"hotpotqa": (0.40, 0.52, 0.76, 0.61), "musique": (0.27, 0.37, 0.64, 0.50)},
    "rankgpt": {"hotpotqa": (0.82, 0.77, 0.82, 0.79), "musique": (0.80, 0.65, 0.82, 0.77)},
}
# Table 13 (tab:overhead): latency s, input tokens, output tokens, parsed, top-K agreement, Kendall tau, recall at K.
TABLE13 = {
    "Haiku-4.5|5": (1.3, 838, 22, 40, 0.99, 0.79, 0.97), "Haiku-4.5|10": (1.5, 1448, 42, 40, 0.95, 0.67, 0.87),
    "Haiku-4.5|20": (1.7, 2789, 82, 40, 0.92, 0.55, 0.79), "GPT-5.5|5": (5.2, 742, 363, 40, 1.00, 0.91, 0.98),
    "GPT-5.5|10": (7.8, 1291, 583, 40, 1.00, 0.81, 0.91), "GPT-5.5|20": (10.7, 2484, 860, 40, 0.93, 0.74, 0.88),
}


def verify_confirm():
    print("CONFIRM: %s" % EXP.relative_to(ROOT).as_posix())
    items = {x["id"]: x for x in jl(EXP / "items.jsonl")}
    rk = jl(EXP / "rankings.jsonl")
    answers, overhead, aug = jl(EXP / "answers.jsonl"), jl(EXP / "overhead.jsonl"), jl(EXP / "augmentation.jsonl")
    shipped = json.load(open(EXP / "analysis_qa.json", encoding="utf-8"))
    roles = Counter(x["role"] for x in items.values())
    check(len(items) == 420 and roles == {"hotpot_rank": 200, "hotpot_aug": 100, "musique_rank": 100, "musique_overhead": 20},
          "items: %d %s" % (len(items), dict(roles)))
    n_local = sum(1 for x in rk if x["kind"] == "local")
    n_gpt = sum(1 for x in rk if x["kind"] == "rankgpt")
    check((n_local, n_gpt, len(answers), len(overhead), len(aug)) == (2100, 600, 8400, 240, 100),
          "rows: local rankings %d, RankGPT requests %d, answers %d, overhead %d, augmentation items %d"
          % (n_local, n_gpt, len(answers), len(overhead), len(aug)))
    ids = [x["id"] for x in rk if x["kind"] == "rankgpt"] + [x["id"] for x in answers + overhead]
    check(len(ids) == len(set(ids)) == 9240, "request ids unique: %d" % len(set(ids)))
    sp = json.load(open(EXP / "splits.json", encoding="utf-8"))
    for ds, v in sp["datasets"].items():
        conf = (EXP / v["confirmation_file"]).read_text(encoding="utf-8").rstrip("\n")
        check(hashlib.sha256(conf.encode()).hexdigest() == v["confirmation_sha256"] and len(conf.split("\n")) == v["confirmation_size"],
              "%s confirmation pool: %d ids, SHA-256 as recorded in splits.json" % (ds, v["confirmation_size"]))
        confset = set(conf.split("\n"))
        check(all(x["id"] in confset for x in v["confirm_items"]) and not confset & set(v["dev"] + v["excluded"]),
              "%s: confirmatory items in the confirmation pool, which excludes the dev pool and the excluded ids" % ds)

    res = recompute(items, rk, answers, overhead)
    d = diff(shipped, res)
    check(not d, "analysis_qa.json recomputed from the export: %s" % (
        "agree within %g (all %d numbers, bootstrap intervals included)" % (TOL, n_numbers(shipped)) if not d else "%d differences" % len(d)))
    for line in d[:15]:
        print("         " + line)

    print(" published figures")
    ev = res["evidence"]
    h =[ev["hotpotqa|%s" % k]["all_supporting"][0] for k in A.LOCAL]
    m = [ev["musique|%s" % k]["all_supporting"][0] for k in A.LOCAL]
    check((pct(ev["hotpotqa|rankgpt"]["all_supporting"][0]), pct(ev["musique|rankgpt"]["all_supporting"][0])) == (82, 80),
          "RankGPT all found: HotpotQA %.3f, MuSiQue %.3f (published 82%%, 80%%)"
          % (ev["hotpotqa|rankgpt"]["all_supporting"][0], ev["musique|rankgpt"]["all_supporting"][0]))
    check((pct(min(h)), pct(max(h)), pct(min(m)), pct(max(m))) == (23, 47, 7, 32),
          "baselines all found: HotpotQA %.3f-%.3f, MuSiQue %.3f-%.3f (published 23-47%%, 7-32%%)" % (min(h), max(h), min(m), max(m)))
    cells = [k for k in res["answers"]]
    same = sum(1 for k in cells if k in shipped["answers"] and res["answers"][k]["n"] == shipped["answers"][k]["n"]
               and same_num(res["answers"][k]["em"][0], shipped["answers"][k]["em"][0])
               and same_num(res["answers"][k]["f1"][0], shipped["answers"][k]["f1"][0]))
    check(len(cells) == 60 and same == 60, "answer cells (role x model x condition): %d recomputed, %d with identical n and EM and F1 means (tolerance %g)" % (len(cells), same, TOL))
    miss = [x for x in answers if x["transport_failed"]]
    check(len(miss) == 13 and res["n"]["transport_failed"] == 13 and len({x["item"] for x in miss}) == 5
          and all(x["missing_reason"] == "content_filter" for x in miss),
          "missing requests: %d, on %d questions, all refused by the provider's content filter (%s)"
          % (len(miss), len({x["item"] for x in miss}), dict(Counter(x["model"] for x in miss))))
    bad12 = []
    for cond, row in TABLE12.items():
        for ds, (allf, *f1s) in row.items():
            role = "hotpot_rank" if ds == "hotpotqa" else "musique_rank"
            if allf is not None and r(ev["%s|%s" % (ds, cond)]["all_supporting"][0]) != allf:
                bad12.append("%s %s all found" % (cond, ds))
            for mdl, v in zip(Q.ANSWER_MODELS, f1s):
                if r(res["answers"]["%s|%s|%s" % (role, mdl, cond)]["f1"][0]) != v:
                    bad12.append("%s %s %s F1" % (cond, ds, mdl))
    check(not bad12, "Table 12 (tab:natural): 60 printed values %s" % ("reproduced" if not bad12 else "MISMATCH %s" % bad12))
    bad13 = []
    for key, (lat, tin, tout, parsed, ag, tau, rec) in TABLE13.items():
        o = res["overhead"][key]
        got = (r(o["latency_s"][0], "0.1"), r(o["input_tokens"][0], "1"), r(o["output_tokens"][0], "1"), o["complete_parses"],
               r(o["topK_agreement"][0]), r(o["kendall_tau"][0]), r(o["support_recall"][0]))
        if got != (lat, tin, tout, parsed, ag, tau, rec) or o["requests"] != 40:
            bad13.append("%s %s" % (key, got))
    check(not bad13, "Table 13 (tab:overhead): 42 printed values %s" % ("reproduced" if not bad13 else "MISMATCH %s" % bad13))
    gpt = [x for x in rk if x["kind"] == "rankgpt"]
    check(sum(x["parse"]["complete"] for x in gpt) == 591, "RankGPT complete rankings: %d of %d (published 591 of 600)"
          % (sum(x["parse"]["complete"] for x in gpt), len(gpt)))
    check(sum(x["parse"]["complete"] for x in overhead) == 240 and sum(x["attempts"] - 1 for x in overhead) == 0,
          "overhead: all %d rankings parsed, none needed a retry (published: all 240)" % len(overhead))
    pr = res["primary"]
    weakest = min(pr.values(), key=lambda v: v["lower"])
    rng = lambda role, mdl: [pr["%s|%s|rankgpt-%s" % (role, mdl, k)]["estimate"] for k in A.LOCAL]
    spans = {mdl: (r(min(rng("hotpot_rank", mdl))), r(max(rng("hotpot_rank", mdl)))) for mdl in Q.ANSWER_MODELS}
    mus = [v["estimate"] for k, v in pr.items() if k.startswith("musique")]
    check(all(v["verified_positive"] for v in pr.values()) and spans == {"Haiku-4.5": (0.23, 0.33), "DeepSeek-V4-Pro": (0.16, 0.27), "GPT-5.5": (0.04, 0.09)}
          and (r(min(mus)), r(max(mus))) == (0.18, 0.45),
          "primary contrasts: 30/30 intervals exclude zero; HotpotQA %s, MuSiQue %.2f-%.2f (published 0.23-0.33, 0.16-0.27, 0.04-0.09; 0.18-0.45)"
          % (spans, r(min(mus)), r(max(mus))))
    key_w = [k for k, v in pr.items() if v is weakest][0]
    check(key_w == "hotpot_rank|GPT-5.5|rankgpt-bge" and r(weakest["lower"], "0.0001") == 0.0029 and weakest["n"] == 199,
          "weakest contrast %s: lower bound %.4f on %d questions (published 0.0029 on 199)" % (key_w, weakest["lower"], weakest["n"]))
    au = res["augmentation"]
    est = [v["estimate"] for v in au.values()]
    lo_f1 = min(v["lower"] for k, v in au.items() if k.endswith("f1"))
    lo_em = min(v["lower"] for k, v in au.items() if k.endswith("em"))
    up = lambda x: float(Decimal(repr(x)).quantize(Decimal("0.001"), rounding=ROUND_CEILING))   # bounds round outward
    check(not any(v["harm_verified"] for v in au.values()) and (r(min(est)), r(max(est))) == (-0.03, 0.02)
          and (up(-lo_f1), up(-lo_em)) == (0.078, 0.092),
          "augmentation: no interval excludes zero; changes %.2f to %.2f; lowest bounds %.5f F1, %.5f EM, i.e. losses "
          "beyond %.3f F1 / %.3f EM excluded (published -0.03 to +0.02; 0.078, 0.092)"
          % (r(min(est)), r(max(est)), lo_f1, lo_em, up(-lo_f1), up(-lo_em)))


# ---- pilot -------------------------------------------------------------------------------------
# REPORT.md (generated by stage2_pilot.py report): PASS / scored replies by model, dataset, task and
# source condition (none, own, other, both).
REPORT = {
    ("DeepSeek-V4-Pro", "hotpotqa", "original-bridge"): ("17/24", "-", "38/48", "48/48"),
    ("DeepSeek-V4-Pro", "hotpotqa", "original-comparison"): ("18/24", "-", "38/48", "45/48"),
    ("DeepSeek-V4-Pro", "hotpotqa", "single-bridge"): ("11/18", "18/18", "9/18", "36/36"),
    ("DeepSeek-V4-Pro", "hotpotqa", "single-comparison"): ("31/42", "42/42", "17/42", "84/84"),
    ("DeepSeek-V4-Pro", "tatqa", "table"): ("0/51", "36/51", "2/51", "81/102"),
    ("DeepSeek-V4-Pro", "tatqa", "table-text"): ("3/30", "-", "31/60", "48/60"),
    ("DeepSeek-V4-Pro", "tatqa", "text"): ("2/54", "47/54", "6/54", "95/108"),
    ("Haiku-4.5", "hotpotqa", "original-bridge"): ("15/24", "-", "33/48", "48/48"),
    ("Haiku-4.5", "hotpotqa", "original-comparison"): ("17/24", "-", "24/48", "42/48"),
    ("Haiku-4.5", "hotpotqa", "single-bridge"): ("9/18", "18/18", "3/18", "36/36"),
    ("Haiku-4.5", "hotpotqa", "single-comparison"): ("22/42", "42/42", "0/42", "84/84"),
    ("Haiku-4.5", "tatqa", "table"): ("0/51", "48/51", "3/51", "94/102"),
    ("Haiku-4.5", "tatqa", "table-text"): ("0/30", "-", "29/60", "48/60"),
    ("Haiku-4.5", "tatqa", "text"): ("0/54", "48/54", "3/54", "100/108"),
}


def verify_pilot():
    print("PILOT (2 October, development data): %s" % PIL.relative_to(ROOT).as_posix())
    items = {x["id"]: x for x in jl(PIL / "items.jsonl")}
    req = jl(PIL / "requests.jsonl")
    s1 = jl(PIL / "stage1_audit.jsonl")
    check(len(items) == 81 and Counter(x["dataset"] for x in items.values()) == {"tatqa": 45, "hotpotqa": 36} and len(s1) == 40,
          "items: %d (%s); Stage 1 audit records: %d" % (len(items), dict(Counter(x["dataset"] for x in items.values())), len(s1)))
    check(len(req) == 2430 and Counter(x["model"] for x in req) == {"Haiku-4.5": 1215, "DeepSeek-V4-Pro": 1215}
          and not any(x["transport_failed"] for x in req) and len({x["id"] for x in req}) == 2430,
          "requests: %d, %s, transport failures %d" % (len(req), dict(Counter(x["model"] for x in req)), sum(x["transport_failed"] for x in req)))
    check(dict(Counter(x["stop_reason"] for x in req)) == {"end_turn": 1215, "stop": 1215}, "stop reasons %s" % dict(Counter(x["stop_reason"] for x in req)))

    def rel(x, it):
        if it["own"] == "AB":
            return "none" if x["condition"] == "none" else "both" if x["condition"] in ("AB", "BA") else "other"
        return ("own" if x["condition"] == it["own"] else "none" if x["condition"] == "none" else
                "both" if x["condition"] in ("AB", "BA") else "other")
    agg = defaultdict(lambda: [0, 0])
    for x in req:
        it = items[x["item"]]
        a = agg[(x["model"], it["dataset"], it["task"], rel(x, it))]
        a[0] += x["pass"]
        a[1] += 1
    got = {k: tuple("%d/%d" % tuple(agg[k + (c,)]) if k + (c,) in agg else "-" for c in ("none", "own", "other", "both"))
           for k in {k[:3] for k in agg}}
    check(got == REPORT, "PASS table of the generated pilot report (14 rows x 4 conditions) %s"
          % ("reproduced" if got == REPORT else "MISMATCH %s" % {k: (got.get(k), v) for k, v in REPORT.items() if got.get(k) != v}))
    num = [x for x in req if items[x["item"]]["score_kind"] == "number"]
    check(sum(1 for x in num if not x["has_number"]) == 7 and len(num) == 510,
          "numeric replies without any number: %d of %d (report: 7 of 510)" % (sum(1 for x in num if not x["has_number"]), len(num)))
    f1s = sorted(x["f1"] for x in req if x["f1"] is not None and rel(x, items[x["item"]]) in ("own", "both"))
    check(len(f1s) == 210 and sum(v >= 0.5 for v in f1s) == 176 and r(f1s[len(f1s) // 2]) == 0.71,
          "long answers with the answering source present: median F1 %.2f, %d of %d at or above 0.5 (report: 0.71, 176 of 210)"
          % (f1s[len(f1s) // 2], sum(v >= 0.5 for v in f1s), len(f1s)))
    tat = defaultdict(lambda: [0, 0])
    for x in req:
        it = items[x["item"]]
        if it["dataset"] != "tatqa" or it["exclusive"] is False:
            continue
        c = rel(x, it) if it["own"] != "AB" else ("one" if x["condition"] in ("A", "B") else rel(x, it))
        a = tat[(x["model"], it["task"], c)]
        a[0] += x["pass"]
        a[1] += 1
    want = {("Haiku-4.5", "table"): ("0/45", "45/45", "0/45", "88/90"), ("Haiku-4.5", "text"): ("0/51", "45/51", "0/51", "94/102"),
            ("DeepSeek-V4-Pro", "table"): ("0/45", "33/45", "0/45", "71/90"), ("DeepSeek-V4-Pro", "text"): ("2/51", "44/51", "3/51", "89/102"),
            ("Haiku-4.5", "table-text"): ("0/30", "48/60", "29/60"), ("DeepSeek-V4-Pro", "table-text"): ("3/30", "48/60", "31/60")}
    got2 = {}
    for (mdl, task), v in want.items():
        conds = ("none", "own", "other", "both") if task != "table-text" else ("none", "both", "one")
        got2[(mdl, task)] = tuple("%d/%d" % tuple(tat[(mdl, task, c)]) for c in conds)
    diffs = {k: (got2[k], v) for k, v in want.items() if got2[k] != v}
    print("  info TAT-QA exclusive-item table of the hand-written STAGE2-REPORT.md: %s" %
          ("reproduced" if not diffs else "differs in %d of 6 rows (recomputed, report): %s" % (len(diffs), diffs)))


# ---- optional: check a rebuild from the public datasets -------------------------------------------
def verify_rebuilt():
    print("REBUILT INPUTS in natural_data/ (digests and prompts from the exported indices)")
    sha = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
    nd = ROOT / "natural_data"
    src = {x["id"]: x for x in jl(nd / "package2" / "items_confirm.jsonl")}
    exp = {x["id"]: x for x in jl(EXP / "items.jsonl")}
    bad = [i for i, e in exp.items() if i not in src or sha(src[i]["question"]) != e["question_sha256"]
           or [sha(p["title"]) for p in src[i]["paragraphs"]] != e["title_sha256"]
           or [sha(p["text"]) for p in src[i]["paragraphs"]] != e["text_sha256"]
           or [k for k, p in enumerate(src[i]["paragraphs"]) if p["supporting"]] != e["supporting"]
           or len(src[i]["answers"]) != e["n_gold_answers"] or src[i]["role"] != e["role"]]
    check(not bad and len(src) == len(exp), "confirm items: %d of %d match (question, every title and text, supporting indices)" % (len(exp) - len(bad), len(exp)))
    n = nbad = 0
    rk = jl(EXP / "rankings.jsonl")
    for x in [y for y in rk if y["kind"] == "rankgpt"] + jl(EXP / "overhead.jsonl"):
        n += 1
        nbad += sha(Q.rank_prompt(src[x["item"]], x["pool"])) != x["prompt_sha256"]
    for x in jl(EXP / "answers.jsonl"):
        it, idx = src[x["item"]], x["context"]
        if idx is None:
            p = Q.ANSWER_NONE.format(q=it["question"])
        else:
            p = Q.ANSWER_CTX.format(ctx="\n".join("[%d] %s" % (k + 1, Q.passage(it["paragraphs"][i])) for k, i in enumerate(idx)),
                                    q=it["question"])
        n += 1
        nbad += sha(p) != x["prompt_sha256"]
    check(not nbad, "confirm prompts rebuilt from the exported pools and context indices: %d of %d match their SHA-256" % (n - nbad, n))
    lp = nd / "package2" / "rankings_local_confirm.jsonl"
    if lp.exists():
        loc = {(y["id"], y["ranker"]): y["order"] for y in jl(lp)}
        local = [x for x in rk if x["kind"] == "local"]
        mism = [x for x in local if loc.get((x["item"], x["ranker"])) != x["order"]]
        check(not mism, "local rankers: %d of %d orders match" % (len(local) - len(mism), len(local)))
    sys.path.insert(0, str(ROOT / "harness" / "natural"))
    import stage2_pilot as P
    pit = {x["id"]: x for x in json.load(open(nd / "stage2" / "items.json", encoding="utf-8"))}
    pexp = {x["id"]: x for x in jl(PIL / "items.jsonl")}
    bad = [i for i, e in pexp.items() if i not in pit or (sha(pit[i]["question"]), sha(pit[i]["A"]), sha(pit[i]["B"]))
           != (e["question_sha256"], e["A_sha256"], e["B_sha256"])]
    check(not bad, "pilot items: %d of %d match (question, source A, source B)" % (len(pexp) - len(bad), len(pexp)))
    req = jl(PIL / "requests.jsonl")
    nbad = sum(sha(P.prompt(pit[x["item"]], x["condition"])) != x["prompt_sha256"] for x in req)
    check(not nbad, "pilot prompts rebuilt: %d of %d match their SHA-256" % (len(req) - nbad, len(req)))


def main():
    verify_confirm()
    print()
    verify_pilot()
    if "--rebuilt" in sys.argv:
        print()
        verify_rebuilt()
    print("\n%s" % ("ALL CHECKS PASSED" if not FAIL else "%d CHECK(S) FAILED" % len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
