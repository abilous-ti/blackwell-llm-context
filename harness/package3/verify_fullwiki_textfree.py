r"""Reproduce package 3's published numbers from the text-free export alone.

results/package3/confirm_fullwiki_textfree/: recomputes every entry of analysis_fullwiki.json (request
accounting, retrieval coverage, the evidence table, the 72 answer cells, the primary (15), secondary
(30), evidence-criterion (5) and worst-case (15) contrasts with their bootstrap intervals, RankGPT
resource use, answer-line compliance and the verdict) with the functions of analyze_fullwiki.py and
analyze_qa.py, and compares them with the shipped analysis_fullwiki.json, floating-point numbers within
a tolerance of 1e-12. It regenerates analysis_fullwiki.md from the recomputed results with
analyze_fullwiki.report, and the runner's summary.txt, and compares both; checks the export's internal
consistency, the exclusions against package 2's export, and the frozen code in this repository against
the frozen digests; then checks Table tab:fullwiki and the figures quoted in sec:natural,
sec:results-natural and the limitations as printed in the manuscript.

The freeze (results/package3/FREEZE_fullwiki.json) lists every candidate title, so the authors keep it
and it is not in the repository. provenance.json records its SHA-256 and every digest it lists, and
those recorded digests serve every check below. Where the freeze file itself is present (the authors'
copy), it is also compared with the export; where it is absent, those comparisons print "freeze not
public; skipped" and everything else runs. FULLWIKI_FREEZE=<path> reads the freeze from another path.

  python harness/package3/verify_fullwiki_textfree.py            (reads the export and package 2's export;
                                                                  no network)
  python harness/package3/verify_fullwiki_textfree.py --rebuilt  (also rebuilds the inputs from the public
         parquet natural_data/hotpot_dev_fullwiki.parquet, with PyArrow: the draw, the 300 confirmatory
         and 10 smoke items, BM25's document frequencies and all 7,800 prompts, checked against the
         exported and frozen SHA-256 digests; the local rankers' orders if their file is present)
  python harness/package3/verify_fullwiki_textfree.py --rebuilt --write
         (then writes the rebuilt items_confirm.jsonl, items_smoke.jsonl and idf_fullwiki.json to
         natural_data/package3/, each only if absent and only if its SHA-256 equals the frozen digest)
Exit status 1 on any mismatch; a skipped check is not a mismatch.
"""
import hashlib
import io
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True          # never write bytecode next to package 2's modules
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "package2"))
import analyze_fullwiki as AF  # noqa: E402  (imports run_fullwiki, analyze_qa, freeze_fullwiki; none reads natural_data at import)
import fullwiki_data as FD  # noqa: E402  (conversion, eligibility, draw, document frequencies; PyArrow only in FD.load)
import verify_qa_textfree as V  # noqa: E402  (package 2's helpers: tolerance comparison, rounding as printed)

RF, A, Q = AF.RF, AF.A, AF.Q
RES3 = ROOT / "results" / "package3"
EXP = RES3 / "confirm_fullwiki_textfree"
FREEZE = Path(os.environ.get("FULLWIKI_FREEZE") or RES3 / "FREEZE_fullwiki.json")   # the authors' copy only
P2_EXPORT = ROOT / "results" / "package2" / "confirm_qa_textfree"
FAIL, SKIPPED = [], []


def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check(ok, what):
    print("  %-4s %s" % ("ok" if ok else "FAIL", what))
    if not ok:
        FAIL.append(what)
    return ok


def skipped(what):
    print("  skip freeze not public; skipped: %s" % what)
    SKIPPED.append(what)


def load_freeze():
    """The authors' freeze, or None where it is absent (it lists the candidate titles)."""
    return json.load(open(FREEZE, encoding="utf-8")) if FREEZE.is_file() else None


def frozen_digests(fz, prov):
    """The digests the freeze lists: from the freeze where present, else as provenance.json records them."""
    return fz["sha256"] if fz is not None else prov["freeze"]["frozen_sha256"]


def stub(item_id):
    return {"id": item_id, "paragraphs": [None] * 10}


