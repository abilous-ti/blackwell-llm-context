r"""Analysis of package 3, as fixed in PROTOCOL_FULLWIKI.md (Sections 5-7).

  coverage        the retrieval system's coverage: supporting paragraphs among the 10 candidates
  evidence        per ranker, over all questions and per subgroup: support recall at K = 2 (over the
                  question's two supporting paragraphs; one the retrieval missed counts as not
                  retrieved) and all supporting paragraphs in the top 2 (possible only in the
                  sufficient subgroup; also reported over all questions)
  answers         per subgroup, answer model and condition: official HotpotQA exact match and F1
  primary         RankGPT minus each of the five local rankers on F1 per answer model, all
                  questions: 15 paired differences, simultaneous 95% (Bonferroni over 15)
  secondary       the same 15 within the sufficient subgroup and within its complement: one
                  family of 30, simultaneous 95% (Bonferroni over 30)
  evidence test   RankGPT minus each local ranker on support recall at K, all questions,
                  simultaneous 95% over the 5; it holds when all five are verified positive
  worst case      the primary family with every missing outcome counted against RankGPT (missing
                  RankGPT answer F1 0, missing comparator answer F1 1), all questions
  missing         every planned request by status: received, transport failure (HTTP 400 on every
                  attempt, or other), interrupted, not issued, RankGPT answer not requested
  resources       RankGPT latency, tokens, extra attempts, complete parses, top-2 agreement and
                  Kendall tau between the two input orders
  verdict         the pre-declared interpretation row, by the protocol's reading rules
Every interval is package 2's paired percentile bootstrap (analyze_qa.boot_mean: 4,000 resamples,
seed 20261005), with approximate coverage. Each contrast uses the questions where both arms have an
outcome, as in package 2.

  python harness/package3/analyze_fullwiki.py            confirmatory -> results/package3/analysis_fullwiki.{json,md}
  python harness/package3/analyze_fullwiki.py --mock     mock records -> natural_data/package3/mock_fullwiki/
  python harness/package3/analyze_fullwiki.py --smoke    smoke records -> natural_data/package3/smoke_fullwiki/
"""
import argparse
import io
import json
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
import run_fullwiki as RF  # noqa: E402
import analyze_qa as A  # noqa: E402
import freeze_fullwiki as FZ  # noqa: E402

Q = RF.Q
LOCAL = A.LOCAL
GROUPS = ("all", "sufficient", "complement")
ALPHA = 0.05
N_PRIMARY, N_SECONDARY, N_EVIDENCE = 15, 30, 5
MAJORITY = 8
RESULTS = ROOT / "results" / "package3"
READING = {
    "improvement in evidence and answers": "the practical advantage extends to these retrieved pools",
    "improvement mainly in the sufficient subgroup": "candidate retrieval coverage limits the benefit of reranking",
    "little or no improvement": "the advantage has narrower scope than the supplied-pool benchmark suggested",
    "decrease": "the tested reranking configuration needs qualification in this setting",
    "not covered by the pre-declared table": "reported with all bounds; no row is claimed",
}


def bounds(diffs, level):
    est, lo, hi = A.boot_mean(diffs, level=level)
    return {"n": len(diffs), "estimate": est, "lower": lo, "upper": hi,
            "verified_positive": lo is not None and lo > 0, "verified_negative": hi is not None and hi < 0}


def accounting(items, st):
    R = st["receipt"]

    def status(rid):
        if rid in R:
            return ("failed_" + RF.failure_class(R[rid])) if R[rid].get("transport_failed") else "received"
        return "interrupted" if rid in st["issued"] else "not_issued"
    rank, ans = Counter(), defaultdict(Counter)
    for it in items:
        o0 = "rank|%s|%s|o0" % (Q.RANK_MODEL, it["id"])
        for j in (0, 1):
            rank["o%d|%s" % (j, status("rank|%s|%s|o%d" % (Q.RANK_MODEL, it["id"], j)))] += 1
        ranked = o0 in R and not R[o0].get("transport_failed")
        for m in Q.ANSWER_MODELS:
            for c in RF.CONDITIONS:
                s = status("ans|%s|%s|%s" % (m, it["id"], c))
                if s == "not_issued" and c == "rankgpt" and o0 in st["issued"] and not ranked:
                    s = "not_requested_no_rankgpt_ranking"
                ans["%s|%s" % (m, c)][s] += 1
    totals = Counter()
    for v in ans.values():
        totals.update(v)
    return {"planned": {"ranking": 2 * len(items), "answer": 24 * len(items), "total": 26 * len(items)},
            "issued": len(st["issued"]), "received": len(R), "ranking_status": dict(sorted(rank.items())),
            "answer_status_totals": dict(sorted(totals.items())),
            "answer_status": {k: dict(sorted(v.items())) for k, v in ans.items()}}


