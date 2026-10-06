r"""Sensitivity analysis: the 24 decisions without the two windows whose boundaries were changed.

d2-pm (third window) had its end moved twice, the second time after 169 of its requests had been
issued; d4-am (sixth window) had its start moved from 10:00 to 09:00 before any of its requests
(results/replication/DEVIATIONS.md). This script repeats the frozen primary analysis on the four
unchanged windows only (d1-pm, d2-am, d3-am, d3-pm), with the same estimator, bound, family level
and margin, and reports every decision next to the full analysis. Reads the records; no model call.

  python harness/replication/sensitivity_windows.py
"""
import io
import json
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import analyze  # noqa: E402
import records  # noqa: E402
import stats  # noqa: E402

AMENDED = ("d2-pm", "d4-am")


def decisions(design, bl, windows):
    alpha, margin = design["analysis"]["per_statement_alpha"], design["analysis"]["harm_margin"]
    out = {}
    for m in [x["label"] for x in design["models"]]:
        for c in design["contrasts"]:
            d = {w: v for w, v in analyze.diffs(bl, m, c).items() if w in windows}
            s = stats.contrast_summary(d, alpha, c["direction"], margin if c["direction"] < 0 else None,
                                       planned_windows=list(windows))
            dec = (s.get("verified"),) if c["direction"] > 0 else (s.get("verified_any_harm"), s.get("verified_margin"))
            out[(m, c["id"])] = (s["n_blocks"], s["estimate"], s["primary_bound"], dec)
    return out


def main():
    design = json.load(open(HERE / "design.json", encoding="utf-8"))
    base = ROOT / "results" / "replication"
    rows = analyze.load_schedule(design, str(base))
    st = records.read_dir(str(base / "records"))
    status, _closed, _stray = analyze.reconcile(rows, st)
    bl = analyze.outcomes(rows, st, status, "published")
    planned = [w["id"] for w in design["windows"]]
    kept = [w for w in planned if w not in AMENDED]
    full, sub = decisions(design, bl, planned), decisions(design, bl, kept)
    changed = [k for k in full if full[k][3] != sub[k][3]]
    res = {"windows_kept": kept, "windows_excluded": list(AMENDED), "decisions_changed": ["%s %s" % k for k in changed],
           "rows": {"%s %s" % k: {"full": {"blocks": full[k][0], "estimate": full[k][1], "bound": full[k][2], "decision": full[k][3]},
                                  "four_windows": {"blocks": sub[k][0], "estimate": sub[k][1], "bound": sub[k][2], "decision": sub[k][3]}}
                    for k in full}}
    json.dump(res, open(base / "sensitivity_windows.json", "w", encoding="utf-8"), indent=1)
    print("windows kept: %s (excluded %s)" % (", ".join(kept), ", ".join(AMENDED)))
    print("%-22s %-28s %-28s" % ("model contrast", "six windows: blocks est bound", "four windows: blocks est bound"))
    for k in full:
        f, s = full[k], sub[k]
        print("%-22s %4d %+.3f %+.3f %-9s %4d %+.3f %+.3f %s" % (
            "%s %s" % k, f[0], f[1], f[2], f[3], s[0], s[1], s[2], s[3]))
    print("\ndecisions changed by excluding the amended windows: %s" % (", ".join("%s %s" % k for k in changed) or "none"))


if __name__ == "__main__":
    main()
