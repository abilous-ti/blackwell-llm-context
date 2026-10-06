r"""Amended analysis of the declarative label experiment (PROTOCOL_LABELS_AMENDMENT.md).

A1 (amended primary): one-sided Clopper-Pearson lower bound on own-source accuracy with every
   scheduled block in the denominator (missing outcomes count as incorrect), alpha = 0.05/24.
A2 (drift-robust): Hoeffding lower bound L_H = k/n - sqrt(ln(1/alpha)/(2n)) on the mean success
   probability over blocks, same n and alpha.
The complete-case bound of the frozen analysis is reported as a sensitivity analysis. The frozen
analyze_labels.py is imported and not changed.

  python harness/package2/analyze_labels_amended.py --record          (before any outcome is viewed)
  python harness/package2/analyze_labels_amended.py --verify-record
  python harness/package2/analyze_labels_amended.py [record_dir]
"""
import hashlib
import io
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import analyze_labels as AL  # noqa: E402

RECORD = ROOT / "results" / "package2" / "FREEZE_labels_amendment.json"
CONFIRM = ROOT / "results" / "package2" / "confirm_labels"
FILES = ["harness/package2/PROTOCOL_LABELS_AMENDMENT.md", "harness/package2/analyze_labels_amended.py"]


def hoeffding_lower(k, n, alpha):
    return k / n - math.sqrt(math.log(1 / alpha) / (2 * n)) if n else None


def analyze(d):
    base = AL.analyze(d)
    rows, certified = [], {}
    for r in base["primary"]:
        k, n = r["k"], r["worst_case"]["n"]
        a1 = r["worst_case"]["cp_lower"]
        a2 = hoeffding_lower(k, n, AL.ALPHA)
        row = {"model": r["model"], "pair": r["pair"], "task": r["task"], "own": r["own"], "cap": r["cap"],
               "correct": k, "scheduled": n, "received": r["n"],
               "A1_cp_lower": a1, "A1_verified": a1 is not None and a1 > r["cap"],
               "A1_deficiency_lower_bound": max(0.0, a1 - r["cap"]) if a1 is not None else None,
               "A2_hoeffding_lower": a2, "A2_verified": a2 is not None and a2 > r["cap"],
               "A2_deficiency_lower_bound": max(0.0, a2 - r["cap"]) if a2 is not None else None,
               "complete_case_cp_lower": r["cp_lower"], "complete_case_verified": r["verified"],
               "bound_direction": r["bound_direction"]}
        rows.append(row)
        certified.setdefault((r["model"], r["pair"]), []).append(row)
    pairs = [{"model": m, "pair": p,
              "A1_certified_incomparable": all(x["A1_verified"] for x in v) and len(v) == 2,
              "A2_certified_incomparable": all(x["A2_verified"] for x in v) and len(v) == 2}
             for (m, p), v in certified.items()]
    return {"n": base["n"], "amended_primary": rows, "certified_pairs": pairs,
            "diagnostics": base["diagnostics"], "invalid": base["invalid"]}


def fmt(x):
    return "-" if x is None else "%.3f" % x


def report(res):
    L = ["requests: scheduled %(scheduled)d, received %(received)d, graded %(graded)d, transport failures %(transport_failed)d" % res["n"], ""]
    L.append("AMENDED PRIMARY (A1, CP, missing = incorrect) and DRIFT-ROBUST (A2, Hoeffding); alpha = 0.05/24 each")
    L.append("%-16s %-18s %-4s %-7s %-6s %-14s %-14s %-12s %s" % ("model", "task", "own", "k/sched", "cap", "A1 L / ok",
                                                               "A2 L_H / ok", "complete-case", "deficiency bounds A1 / A2"))
    for r in res["amended_primary"]:
        L.append("%-16s %-18s %-4s %2d/%-4d %-6s %-6s %-7s %-6s %-7s %-12s %s >= %s / %s" % (
            r["model"], r["task"], r["own"], r["correct"], r["scheduled"], fmt(r["cap"]),
            fmt(r["A1_cp_lower"]), "yes" if r["A1_verified"] else "no",
            fmt(r["A2_hoeffding_lower"]), "yes" if r["A2_verified"] else "no",
            "yes" if r["complete_case_verified"] else "no", r["bound_direction"],
            fmt(r["A1_deficiency_lower_bound"]), fmt(r["A2_deficiency_lower_bound"])))
    p = res["amended_primary"]
    L.append("statements verified: A1 %d of %d; A2 %d of %d; complete-case %d of %d" % (
        sum(r["A1_verified"] for r in p), len(p), sum(r["A2_verified"] for r in p), len(p),
        sum(r["complete_case_verified"] for r in p), len(p)))
    c = res["certified_pairs"]
    L.append("pair-model combinations certified incomparable: A1 %d of %d; A2 %d of %d" % (
        sum(x["A1_certified_incomparable"] for x in c), len(c), sum(x["A2_certified_incomparable"] for x in c), len(c)))
    L.append("diagnostic flags (frozen analysis, 0.05/48): %d" % sum(r["flag"] for r in res["diagnostics"]))
    return "\n".join(L)


def digest(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def record():
    if RECORD.exists():
        raise SystemExit("amendment already recorded")
    counts = {"issued": 0, "received": 0}
    rp = CONFIRM / "records.jsonl"
    if rp.exists():                      # line types only; no outcome is parsed
        for line in open(rp, encoding="utf-8"):
            counts["issued"] += '"type": "issued"' in line
            counts["received"] += '"type": "receipt"' in line
    out = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "confirmatory_lines_at_recording": counts, "outcomes_viewed_before_recording": False,
           "sha256": {rel: digest(rel) for rel in FILES}}
    RECORD.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print("amendment recorded %s (confirmatory lines: %s)" % (out["recorded_at_utc"], counts))


def verify_record():
    f = json.loads(RECORD.read_text(encoding="utf-8"))
    bad = [rel for rel, h in f["sha256"].items() if digest(rel) != h]
    print("amendment %s: %s" % (f["recorded_at_utc"], "verified, nothing changed" if not bad else "CHANGED " + ", ".join(bad)))
    return not bad


def main():
    if "--record" in sys.argv:
        record()
        return
    if "--verify-record" in sys.argv:
        sys.exit(0 if verify_record() else 1)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = Path(args[0]) if args else CONFIRM
    res = analyze(d)
    text = report(res)
    (d / "analysis_labels_amended.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (d / "analysis_labels_amended.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