def resources(items, st):
    R = st["receipt"]
    ids = {it["id"] for it in items}
    rows = sorted((rc for rc in R.values() if rc.get("kind") == "rank" and rc["item"] in ids),
                  key=lambda rc: rc["id"])          # by id: intervals independent of the lanes' write order
    ok = [rc for rc in rows if not rc.get("transport_failed")]
    comp, of, orders = Counter(), Counter(), defaultdict(dict)
    for rc in ok:
        order, info = Q.parse_ranking(rc.get("raw_text"), len(rc["pool"]))
        comp["o%d" % rc["order_idx"]] += info["complete"]
        of["o%d" % rc["order_idx"]] += 1
        orders[rc["item"]][rc["order_idx"]] = [rc["pool"][k] for k in order]
    agree, tau = [], []
    for i in sorted(orders):
        o = orders[i]
        if 0 in o and 1 in o:
            agree.append(len(set(o[0][:RF.K]) & set(o[1][:RF.K])) / RF.K)
            tau.append(Q.kendall_tau(o[0], o[1]))
    return {"requests": len(rows), "transport_failed": len(rows) - len(ok),
            "latency_s": A.boot_mean([rc["wall_s"] for rc in ok]),
            "input_tokens": A.boot_mean([Q.toks(rc)[0] for rc in ok]),
            "output_tokens": A.boot_mean([Q.toks(rc)[1] for rc in ok]),
            "extra_attempts": sum(len(rc.get("attempts") or []) - 1 for rc in rows),
            "complete_parses": {k: [comp[k], of[k]] for k in ("o0", "o1")},
            "order_pairs": len(agree), "topK_agreement": A.boot_mean(agree), "kendall_tau": A.boot_mean(tau)}


def verdict(res):
    P, S, W = res["primary"], res["secondary"], res["worst_case"]
    s_pos = sum(v["verified_positive"] for k, v in S.items() if k.startswith("sufficient|"))
    c_pos = sum(v["verified_positive"] for k, v in S.items() if k.startswith("complement|"))
    e = res["evidence_criterion"]["holds"]

    def row(p_pos, p_neg):
        if p_neg >= MAJORITY:
            return 1, "decrease"
        if e and p_pos >= MAJORITY:
            return 2, "improvement in evidence and answers"
        if s_pos >= MAJORITY and c_pos < MAJORITY:
            return 3, "improvement mainly in the sufficient subgroup"
        if p_pos < MAJORITY and s_pos < MAJORITY:
            return 4, "little or no improvement"
        return 5, "not covered by the pre-declared table"
    p_pos = sum(v["verified_positive"] for v in P.values())
    p_neg = [k for k, v in P.items() if v["verified_negative"]]
    rule, name = row(p_pos, len(p_neg))
    w_pos = sum(v["verified_positive"] for v in W.values())
    w_neg = sum(v["verified_negative"] for v in W.values())
    w_rule, w_name = row(w_pos, w_neg)
    return {"rule": rule, "row": name, "reading": READING[name],
            "P_plus": p_pos, "P_minus": len(p_neg), "S_plus": s_pos, "C_plus": c_pos, "evidence_criterion": e,
            "qualifications_verified_negative": p_neg,
            "concentrated_in_sufficient_subgroup": rule == 2 and s_pos >= MAJORITY and c_pos < MAJORITY,
            "worst_case": {"P_plus": w_pos, "P_minus": w_neg, "rule": w_rule, "row": w_name,
                           "changes_row": w_name != name,
                           "note": "row recomputed with the worst-case primary family; everything else unchanged"}}