# ---- the export's internal consistency ------------------------------------------------------------
def consistency(items, rk, answers, sample, fz):
    print(" export consistency")
    groups = Counter(x["group"] for x in items)
    check(len(items) == 300 and groups == {"sufficient": 90, "complement": 210}
          and Counter(x["supporting_in_pool"] for x in items) == {0: 60, 1: 150, 2: 90},
          "items: %d, %s, supporting candidates per question %s" % (
              len(items), dict(groups), dict(sorted(Counter(x["supporting_in_pool"] for x in items).items()))))
    check(all(x["eligible"] and x["n_candidates"] == 10 and x["n_supporting_titles"] == 2
              and len(x["supporting"]) == x["supporting_in_pool"] and len(x["title_sha256"]) == len(x["text_sha256"]) == 10
              and len(x["supporting_title_sha256"]) == 2
              and set(x["supporting"]) <= set(range(10)) and set(x["title_sha256"][i] for i in x["supporting"]) <= set(x["supporting_title_sha256"])
              and x["group"] == ("sufficient" if x["supporting_in_pool"] == 2 else "complement") for x in items),
          "every item: eligible (10 candidates, 2 supporting titles), supporting indices, group and digests consistent")
    order = [x["id"] for x in items]
    groups_in_order = [(x["group"], x["supporting_in_pool"]) for x in items]
    check(order == [x["id"] for x in sample["confirm"]]
          and groups_in_order == [(x["group"], x["supporting_in_pool"]) for x in sample["confirm"]]
          and len(sample["smoke"]) == 10 and len({x["id"] for x in sample["smoke"]} | set(order)) == 310,
          "items.jsonl and sample.json list the same 300 questions in drawing order, with the same groups; "
          "10 further smoke ids")
    if fz is None:
        skipped("the 300 questions, their groups and the 10 smoke ids against the freeze's own sample")
    else:
        fzs = fz["sample"]
        check(order == [x["id"] for x in fzs["confirm"]]
              and groups_in_order == [(x["group"], x["supporting_in_pool"]) for x in fzs["confirm"]]
              and [x["id"] for x in sample["smoke"]] == [x["id"] for x in fzs["smoke"]],
              "the 300 questions, in drawing order, with their groups, and the 10 smoke ids are those of the freeze")
    sp = json.load(open(P2_EXPORT / "splits.json", encoding="utf-8"))["datasets"]["hotpotqa"]
    pub = set(sp["excluded"]) | set(sp["dev"]) | {x["id"] for x in sp["pilot_items"] + sp["confirm_items"]}
    pub |= {x["id"] for x in V.jl(P2_EXPORT / "items.jsonl") if x["dataset"] == "hotpotqa"}
    ex = sample["excluded"]
    check(sorted(pub) == ex["ids"] and len(pub) == ex["count"] == sample["counts"]["excluded"] == 520
          and sha_text("\n".join(ex["ids"])) == ex["ids_sha256"] and not pub & set(order + [x["id"] for x in sample["smoke"]]),
          "exclusions: the %d HotpotQA ids of package 2's export (confirmatory, development, excluded), none drawn" % len(pub))

    local = [x for x in rk if x["kind"] == "local"]
    gpt = [x for x in rk if x["kind"] == "rankgpt"]
    check(len(local) == 1500 and {(x["item"], x["ranker"]) for x in local} == {(i, r) for i in order for r in AF.LOCAL}
          and all(sorted(x["order"]) == list(range(10)) and x["top_k"] == x["order"][:RF.K] for x in local),
          "local rankings: %d, one complete order per question and ranker, top_k = first %d" % (len(local), RF.K))
    expected = {q["id"]: q for q in RF.rank_requests([stub(i) for i in order])}
    check(len(gpt) == 600 and {x["id"] for x in gpt} == set(expected)
          and all(x["pool"] == expected[x["id"]]["pool"] and x["order_idx"] == expected[x["id"]]["order_idx"] for x in gpt),
          "RankGPT requests: %d; input orders o0 (file order) and o1 (seeded shuffle) as run_fullwiki.rank_requests" % len(gpt))
    good = all(x["transport_failed"] or (sorted(x["order"]) == list(range(10)) and x["top_k"] == x["order"][:RF.K]
               and x["parse"]["returned"] + x["parse"]["appended"] == x["size"]
               and x["parse"]["complete"] == (x["parse"]["returned"] == x["size"])
               and x["parse"]["repaired"] == bool(x["parse"]["appended"] or x["parse"]["duplicates"] or x["parse"]["out_of_range"]))
               and x["used_for_answers"] == (x["order_idx"] == 0 and not x["transport_failed"]) for x in gpt)
    check(good, "RankGPT rows: complete orders, parse counts and flags consistent, used_for_answers = received o0")

    rankings = {(x["item"], x["ranker"]): x["order"] for x in local}
    rankings.update({(x["item"], "rankgpt"): x["order"] for x in gpt if x["used_for_answers"]})
    planned = {"ans|%s|%s|%s" % (m, i, c) for i in order for m in Q.ANSWER_MODELS for c in RF.CONDITIONS
               if c != "rankgpt" or (i, "rankgpt") in rankings}
    by_item = {x["id"]: x for x in items}

    def context(x):
        c = x["cond"]
        return None if c == "none" else list(range(10)) if c == "full" else rankings[(x["item"], c)][:RF.K]
    check(len(answers) == 7200 and {x["id"] for x in answers} == planned and len({x["id"] for x in answers}) == 7200,
          "answer requests: %d, exactly the planned questions x models x conditions" % len(answers))
    check(all(x["context"] == context(x) and x["group"] == by_item[x["item"]]["group"] for x in answers),
          "every answer's context indices equal the condition's selection (none, all 10, or the ranker's top %d)" % RF.K)
    reqs = gpt + answers
    check(all((x["status"] == "received") == (not x["transport_failed"])
              and (x["missing_reason"] is None) == (not x["transport_failed"]) for x in reqs)
          and all((x["em"] is None) == x["transport_failed"] == (x["f1"] is None) for x in answers)
          and all(x["prompt_sha256"] and x["prompt_chars"] > 0 for x in reqs),
          "status, missingness and scores consistent; every request has a prompt digest")
    return rankings


