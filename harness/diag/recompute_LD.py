"""Recompute the incomparability certificate from the retention re-measurement.

Uses the harness's own certify_incomparable so the arithmetic cannot drift from
the published path. Reports both directions under the published verifier and,
where a cell has a ledger import to neutralize, under the neutralized one.

  python recompute_LD.py ../../results/audit
"""
import sys, os, json, glob, re
from pathlib import Path

HARNESS = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, HARNESS)
import measure_blackwell as mb  # noqa: E402

BATTERY = ["api_post_ok", "api_argorder", "enc_amount", "trap_store_wire"]
ROSTER = ["haiku", "sonnet", "opus", "deepseek", "kimi", "gpt55"]
PUBLISHED = {                       # Table: verified incomparability, paper 1
    "haiku": (0.762, 0.762), "sonnet": (0.715, 0.762), "opus": (0.715, 0.762),
    "gpt55": (0.762, 0.762), "deepseek": (0.347, 0.715), "kimi": (0.675, 0.762),
}


def load(out, label, task, arm):
    f = os.path.join(out, "audit_%s_%s_%s.json" % (label, task, arm))
    if os.path.exists(f):
        return json.load(open(f, encoding="utf-8"))
    # Haiku api_post_ok was measured with retention by haiku_ctrl.py under the same
    # prompt, extractor and verifier; reuse rather than re-draw.
    if label == "haiku" and task == "api_post_ok":
        alt = os.path.join(os.path.dirname(out), "diag", "ctrl_api_post_ok_%s.json" % arm)
        if os.path.exists(alt):
            return json.load(open(alt, encoding="utf-8"))
    return None


def counts(rows, key):
    k = sum(1 for r in rows if r.get(key))
    return [k, len(rows)]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "../../results/audit"
    print("%-12s  %-28s  %-28s  %s" % ("model", "published L(W1,W2)/L(W2,W1)",
                                       "re-measured (published verif.)", "import-neutralized"))
    for lab in ROSTER:
        cA, cB, cAn, cBn, missing = {}, {}, {}, {}, []
        for t in BATTERY:
            w1, w2 = load(out, lab, t, "W1"), load(out, lab, t, "W2")
            if w1 is None or w2 is None:
                missing.append("%s:%s" % (t, "W1" if w1 is None else "W2"))
                continue
            cA[t], cB[t] = counts(w1, "pass_original"), counts(w2, "pass_original")
            cAn[t], cBn[t] = counts(w1, "pass_neutral"), counts(w2, "pass_neutral")
        if missing:
            print("%-12s  incomplete, missing: %s" % (lab, ", ".join(missing)))
            continue
        by = list(cA.keys())
        r = mb.certify_incomparable(cA, cB, by, eta=0.10)
        rn = mb.certify_incomparable(cAn, cBn, by, eta=0.10)
        p = PUBLISHED.get(lab, (None, None))
        ok = lambda x: "verified" if (x["L_AB"] > 0 and x["L_BA"] > 0) else "** NOT VERIFIED **"
        print("%-12s  %+.3f/%+.3f   %+.3f/%+.3f %-18s  %+.3f/%+.3f %s"
              % (lab, p[0], p[1],
                 r["L_AB"], r["L_BA"], ok(r),
                 rn["L_AB"], rn["L_BA"], ok(rn)))
        for t in by:
            d = r["detail"][t]
            print("        %-18s W1 %s  W2 %s" % (t, d["A_ci"], d["B_ci"]))


if __name__ == "__main__":
    main()