def analyze(mode, rec_dir):
    rec_path = Path(rec_dir) / "records.jsonl"
    st = Q.load_records(rec_path)
    R = st["receipt"]
    items = RF.load_items(mode)
    if mode == "smoke":                                   # only the smoke questions that were run
        seen = {i.split("|")[2] for i in st["issued"]}
        items = [it for it in items if it["id"] in seen]
    by_id = {it["id"]: it for it in items}
    ids = {g: sorted(it["id"] for it in items if g == "all" or it["group"] == g) for g in GROUPS}
    rankings = RF.load_local(mode)
    rankings.update(Q.rankgpt_rankings(st, by_id))
    sup = {i: {k for k, p in enumerate(it["paragraphs"]) if p["supporting"]} for i, it in by_id.items()}
    nsup = {i: len(it["supporting_titles"]) for i, it in by_id.items()}

    def hit(i, rk):
        return len(set(rankings[(i, rk)][:RF.K]) & sup[i])

    problems = FZ.check()
    res = {"mode": mode, "records": RF.rel(rec_path),
           "freeze": {"verified": not problems, "problems": problems},
           "questions": {g: len(ids[g]) for g in GROUPS},
           "requests": accounting(items, st)}
    res["retrieval_coverage"] = {g: {
        "n": len(ids[g]), "supporting_in_pool": dict(sorted(Counter(str(by_id[i]["supporting_in_pool"]) for i in ids[g]).items())),
        "coverage": A.boot_mean([by_id[i]["supporting_in_pool"] / nsup[i] for i in ids[g]])} for g in GROUPS}
    res["evidence"] = {}
    for rk in Q.RANKED:
        for g in GROUPS:
            have = [i for i in ids[g] if (i, rk) in rankings]
            res["evidence"]["%s|%s" % (g, rk)] = {
                "n": len(have), "support_recall": A.boot_mean([hit(i, rk) / nsup[i] for i in have]),
                "all_supporting": A.boot_mean([float(hit(i, rk) == nsup[i]) for i in have])}
    per, fmt = defaultdict(dict), defaultdict(lambda: [0, 0])     # (model, cond) -> {question: (em, f1)}
    for rc in R.values():
        if rc.get("kind") != "answer" or rc.get("transport_failed") or rc["item"] not in by_id:
            continue
        em, f1, _ = Q.score(rc.get("raw_text"), by_id[rc["item"]]["answers"])
        per[(rc["model"], rc["cond"])][rc["item"]] = (em, f1)
        fmt[rc["model"]][0] += 1
        fmt[rc["model"]][1] += bool(RF.ANSWER_LINE.search(rc.get("raw_text") or ""))
    res["format"] = {m: {"replies": v[0], "with_answer_line": v[1]} for m, v in fmt.items()}
    res["answers"] = {}
    for g in GROUPS:
        for m in Q.ANSWER_MODELS:
            for c in RF.CONDITIONS:
                d = per.get((m, c), {})
                have = [i for i in ids[g] if i in d]
                res["answers"]["%s|%s|%s" % (g, m, c)] = {"n": len(have), "em": A.boot_mean([d[i][0] for i in have]),
                                                         "f1": A.boot_mean([d[i][1] for i in have])}

    def contrast(m, rk, g, level):
        a, b = per.get((m, "rankgpt"), {}), per.get((m, rk), {})
        common = sorted(set(a) & set(b) & set(ids[g]))
        return bounds([a[i][1] - b[i][1] for i in common], level)
    res["primary"] = {"%s|rankgpt-%s" % (m, rk): contrast(m, rk, "all", 1 - ALPHA / N_PRIMARY)
                      for m in Q.ANSWER_MODELS for rk in LOCAL}
    res["secondary"] = {"%s|%s|rankgpt-%s" % (g, m, rk): contrast(m, rk, g, 1 - ALPHA / N_SECONDARY)
                        for g in ("sufficient", "complement") for m in Q.ANSWER_MODELS for rk in LOCAL}
    ranked = [i for i in ids["all"] if (i, "rankgpt") in rankings]
    ec = {"rankgpt-%s" % rk: bounds([(hit(i, "rankgpt") - hit(i, rk)) / nsup[i] for i in ranked], 1 - ALPHA / N_EVIDENCE)
          for rk in LOCAL}
    res["evidence_criterion"] = {"contrasts": ec, "missing_rankgpt_rankings": len(ids["all"]) - len(ranked),
                                 "holds": len(ec) == N_EVIDENCE and all(v["verified_positive"] for v in ec.values())}
    res["worst_case"] = {}
    for m in Q.ANSWER_MODELS:
        a = per.get((m, "rankgpt"), {})
        for rk in LOCAL:
            b = per.get((m, rk), {})
            v = bounds([(a[i][1] if i in a else 0.0) - (b[i][1] if i in b else 1.0) for i in ids["all"]],
                       1 - ALPHA / N_PRIMARY)
            v.update({"missing_rankgpt": sum(i not in a for i in ids["all"]),
                      "missing_comparator": sum(i not in b for i in ids["all"])})
            res["worst_case"]["%s|rankgpt-%s" % (m, rk)] = v
    res["rankgpt_resources"] = resources(items, st)
    res["verdict"] = verdict(res)
    return res