# ---- recompute analysis_fullwiki.json from the export -------------------------------------------
def accounting(items, requests):
    """analyze_fullwiki.accounting, from the exported request statuses."""
    status = {x["id"]: x["status"] for x in requests}

    def st(rid):
        return status.get(rid, "not_issued")
    rank, ans = Counter(), defaultdict(Counter)
    for it in items:
        o0 = "rank|%s|%s|o0" % (Q.RANK_MODEL, it["id"])
        for j in (0, 1):
            rank["o%d|%s" % (j, st("rank|%s|%s|o%d" % (Q.RANK_MODEL, it["id"], j)))] += 1
        ranked = status.get(o0) == "received"
        for m in Q.ANSWER_MODELS:
            for c in RF.CONDITIONS:
                s = st("ans|%s|%s|%s" % (m, it["id"], c))
                if s == "not_issued" and c == "rankgpt" and o0 in status and not ranked:
                    s = "not_requested_no_rankgpt_ranking"
                ans["%s|%s" % (m, c)][s] += 1
    totals = Counter()
    for v in ans.values():
        totals.update(v)
    return {"planned": {"ranking": 2 * len(items), "answer": 24 * len(items), "total": 26 * len(items)},
            "issued": len(status), "received": sum(1 for s in status.values() if s != "interrupted"),
            "ranking_status": dict(sorted(rank.items())), "answer_status_totals": dict(sorted(totals.items())),
            "answer_status": {k: dict(sorted(v.items())) for k, v in ans.items()}}


def resources(items, gpt):
    """analyze_fullwiki.resources, from the exported RankGPT rows."""
    ids = {x["id"] for x in items}
    rows = sorted((x for x in gpt if x["item"] in ids), key=lambda x: x["id"])
    ok = [x for x in rows if not x["transport_failed"]]
    comp, of, orders = Counter(), Counter(), defaultdict(dict)
    for x in ok:
        comp["o%d" % x["order_idx"]] += x["parse"]["complete"]
        of["o%d" % x["order_idx"]] += 1
        orders[x["item"]][x["order_idx"]] = x["order"]
    agree, tau = [], []
    for i in sorted(orders):
        o = orders[i]
        if 0 in o and 1 in o:
            agree.append(len(set(o[0][:RF.K]) & set(o[1][:RF.K])) / RF.K)
            tau.append(Q.kendall_tau(o[0], o[1]))
    return {"requests": len(rows), "transport_failed": len(rows) - len(ok),
            "latency_s": A.boot_mean([x["wall_s"] for x in ok]),
            "input_tokens": A.boot_mean([x["input_tokens"] or 0 for x in ok]),
            "output_tokens": A.boot_mean([x["output_tokens"] or 0 for x in ok]),
            "extra_attempts": sum(x["attempts"] - 1 for x in rows),
            "complete_parses": {k: [comp[k], of[k]] for k in ("o0", "o1")},
            "order_pairs": len(agree), "topK_agreement": A.boot_mean(agree), "kendall_tau": A.boot_mean(tau)}


