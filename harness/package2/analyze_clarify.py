r"""Analysis of the clarified-contract experiment, as fixed in PROTOCOL_CLARIFY.md (Section 4).

Primary (24 two-sided statements: 4 tasks x 6 models, alpha = 0.05/24 each): the harm under the
clarified contract, H_c = PASS(AcB) - PASS(Ac), bounded by Clopper-Pearson intervals for the two
arms, each at level alpha/2 (lower = L(AcB) - U(Ac), upper = U(AcB) - L(Ac)). Reading:
  harm persists            upper < 0 (and "beyond the margin" when upper <= -0.30);
  no harm beyond margin    lower > -0.30;
  inconclusive             otherwise.
Secondary (each at its own level, never part of the primary): the harm under the original texts,
H_o = PASS(AB) - PASS(A), and the effect of the sentence alone, C = PASS(Ac) - PASS(A), both with the
same construction; block-difference Hoeffding bounds for H_c (two-sided, range 2) and for the
difference in differences D = H_c - H_o (range 4), complete blocks only. Descriptive: failing AB and
AcB replies that apply the other source's transformation to the argument (pattern counts).

  python harness/package2/analyze_clarify.py [record_dir]   (default results/package2/confirm_clarify)
"""
import io
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import measure_blackwell as mb  # noqa: E402

MODELS = ["Haiku-4.5", "Sonnet-4.6", "Opus-4.8", "GPT-5.5", "DeepSeek-V4-Pro", "Kimi-K2.6"]
TASKS = ["api_post_ok", "api_argorder", "cache_put_ok", "inv_book"]
ALPHA = 0.05 / 24
MARGIN = -0.30
TRANSFORM = {"api_post_ok": re.compile(r"encode|%\s*10|['\"]#"), "api_argorder": re.compile(r"encode|%\s*10|['\"]#"),
             "cache_put_ok": re.compile(r"kx7|re\.sub|\.lower\(\)"), "inv_book": re.compile(r"iv9|zfill|%\s*7|KMPRTWY")}


def cp(k, n, alpha):
    return mb.clopper_pearson(k, n, alpha) if n else (0.0, 1.0)


def diff_bounds(k1, n1, k0, n0, alpha):
    """Two-sided simultaneous bounds on p1 - p0 from two CP intervals at alpha/2 each."""
    l1, u1 = cp(k1, n1, alpha / 2)
    l0, u0 = cp(k0, n0, alpha / 2)
    return (k1 / n1 - k0 / n0 if n1 and n0 else None), l1 - u0, u1 - l0


