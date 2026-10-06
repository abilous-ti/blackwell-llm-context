r"""Freeze of the declarative clarified-contract experiment: hashes of the code, the protocol and the
confirmatory schedule (hidden states included), written before the first confirmatory request.

  python harness/package2/run_clarify.py --schedule-only --n 40
  python harness/package2/freeze_clarify.py            (freeze; refused once confirmatory records exist)
  python harness/package2/freeze_clarify.py --verify
"""
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FREEZE = ROOT / "results" / "package2" / "FREEZE_clarify.json"
CONFIRM = ROOT / "results" / "package2" / "confirm_clarify"
FILES = ["harness/package2/run_clarify.py", "harness/package2/analyze_clarify.py",
         "harness/package2/freeze_clarify.py", "harness/package2/PROTOCOL_CLARIFY.md", "harness/package2/pairs.py",
         "harness/package2/run_pairs.py", "harness/replication/transport.py", "harness/replication/design.json",
         "harness/measure_blackwell.py", "results/package2/confirm_clarify/schedule.jsonl"]


def digest(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def parameters():
    rows = [json.loads(l) for l in open(CONFIRM / "schedule.jsonl", encoding="utf-8") if l.strip()]
    return {"requests": len(rows), "blocks_per_cell": max(r["block"] for r in rows) + 1,
            "models": sorted({r["model"] for r in rows}), "lanes": max(r["lane"] for r in rows) + 1,
            "alpha_primary": "0.05/24 (two-sided)",
            "schedule_draws": "operating-system entropy (random.SystemRandom), recorded in the schedule"}


def check():
    if not FREEZE.exists():
        return ["no freeze (%s)" % FREEZE.name]
    f = json.loads(FREEZE.read_text(encoding="utf-8"))
    problems = []
    for rel, h in f["sha256"].items():
        if not (ROOT / rel).exists():
            problems.append("missing %s" % rel)
        elif digest(rel) != h:
            problems.append("changed %s" % rel)
    return problems


def freeze():
    if FREEZE.exists():
        raise SystemExit("already frozen at %s" % json.loads(FREEZE.read_text(encoding="utf-8"))["frozen_at_utc"])
    if not (CONFIRM / "schedule.jsonl").exists():
        raise SystemExit("no confirmatory schedule: run run_clarify.py --schedule-only first")
    rec = CONFIRM / "records.jsonl"
    if rec.exists() and rec.stat().st_size > 0:
        raise SystemExit("confirmatory records exist; a freeze after data collection is refused")
    out = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "parameters": parameters(), "sha256": {rel: digest(rel) for rel in FILES}}
    FREEZE.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print("frozen %s: %d files" % (out["frozen_at_utc"], len(FILES)))


def main():
    if "--verify" in sys.argv:
        p = check()
        if p:
            print("freeze NOT verified: " + "; ".join(p))
            sys.exit(1)
        print("freeze %s: verified, nothing changed" % json.loads(FREEZE.read_text(encoding="utf-8"))["frozen_at_utc"])
    else:
        freeze()


if __name__ == "__main__":
    main()