def recompute(shipped, items, rk, answers, rankings):
    """analyze_fullwiki.analyze, step for step, on the exported rows (answers in the records' order)."""
    by_id = {x["id"]: x for x in items}
    ids = {g: sorted(x["id"] for x in items if g == "all" or x["group"] == g) for g in AF.GROUPS}
    sup = {i: set(x["supporting"]) for i, x in by_id.items()}
    nsup = {i: x["n_supporting_titles"] for i, x in by_id.items()}
    gpt = [x for x in rk if x["kind"] == "rankgpt"]

    def hit(i, r):
        return len(set(rankings[(i, r)][:RF.K]) & sup[i])
    res = {"mode": shipped["mode"], "records": shipped["records"], "freeze": shipped["freeze"],
           "questions": {g: len(ids[g]) for g in AF.GROUPS}, "requests": accounting(items, gpt + answers)}
    res["retrieval_coverage"] = {g: {
        "n": len(ids[g]),
        "supporting_in_pool": dict(sorted(Counter(str(by_id[i]["supporting_in_pool"]) for i in ids[g]).items())),
        "coverage": A.boot_mean([by_id[i]["supporting_in_pool"] / nsup[i] for i in ids[g]])} for g in AF.GROUPS}
    res["evidence"] = {}
    for r in Q.RANKED:
        for g in AF.GROUPS:
            have = [i for i in ids[g] if (i, r) in rankings]
            res["evidence"]["%s|%s" % (g, r)] = {
                "n": len(have), "support_recall": A.boot_mean([hit(i, r) / nsup[i] for i in have]),
                "all_supporting": A.boot_mean([float(hit(i, r) == nsup[i]) for i in have])}
    per, fmt = defaultdict(dict), defaultdict(lambda: [0, 0])
    for x in answers:
        if x["transport_failed"]:
            continue
        per[(x["model"], x["cond"])][x["item"]] = (x["em"], x["f1"])
        fmt[x["model"]][0] += 1
        fmt[x["model"]][1] += x["has_answer_line"]
    res["format"] = {m: {"replies": v[0], "with_answer_line": v[1]} for m, v in fmt.items()}
    res["answers"] = {}
    for g in AF.GROUPS:
        for m in Q.ANSWER_MODELS:
            for c in RF.CONDITIONS:
                d = per.get((m, c), {})
                have = [i for i in ids[g] if i in d]
                res["answers"]["%s|%s|%s" % (g, m, c)] = {"n": len(have), "em": A.boot_mean([d[i][0] for i in have]),
                                                         "f1": A.boot_mean([d[i][1] for i in have])}

    def contrast(m, r, g, level):
        a, b = per.get((m, "rankgpt"), {}), per.get((m, r), {})
        common = sorted(set(a) & set(b) & set(ids[g]))
        return AF.bounds([a[i][1] - b[i][1] for i in common], level)
    res["primary"] = {"%s|rankgpt-%s" % (m, r): contrast(m, r, "all", 1 - AF.ALPHA / AF.N_PRIMARY)
                      for m in Q.ANSWER_MODELS for r in AF.LOCAL}
    res["secondary"] = {"%s|%s|rankgpt-%s" % (g, m, r): contrast(m, r, g, 1 - AF.ALPHA / AF.N_SECONDARY)
                        for g in ("sufficient", "complement") for m in Q.ANSWER_MODELS for r in AF.LOCAL}
    ranked = [i for i in ids["all"] if (i, "rankgpt") in rankings]
    ec = {"rankgpt-%s" % r: AF.bounds([(hit(i, "rankgpt") - hit(i, r)) / nsup[i] for i in ranked],
                                      1 - AF.ALPHA / AF.N_EVIDENCE) for r in AF.LOCAL}
    res["evidence_criterion"] = {"contrasts": ec, "missing_rankgpt_rankings": len(ids["all"]) - len(ranked),
                                 "holds": len(ec) == AF.N_EVIDENCE and all(v["verified_positive"] for v in ec.values())}
    res["worst_case"] = {}
    for m in Q.ANSWER_MODELS:
        a = per.get((m, "rankgpt"), {})
        for r in AF.LOCAL:
            b = per.get((m, r), {})
            v = AF.bounds([(a[i][1] if i in a else 0.0) - (b[i][1] if i in b else 1.0) for i in ids["all"]],
                          1 - AF.ALPHA / AF.N_PRIMARY)
            v.update({"missing_rankgpt": sum(i not in a for i in ids["all"]),
                      "missing_comparator": sum(i not in b for i in ids["all"])})
            res["worst_case"]["%s|rankgpt-%s" % (m, r)] = v
    res["rankgpt_resources"] = resources(items, gpt)
    res["verdict"] = AF.verdict(res)
    return json.loads(json.dumps(res))


def summary_text(shipped, items, gpt, answers):
    """run_fullwiki.summary's text, from the exported rows (no halt records: the export refuses them)."""
    reqs = gpt + answers
    issued = Counter(x["id"].split("|")[0] for x in reqs)
    got = Counter("rank" if x["id"].startswith("rank|") else "answer" for x in reqs if x["status"] != "interrupted")
    failed = [x for x in reqs if x["transport_failed"]]
    cls = Counter(x["status"][len("failed_"):] for x in failed)
    L = ["%s: %d questions; records %s" % (shipped["mode"], len(items), shipped["records"]),
         "ranking requests: planned %d, issued %d, received %d" % (2 * len(items), issued["rank"], got["rank"]),
         "answer requests: planned up to %d, issued %d, received %d" % (24 * len(items), issued["ans"], got["answer"]),
         "transport failures: %d (HTTP 400 on every attempt %d, other %d); interrupted (issued, no receipt) %d" % (
             len(failed), cls["http400"], cls["other"], sum(1 for x in reqs if x["status"] == "interrupted"))]
    ranks = [x for x in gpt if not x["transport_failed"]]
    if ranks:
        L.append("RankGPT complete parses %d/%d" % (sum(x["parse"]["complete"] for x in ranks), len(ranks)))
    acc, fmt = defaultdict(list), defaultdict(lambda: [0, 0])
    for x in answers:
        if not x["transport_failed"]:
            acc[(x["model"], x["cond"])].append(x["f1"])
            fmt[x["model"]][0] += 1
            fmt[x["model"]][1] += x["has_answer_line"]
    if acc:
        L.append("mean F1 (n) by answer model and condition; intervals and contrasts: analyze_fullwiki.py")
        L.append("  %-16s" % "" + "".join("%13s" % c for c in RF.CONDITIONS))
        for m in Q.ANSWER_MODELS:
            L.append("  %-16s" % m + "".join("%13s" % ("%.2f (%d)" % (sum(v) / len(v), len(v)) if v else "-")
                                             for v in (acc.get((m, c), []) for c in RF.CONDITIONS)))
        L.append("answer-line compliance: " + "; ".join("%s %d/%d" % (m, v[1], v[0]) for m, v in fmt.items()))
    return "\n".join(L) + "\n"