def ci(t, nd=2):
    if not t or t[0] is None:
        return "-"
    return "%.*f [%.*f, %.*f]" % (nd, t[0], nd, t[1], nd, t[2])


def contrast_line(k, v):
    tag = "RankGPT better" if v["verified_positive"] else ("RankGPT worse" if v["verified_negative"] else "")
    return "  %-44s n=%3d  %s %s" % (k, v["n"], ci((v["estimate"], v["lower"], v["upper"])), tag)


def report(res):
    q, rq = res["questions"], res["requests"]
    L = ["PACKAGE 3: listwise reranking on HotpotQA's retrieved candidates (fullwiki), %s records %s" % (res["mode"], res["records"]),
         "freeze: " + ("verified, nothing changed" if res["freeze"]["verified"] else "NOT verified: " + "; ".join(res["freeze"]["problems"])),
         "questions: %d (sufficient %d, complement %d)" % (q["all"], q["sufficient"], q["complement"]),
         "requests: planned %d (ranking %d, answer %d); issued %d; received %d" % (
             rq["planned"]["total"], rq["planned"]["ranking"], rq["planned"]["answer"], rq["issued"], rq["received"]),
         "  ranking status: " + ", ".join("%s %d" % kv for kv in rq["ranking_status"].items()),
         "  answer status: " + ", ".join("%s %d" % kv for kv in rq["answer_status_totals"].items()), ""]
    L.append("RETRIEVAL COVERAGE: supporting paragraphs among the 10 candidates, mean share [95% CI] (count with 0/1/2)")
    for g in GROUPS:
        v = res["retrieval_coverage"][g]
        L.append("  %-11s n=%3d  %s  %s" % (g, v["n"], ci(v["coverage"]), v["supporting_in_pool"]))
    L.append("")
    L.append("EVIDENCE at K = 2, mean [95% CI]: support recall | all supporting in the top 2")
    for rk in Q.RANKED:
        for g in GROUPS:
            v = res["evidence"]["%s|%s" % (g, rk)]
            L.append("  %-8s %-11s n=%3d  %s | %s" % (rk, g, v["n"], ci(v["support_recall"]), ci(v["all_supporting"])))
    L.append("")
    L.append("ANSWERS, mean [95% CI]: exact match | F1")
    for g in GROUPS:
        for m in Q.ANSWER_MODELS:
            for c in RF.CONDITIONS:
                v = res["answers"]["%s|%s|%s" % (g, m, c)]
                L.append("  %-11s %-16s %-8s n=%3d  %s | %s" % (g, m, c, v["n"], ci(v["em"]), ci(v["f1"])))
    L.append("")
    L.append("PRIMARY: RankGPT minus each local ranker, F1, all questions (estimate [simultaneous 95%, Bonferroni over 15])")
    L += [contrast_line(k, v) for k, v in res["primary"].items()]
    L.append("")
    L.append("SECONDARY: the same contrasts per subgroup (estimate [simultaneous 95%, Bonferroni over 30])")
    L += [contrast_line(k, v) for k, v in res["secondary"].items()]
    L.append("")
    ec = res["evidence_criterion"]
    L.append("EVIDENCE CRITERION: RankGPT minus each local ranker, support recall at K, all questions "
             "(simultaneous 95%%, Bonferroni over 5); missing RankGPT rankings %d" % ec["missing_rankgpt_rankings"])
    L += [contrast_line(k, v) for k, v in ec["contrasts"].items()]
    L.append("  criterion holds (all five verified positive): %s" % ("yes" if ec["holds"] else "no"))
    L.append("")
    L.append("WORST CASE (primary family; missing RankGPT answer F1 0, missing comparator answer F1 1)")
    for k, v in res["worst_case"].items():
        L.append(contrast_line(k, v) + "  (missing: RankGPT %d, comparator %d)" % (v["missing_rankgpt"], v["missing_comparator"]))
    L.append("")
    r = res["rankgpt_resources"]
    L.append("RANKGPT RESOURCES (Haiku-4.5, both input orders): requests %d, transport failures %d, extra attempts %d" % (
        r["requests"], r["transport_failed"], r["extra_attempts"]))
    L.append("  latency s %s | input tokens %s | output tokens %s" % (ci(r["latency_s"]), ci(r["input_tokens"], 0), ci(r["output_tokens"], 0)))
    L.append("  complete parses o0 %d/%d, o1 %d/%d; top-2 agreement o0 vs o1 %s; Kendall tau %s (pairs %d)" % (
        r["complete_parses"]["o0"][0], r["complete_parses"]["o0"][1], r["complete_parses"]["o1"][0],
        r["complete_parses"]["o1"][1], ci(r["topK_agreement"]), ci(r["kendall_tau"]), r["order_pairs"]))
    L.append("")
    L.append("Answer-line compliance: " + "; ".join("%s %d/%d" % (m, v["with_answer_line"], v["replies"]) for m, v in res["format"].items()))
    L.append("")
    vd = res["verdict"]
    L.append("VERDICT (PROTOCOL_FULLWIKI.md, Section 7): rule %d, %s: %s" % (vd["rule"], vd["row"], vd["reading"]))
    L.append("  P+ %d, P- %d (of 15); S+ %d, C+ %d (of 15 each); evidence criterion %s" % (
        vd["P_plus"], vd["P_minus"], vd["S_plus"], vd["C_plus"], "holds" if vd["evidence_criterion"] else "does not hold"))
    if vd["qualifications_verified_negative"]:
        L.append("  qualifications (verified negative): " + ", ".join(vd["qualifications_verified_negative"]))
    if vd["concentrated_in_sufficient_subgroup"]:
        L.append("  the improvement is concentrated in the sufficient subgroup (S+ >= 8, C+ < 8)")
    w = vd["worst_case"]
    L.append("  worst case: P+ %d, P- %d -> rule %d, %s (%s)" % (
        w["P_plus"], w["P_minus"], w["rule"], w["row"], "changes the row" if w["changes_row"] else "same row"))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--mock", action="store_true", help="analyze the mock records")
    g.add_argument("--smoke", action="store_true", help="analyze the smoke records")
    ap.add_argument("--records", default=None, help="record directory for --mock or --smoke (default: the mode's)")
    a = ap.parse_args()
    mode = "mock" if a.mock else "smoke" if a.smoke else "confirm"
    if a.records and mode == "confirm":
        ap.error("the confirmatory analysis reads only natural_data/package3/confirm_fullwiki")
    rec_dir = Path(a.records) if a.records else RF.SETS[mode]["out"]
    if not (rec_dir / "records.jsonl").exists():
        raise SystemExit("no records in %s" % RF.rel(rec_dir))
    res = analyze(mode, rec_dir)
    text = report(res)
    out_dir = RESULTS if mode == "confirm" else rec_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    RF.write_lf(out_dir / "analysis_fullwiki.json", json.dumps(res, indent=1) + "\n")
    RF.write_lf(out_dir / "analysis_fullwiki.md", text + "\n")
    print(text)
    print("\nwritten: %s, %s" % (RF.rel(out_dir / "analysis_fullwiki.json"), RF.rel(out_dir / "analysis_fullwiki.md")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
