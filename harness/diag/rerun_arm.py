#!/usr/bin/env python3
"""Re-measure one arm of one model on chosen cells, in the published single-shot
regime and with the published prompt, writing a log whose header records the regime.

Why this exists. Four result files cited by the manuscript are arm-only
re-measurements that were produced by ad-hoc scripts nobody kept, so their regime
was asserted in prose rather than recoverable from a run log. That is the same
provenance gap that let three regime mismatches reach the manuscript. This script
closes it: it uses measure_blackwell.run_one, which is the function the six-model
tables are built from, so a re-run here is the same protocol by construction and
the log says so.

It deliberately does NOT use diag/audit_any.py: that tool appends its own
instruction suffix to the prompt, which is a different measurement condition.

Examples
--------
  python harness/diag/rerun_arm.py --model claude-opus-4-8 --arm W1plus \\
      --tasks api_post_ok,api_argorder,enc_amount,trap_store_wire \\
      --runs 40 --out results/blackwell_opus_ss_W1plus_rerun.json

  python harness/diag/rerun_arm.py --model claude-haiku-4-5-20251001 --arm W1 \\
      --tasks enc_amount --runs 40 --out results/blackwell_haiku_ss_W1_enc_rerun2.json
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import measure_blackwell as mb  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--arm", required=True, help="none, W1, W2, W1plus, W1plus_rev, W1pad, ...")
    ap.add_argument("--tasks", required=True, help="comma list of task ids")
    ap.add_argument("--runs", type=int, default=40)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    ap.add_argument("--agentic", action="store_true",
                    help="run the multi-turn CLI path instead (default is single-shot)")
    a = ap.parse_args()

    singleshot = not a.agentic
    if a.arm not in mb.ARMS:
        ap.error("unknown arm %r; known: %s" % (a.arm, ",".join(sorted(mb.ARMS))))
    by_id = {t["id"]: t for t in mb.TASKS}
    tasks = []
    for tid in a.tasks.split(","):
        tid = tid.strip()
        if tid not in by_id:
            ap.error("unknown task %r; known: %s" % (tid, ",".join(sorted(by_id))))
        tasks.append(by_id[tid])

    # The header is the regime record. harness/diag/check_regimes.py reads it.
    print("BLACKWELL arm re-measurement | arm=%s | tasks=%s | n=%d/cell | %d calls"
          % (a.arm, [t["id"] for t in tasks], a.runs, len(tasks) * a.runs))
    print("  model = %s%s" % (a.model, "  [SINGLE-SHOT]" if singleshot else ""))
    print("  prompt = published (measure_blackwell.run_one), no added instruction suffix")
    sys.stdout.flush()

    counts, cost, errs = {}, 0.0, 0
    for t in tasks:
        t0 = time.time()
        with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = [ex.submit(mb.run_one, t, a.arm, False, i, a.model, singleshot)
                    for i in range(a.runs)]
            rows = []
            for f in cf.as_completed(futs):
                try:
                    rows.append(f.result())
                except Exception:
                    errs += 1
                    rows.append({"solved": False, "cost": 0.0})
        k = sum(1 for r in rows if r.get("solved"))
        cost += sum(r.get("cost", 0.0) or 0.0 for r in rows)
        counts["%s|%s" % (a.arm, t["id"])] = [k, len(rows)]
        print("  arm=%-6s %-18s PASS %d/%d=%d%%   (%.0fs)"
              % (a.arm, t["id"], k, len(rows), round(100 * k / len(rows)), time.time() - t0))
        sys.stdout.flush()

    out = {"counts": counts, "model": a.model,
           "regime": "cli-singleshot" if singleshot else "cli-agentic",
           "prompt": "published", "n_per_cell": a.runs,
           "transport_errors": errs, "total_cost_usd": round(cost, 6)}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("wrote %s   errors=%d   cost=$%.4f" % (a.out, errs, cost))
    return 0


if __name__ == "__main__":
    sys.exit(main())