def text_diff(a, b):
    la, lb = a.split("\n"), b.split("\n")
    return [i + 1 for i in range(max(len(la), len(lb))) if i >= len(la) or i >= len(lb) or la[i] != lb[i]]


# As printed in the manuscript, Table tab:fullwiki: all found over all 300 questions and within the
# sufficient 90, then F1 over all questions for Haiku, GPT-5.5 and DeepSeek (None where not printed).
TABLE_FULLWIKI = {
    "none":    (None, None, 0.46, 0.67, 0.58),
    "full":    (None, None, 0.41, 0.70, 0.53),
    "bm25":    (0.16, 0.54, 0.39, 0.69, 0.49),
    "mmr":     (0.12, 0.39, 0.34, 0.69, 0.47),
    "bge":     (0.21, 0.69, 0.39, 0.68, 0.50),
    "e5":      (0.20, 0.67, 0.36, 0.69, 0.50),
    "minilm":  (0.23, 0.76, 0.41, 0.72, 0.52),
    "rankgpt": (0.26, 0.88, 0.43, 0.69, 0.54),
}


def published(res, items, answers):
    print(" published figures (manuscript: tab:fullwiki, sec:natural, sec:results-natural, limitations)")
    r = V.r
    ev, an = res["evidence"], res["answers"]
    bad = []
    for cond, (all_found, suff_found, *f1s) in TABLE_FULLWIKI.items():
        if all_found is not None and r(ev["all|%s" % cond]["all_supporting"][0]) != all_found:
            bad.append("%s all found" % cond)
        if suff_found is not None and r(ev["sufficient|%s" % cond]["all_supporting"][0]) != suff_found:
            bad.append("%s all found (sufficient)" % cond)
        for m, v in zip(Q.ANSWER_MODELS, f1s):
            if r(an["all|%s|%s" % (m, cond)]["f1"][0]) != v:
                bad.append("%s F1 %s" % (cond, m))
    check(not bad, "Table tab:fullwiki: 36 printed values %s" % ("reproduced" if not bad else "MISMATCH %s" % bad))
    rc, q = res["retrieval_coverage"], res["questions"]
    check(q == {"all": 300, "sufficient": 90, "complement": 210} and rc["all"]["supporting_in_pool"] == {"0": 60, "1": 150, "2": 90}
          and res["requests"]["issued"] == 7800 and len(res["primary"]) == 15,
          "300 questions, 90 with both supporting paragraphs among the candidates, 60 with neither; 7,800 requests; "
          "15 primary contrasts (sec:natural, sec:results-natural)")
    base_all = [ev["all|%s" % k]["all_supporting"][0] for k in AF.LOCAL]
    base_suf = [ev["sufficient|%s" % k]["all_supporting"][0] for k in AF.LOCAL]
    check(r(90 / 300) == 0.30 and r(ev["all|rankgpt"]["all_supporting"][0]) == 0.26 and (r(min(base_all)), r(max(base_all))) == (0.12, 0.23)
          and r(ev["sufficient|rankgpt"]["all_supporting"][0]) == 0.88 and (r(min(base_suf)), r(max(base_suf))) == (0.39, 0.76),
          "complete evidence capped at 0.30; RankGPT 0.26, baselines %.2f-%.2f; within the 90: RankGPT 0.88, baselines "
          "%.2f-%.2f (published 0.26, 0.12-0.23; 0.88, 0.39-0.76)" % (r(min(base_all)), r(max(base_all)), r(min(base_suf)), r(max(base_suf))))
    ec = res["evidence_criterion"]["contrasts"]
    check([k for k, v in ec.items() if v["verified_positive"]] == ["rankgpt-bm25", "rankgpt-mmr", "rankgpt-bge", "rankgpt-e5"]
          and not res["evidence_criterion"]["holds"],
          "support recall: RankGPT above four of the five baselines simultaneously, not the MiniLM cross-encoder")
    pos = sorted(k for k, v in res["primary"].items() if v["verified_positive"])
    neg = [k for k, v in res["primary"].items() if v["verified_negative"]]
    wpos = sorted(k for k, v in res["worst_case"].items() if v["verified_positive"])
    wneg = [k for k, v in res["worst_case"].items() if v["verified_negative"]]
    vd = res["verdict"]
    check(pos == ["DeepSeek-V4-Pro|rankgpt-mmr", "Haiku-4.5|rankgpt-e5", "Haiku-4.5|rankgpt-mmr"] and not neg
          and not any(v["lower"] > 0 or v["upper"] < 0 for k, v in res["primary"].items() if k.startswith("GPT-5.5"))
          and wpos == pos and not wneg and not vd["worst_case"]["changes_row"]
          and (vd["rule"], vd["row"]) == (4, "little or no improvement"),
          "primary: RankGPT higher in 3 of 15 (%s), lower in none, no GPT-5.5 contrast excludes zero; the worst case "
          "changes no decision; verdict rule %d, %s" % (", ".join(pos), vd["rule"], vd["row"]))
    f1 = lambda g, m, c: an["%s|%s|%s" % (g, m, c)]["f1"][0]   # noqa: E731
    sel = ("full",) + Q.RANKED
    hd = ("Haiku-4.5", "DeepSeek-V4-Pro")
    check(tuple(r(f1("all", m, "none")) for m in hd) == (0.46, 0.58)
          and tuple(r(max(f1("all", m, c) for c in Q.RANKED)) for m in hd) == (0.43, 0.54)
          and all(f1("all", m, "none") > f1("all", m, c) for m in hd for c in sel),
          "Haiku and DeepSeek: no context F1 0.46 and 0.58, above every selection (at most 0.43 and 0.54)")
    check(all(f1("complement", m, c) < f1("complement", m, "none") for m in hd for c in sel)
          and all(f1("sufficient", m, c) > f1("sufficient", m, "none") for m in hd for c in sel)
          and tuple(r(f1("sufficient", m, "rankgpt")) for m in hd) == (0.71, 0.71)
          and tuple(r(f1("sufficient", m, "none")) for m in hd) == (0.46, 0.55)
          and (vd["S_plus"], vd["C_plus"]) == (3, 0),
          "secondary: in the 210 every selection lowered Haiku's and DeepSeek's F1, within the 90 every one raised it "
          "(RankGPT 0.71 and 0.71 against 0.46 and 0.55); RankGPT higher in 3 of 15 sufficient and 0 of 15 complement contrasts")
    rs = res["rankgpt_resources"]
    check((r(rs["latency_s"][0]), r(rs["input_tokens"][0], "1"), rs["complete_parses"]["o0"], r(rs["topK_agreement"][0]))
          == (1.53, 1671, [291, 300], 0.79),
          "RankGPT on Haiku: %.2f s, %d input tokens per ranking, %d of %d first-order rankings complete, top two agree "
          "for %.2f (published 1.53 s, 1,671, 291 of 300, 0.79)" % (rs["latency_s"][0], round(rs["input_tokens"][0]),
                                                                    rs["complete_parses"]["o0"][0], rs["complete_parses"]["o0"][1], rs["topK_agreement"][0]))
    miss = [x for x in answers if x["transport_failed"]]
    check(len(miss) == 13 and all(x["status"] == "failed_http400" and x["missing_reason"] == "content_filter" for x in miss),
          "13 answer requests refused with HTTP 400, all by the provider's content filter (%s)" % dict(Counter(x["model"] for x in miss)))