def load(d):
    d = Path(d)
    sched = [json.loads(l) for l in open(d / "schedule.jsonl", encoding="utf-8") if l.strip()]
    rec, grd = {}, {}
    for line in open(d / "records.jsonl", encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("type") == "receipt":
            rec[r["id"]] = r
        elif r.get("type") == "grade":
            grd[r["id"]] = r
    return sched, rec, grd


def analyze(d):
    sched, rec, grd = load(d)
    Y = defaultdict(dict)                 # (model, task, block) -> {arm: 0/1}
    for s in sched:
        g = grd.get(s["id"])
        if g is None or rec.get(s["id"], {}).get("transport_failed"):
            continue
        Y[(s["model"], s["task"], s["block"])][s["arm"]] = int(bool(g["pass"]))
    cnt = defaultdict(lambda: [0, 0])
    for (m, t, b), ys in Y.items():
        for arm, v in ys.items():
            cnt[(m, t, arm)][0] += v
            cnt[(m, t, arm)][1] += 1
    res = {"n": {"scheduled": len(sched), "received": len(rec), "graded": len(grd),
                 "transport_failed": sum(1 for r in rec.values() if r.get("transport_failed"))},
           "counts": {}, "primary": [], "secondary": [], "transformation": []}
    for (m, t, arm), (k, n) in sorted(cnt.items()):
        res["counts"]["%s|%s|%s" % (m, t, arm)] = [k, n]
    for m in MODELS:
        for t in TASKS:
            k = {arm: cnt[(m, t, arm)] for arm in ("A", "AB", "Ac", "AcB")}
            est, lo, hi = diff_bounds(*k["AcB"], *k["Ac"], ALPHA)
            reading = ("harm persists beyond the margin" if hi <= MARGIN else "harm persists" if hi < 0
                       else "no harm beyond the margin" if lo > MARGIN else "inconclusive")
            res["primary"].append({"model": m, "task": t, "estimate": est, "lower": lo, "upper": hi, "reading": reading,
                                   "counts": {a: k[a] for a in k}})
            eo, lo_o, hi_o = diff_bounds(*k["AB"], *k["A"], ALPHA)
            ec, lo_c, hi_c = diff_bounds(*k["Ac"], *k["A"], ALPHA)
            blocks = [ys for (mm, tt, b), ys in Y.items() if (mm, tt) == (m, t) and len(ys) == 4]
            B = len(blocks)
            hc = [ys["AcB"] - ys["Ac"] for ys in blocks]
            dd = [(ys["AcB"] - ys["Ac"]) - (ys["AB"] - ys["A"]) for ys in blocks]
            h2 = math.sqrt(2 * math.log(2 / ALPHA) / B) if B else None
            res["secondary"].append({
                "model": m, "task": t, "H_o": [eo, lo_o, hi_o], "C": [ec, lo_c, hi_c], "blocks": B,
                "H_c_hoeffding": [sum(hc) / B, sum(hc) / B - h2, sum(hc) / B + h2] if B else None,
                "D_hoeffding": [sum(dd) / B, sum(dd) / B - 2 * h2, sum(dd) / B + 2 * h2] if B else None})
    for s in sched:
        if s["arm"] not in ("AB", "AcB"):
            continue
        g = grd.get(s["id"])
        if g is None or g["pass"]:
            continue
        code = mb._extract_code(rec[s["id"]].get("raw_text") or "")
        res["transformation"].append((s["model"], s["task"], s["arm"], bool(TRANSFORM[s["task"]].search(code))))
    agg = Counter()
    for m, t, arm, hit in res["transformation"]:
        agg[(t, arm, "fail")] += 1
        agg[(t, arm, "hit")] += hit
    res["transformation_summary"] = {"%s|%s" % (t, arm): [agg[(t, arm, "hit")], agg[(t, arm, "fail")]]
                                     for t in TASKS for arm in ("AB", "AcB")}
    del res["transformation"]
    return res


def f(x):
    return "-" if x is None else "%+.2f" % x


def report(res):
    L = ["requests: scheduled %(scheduled)d, received %(received)d, graded %(graded)d, transport failures %(transport_failed)d" % res["n"], ""]
    L.append("PRIMARY: harm under the clarified contract, PASS(AcB) - PASS(Ac) (CP, two-sided, alpha = 0.05/24)")
    for r in res["primary"]:
        c = r["counts"]
        L.append("  %-16s %-13s A %2d/%-2d AB %2d/%-2d Ac %2d/%-2d AcB %2d/%-2d  H_c %s [%s, %s]  %s" % (
            r["model"], r["task"], *c["A"], *c["AB"], *c["Ac"], *c["AcB"], f(r["estimate"]), f(r["lower"]), f(r["upper"]), r["reading"]))
    rd = Counter(r["reading"] for r in res["primary"])
    L.append("readings: " + "; ".join("%s %d" % (k, v) for k, v in sorted(rd.items())))
    L.append("")
    L.append("SECONDARY: H_o = PASS(AB) - PASS(A); C = PASS(Ac) - PASS(A) (CP); D = H_c - H_o (block Hoeffding)")
    for r in res["secondary"]:
        L.append("  %-16s %-13s H_o %s [%s, %s]  C %s [%s, %s]  D %s [%s, %s] (B=%d)" % (
            r["model"], r["task"], *map(f, r["H_o"]), *map(f, r["C"]), *map(f, r["D_hoeffding"] or [None] * 3), r["blocks"]))
    L.append("")
    L.append("DESCRIPTIVE: failing superset replies applying the other source's transformation (hit/fail)")
    for k, v in res["transformation_summary"].items():
        L.append("  %-22s %d/%d" % (k, v[0], v[1]))
    return "\n".join(L)


def main():
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results" / "package2" / "confirm_clarify"
    res = analyze(d)
    text = report(res)
    (d / "analysis_clarify.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (d / "analysis_clarify.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
