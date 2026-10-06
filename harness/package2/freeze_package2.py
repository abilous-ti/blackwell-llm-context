r"""Freeze package 2 before its confirmatory runs: SHA-256 of the code, protocol, items, rankings
and certificates, written to results/package2/FREEZE.json. `--verify` recomputes them and lists any
file that changed since (the analysis must report a clean verify).

  python harness/package2/freeze_package2.py            (freeze; refuses if confirmatory records exist)
  python harness/package2/freeze_package2.py --verify
"""
import hashlib
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent.parent
FILES = [
    "harness/package2/pairs.py", "harness/package2/certify_pairs.py", "harness/package2/run_pairs.py",
    "harness/package2/run_qa.py", "harness/package2/rank_local.py", "harness/package2/qa_data.py",
    "harness/package2/PROTOCOL.md", "harness/package2/PILOT.md", "harness/replication/transport.py",
    "harness/measure_blackwell.py", "harness/replication/design.json",
    "natural_data/package2/items_confirm.jsonl", "natural_data/package2/rankings_local_confirm.jsonl",
    "natural_data/package2/splits.json", "results/package2/certificates.json",
]
FREEZE = ROOT / "results" / "package2" / "FREEZE.json"
CONFIRM_RECORDS = [ROOT / "results" / "package2" / "confirm_pairs" / "records.jsonl",
                   ROOT / "natural_data" / "package2" / "confirm_qa" / "records.jsonl"]


def digests():
    return {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        fz = json.load(open(FREEZE, encoding="utf-8"))
        now = digests()
        changed = [f for f in FILES if now.get(f) != fz["sha256"].get(f)]
        print("freeze %s: %s" % (fz["frozen_at_utc"], "verified, nothing changed" if not changed
                                 else "CHANGED: " + ", ".join(changed)))
        return 1 if changed else 0
    started = [str(p) for p in CONFIRM_RECORDS if p.exists() and p.stat().st_size > 0]
    if started:
        raise SystemExit("confirmatory records already exist (%s): not freezing" % ", ".join(started))
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = None
    fz = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "harness_commit": commit,
          "parameters": {"pairs_blocks_per_task": 40, "pairs_seed": 20261006, "pairs_lanes": 4,
                         "qa_budget_K": {"hotpotqa": 2, "musique": 4}, "qa_lanes": 4,
                         "answer_models": ["Haiku-4.5", "GPT-5.5", "DeepSeek-V4-Pro"],
                         "rank_model": "Haiku-4.5", "overhead_models": ["Haiku-4.5", "GPT-5.5"]},
          "sha256": digests()}
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(fz, open(FREEZE, "w", encoding="utf-8"), indent=1)
    print("frozen at %s: %d files" % (fz["frozen_at_utc"], len(FILES)))


if __name__ == "__main__":
    sys.exit(main())