def verify():
    print("CONFIRM: %s" % EXP.relative_to(ROOT).as_posix())
    items = V.jl(EXP / "items.jsonl")
    rk = V.jl(EXP / "rankings.jsonl")
    answers = V.jl(EXP / "answers.jsonl")
    sample = json.load(open(EXP / "sample.json", encoding="utf-8"))
    prov = json.load(open(EXP / "provenance.json", encoding="utf-8"))
    shipped = json.load(open(EXP / "analysis_fullwiki.json", encoding="utf-8"))
    fz = load_freeze()
    print("freeze: %s" % ("the authors' copy, %s" % RF.rel(FREEZE) if fz is not None else
                          "not public (kept by the authors; it lists the candidate titles); the digests it lists are "
                          "read from provenance.json"))
    rankings = consistency(items, rk, answers, sample, fz)

    print(" provenance")
    pf = prov["freeze"]
    inputs = prov["frozen_inputs_match_FREEZE_fullwiki_json"]
    check(pf["public"] is False and pf["files"] == len(pf["frozen_sha256"]) and inputs
          and all(prov["inputs_sha256"][f] == pf["frozen_sha256"][f] for f in inputs),
          "the export was written from the frozen inputs: %d input digests equal the frozen digests in provenance.json" % len(inputs))
    code = sorted(f for f in pf["frozen_sha256"] if f.startswith("harness/"))
    check(all((ROOT / f).is_file() and sha_file(ROOT / f) == pf["frozen_sha256"][f] for f in code),
          "the frozen protocol and code in this repository equal their frozen digests (%d files)" % len(code))
    if fz is None:
        skipped("the freeze file's SHA-256 (%s..., %s) and its digest list against provenance.json"
                % (pf["sha256"][:16], pf["frozen_at_utc"]))
    else:
        check(sha_file(FREEZE) == pf["sha256"] and fz["frozen_at_utc"] == pf["frozen_at_utc"] and fz["sha256"] == pf["frozen_sha256"],
              "the freeze file's SHA-256, time and every digest it lists equal provenance.json")
    same = all((EXP / n).read_bytes() == (RES3 / n).read_bytes() and sha_file(RES3 / n) == prov["analysis_sha256"]["results/package3/" + n]
               for n in ("analysis_fullwiki.json", "analysis_fullwiki.md"))
    check(same, "analysis_fullwiki.json and .md: the copies equal results/package3/ and the digests recorded at export")
    c = prov["counts"]
    check(c["prompts_rebuilt_and_matched"] == c["requests"] == len(answers) + sum(x["kind"] == "rankgpt" for x in rk) == 7800,
          "prompts rebuilt from the exported indices and matched at export: %d of %d requests" % (c["prompts_rebuilt_and_matched"], c["requests"]))

    print(" analysis")
    res = recompute(shipped, items, rk, answers, rankings)
    d = V.diff(shipped, res)
    check(not d, "analysis_fullwiki.json recomputed from the export: %s" % (
        "agrees within %g (all %d numbers, bootstrap intervals included)" % (V.TOL, V.n_numbers(shipped)) if not d
        else "%d differences" % len(d)))
    for line in d[:15]:
        print("         " + line)
    md = (EXP / "analysis_fullwiki.md").read_text(encoding="utf-8")
    regen = AF.report(res) + "\n"
    dl = text_diff(md, regen)
    check(not dl, "analysis_fullwiki.md regenerated from the recomputed results (analyze_fullwiki.report): %s" % (
        "identical, %d lines" % md.count("\n") if not dl else "differs in lines %s" % dl[:10]))
    gpt = [x for x in rk if x["kind"] == "rankgpt"]
    sm = (EXP / "summary.txt").read_text(encoding="utf-8")
    dl = text_diff(sm, summary_text(shipped, items, gpt, answers))
    check(not dl, "summary.txt regenerated from the export (run_fullwiki.summary): %s" % (
        "identical, %d lines" % sm.count("\n") if not dl else "differs in lines %s" % dl))
    published(res, items, answers)


# ---- optional: rebuild the inputs from the public parquet -----------------------------------------
def idf_text(n_questions, n_par, df):
    """idf_fullwiki.json as fullwiki_data.build() writes it; its constants are repeated here, and the
    frozen digest confirms the copy."""
    idf = {"source": FD.SRC.name, "source_sha256": FD.SRC_SHA256, "questions": n_questions, "paragraphs": n_par,
           "counting": "every paragraph of the file, once per question it appears in (rank_local.idf_table)",
           "tokens": "rank_local.toks of 'title. text' (rank_local.passage)",
           "idf": "log(1 + (paragraphs - df + 0.5) / (df + 0.5)), rank_local.idf_table's formula",
           "vocabulary": "tokens of the confirmatory and smoke questions that occur in some paragraph "
                         "(bm25_scores reads no other IDF; a token absent here has IDF 0, as in rank_local)",
           "df": dict(sorted(df.items()))}
    return json.dumps(idf, indent=0) + "\n"


def verify_rebuilt(write=False):
    import export_qa_textfree as X    # package 2's prompt rebuild from indices
    print("REBUILT INPUTS from %s (digests, the draw and every prompt)" % RF.rel(FD.SRC))
    freeze = load_freeze()
    fz = frozen_digests(freeze, json.load(open(EXP / "provenance.json", encoding="utf-8")))
    print("  frozen digests from %s" % ("the freeze (the authors' copy)" if freeze is not None
                                        else "provenance.json, which records every digest the freeze lists"))
    sample = json.load(open(EXP / "sample.json", encoding="utf-8"))
    exp = V.jl(EXP / "items.jsonl")
    if not check(FD.SRC.exists(), "source file present (download %s)" % FD.SRC_URL):
        return
    size, digest = FD.SRC.stat().st_size, FD.sha(FD.SRC)
    check(size == FD.SRC_BYTES == sample["source"]["bytes"] and digest == FD.SRC_SHA256 == sample["source"]["sha256"]
          == fz["natural_data/hotpot_dev_fullwiki.parquet"], "source: %d bytes, SHA-256 %s..." % (size, digest[:16]))
    all_items = FD.load()
    confirm, smoke, ineligible, pool = FD.draw(all_items, set(sample["excluded"]["ids"]))
    c = sample["counts"]
    check([x["id"] for x in confirm] == [x["id"] for x in exp] and [x["id"] for x in smoke] == [x["id"] for x in sample["smoke"]]
          and ineligible == sample["ineligible_skipped_ids"] and len(pool) == c["pool_after_exclusion"]
          and len(all_items) == c["questions"] and sum(FD.eligible(x) for x in all_items) == c["eligible_all"],
          "draw (seed %d, %d excluded ids): the 300 confirmatory questions in order and the 10 smoke questions reproduced"
          % (FD.SEED, sample["excluded"]["count"]))
    both = [x for x in all_items if sum(p["supporting"] for p in x["paragraphs"]) == 2]
    eligible_both = sum(FD.eligible(x) for x in both)
    check(eligible_both == c["all_sufficient"] == 2066 and len(both) == 2089,
          "sufficient questions in the file: %d of the %d eligible, %d of all %d (PROTOCOL_FULLWIKI.md, Section 3, gives "
          "2,089 for the eligible ones; corrected in PROTOCOL_FULLWIKI_ERRATA.md)"
          % (eligible_both, c["eligible_all"], len(both), len(all_items)))
    items = [FD.annotate(x, "fullwiki_rank") for x in confirm]
    smoke_items = [FD.annotate(x, "fullwiki_smoke") for x in smoke]
    bad = [e["id"] for it, e in zip(items, exp) if sha_text(it["question"]) != e["question_sha256"]
           or [sha_text(p["title"]) for p in it["paragraphs"]] != e["title_sha256"]
           or [sha_text(p["text"]) for p in it["paragraphs"]] != e["text_sha256"]
           or [sha_text(t) for t in it["supporting_titles"]] != e["supporting_title_sha256"]
           or [k for k, p in enumerate(it["paragraphs"]) if p["supporting"]] != e["supporting"]
           or (it["group"], it["supporting_in_pool"], it["type"], it["level"], len(it["answers"]))
           != (e["group"], e["supporting_in_pool"], e["type"], e["level"], e["n_gold_answers"])]
    check(not bad, "items: %d of %d match (question, every title and text, supporting titles and indices, group)"
          % (len(exp) - len(bad), len(exp)))
    files = {"items_confirm.jsonl": FD.jsonl_text(items), "items_smoke.jsonl": FD.jsonl_text(smoke_items)}
    vocab = set().union(*(set(FD.RL.toks(x["question"])) for x in items + smoke_items))
    n_par, df = FD.doc_freqs(all_items, vocab)
    b = sample["bm25_idf"]
    check((n_par, len(vocab), len(df)) == (b["paragraphs"], b["query_tokens"], b["tokens_with_df"])
          and sha_text(json.dumps(dict(df), sort_keys=True, separators=(",", ":"))) == b["df_sha256"],
          "BM25 document frequencies: %d paragraphs, %d query tokens, %d with a frequency, digest as exported"
          % (n_par, len(vocab), len(df)))
    files["idf_fullwiki.json"] = idf_text(len(all_items), n_par, df)
    for name, text in files.items():
        check(sha_text(text) == fz["natural_data/package3/" + name],
              "%s rebuilt: SHA-256 equals the frozen digest" % name)
    by_id = {x["id"]: x for x in items}
    n = nbad = 0
    for x in V.jl(EXP / "rankings.jsonl"):
        if x["kind"] == "rankgpt":
            n += 1
            nbad += sha_text(Q.rank_prompt(by_id[x["item"]], x["pool"])) != x["prompt_sha256"]
    for x in V.jl(EXP / "answers.jsonl"):
        n += 1
        nbad += sha_text(X.prompt_from_indices(by_id[x["item"]], x["context"])) != x["prompt_sha256"]
    check(not nbad, "prompts rebuilt from the exported pools and context indices: %d of %d match their SHA-256" % (n - nbad, n))
    lp = FD.OUT / "rankings_local_confirm.jsonl"
    if lp.exists():
        loc = {(y["id"], y["ranker"]): y["order"] for y in V.jl(lp)}
        local = [x for x in V.jl(EXP / "rankings.jsonl") if x["kind"] == "local"]
        mism = [x for x in local if loc.get((x["item"], x["ranker"])) != x["order"]]
        check(not mism, "local rankers: %d of %d orders match %s" % (len(local) - len(mism), len(local), RF.rel(lp)))
    if write:
        FD.OUT.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            p = FD.OUT / name
            if p.exists():
                print("  keep %s (exists; never overwritten)" % RF.rel(p))
            elif sha_text(text) == fz["natural_data/package3/" + name]:
                FD.write_text(p, text)
                print("  wrote %s" % RF.rel(p))


def main():
    verify()
    if "--rebuilt" in sys.argv:
        print()
        verify_rebuilt(write="--write" in sys.argv)
    note = " (%d skipped: the freeze is not public)" % len(SKIPPED) if SKIPPED else ""
    print("\n%s%s" % ("ALL CHECKS PASSED" if not FAIL else "%d CHECK(S) FAILED" % len(FAIL), note))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
