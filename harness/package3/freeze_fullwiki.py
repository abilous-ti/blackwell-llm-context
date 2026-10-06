r"""Freeze package 3 before its first request (PROTOCOL_FULLWIKI.md). The freeze records:
  - SHA-256 of the protocol, the code (package 3's files and the package 2 and replication modules
    they import), the source file, the sample, the items, the IDF table and the local rankings;
  - the seeds and the design parameters;
  - the sample itself (ids, groups, candidate titles).
It is written to results/package3/FREEZE_fullwiki.json. `--verify` recomputes every hash: run_fullwiki.py
refuses the confirmatory run unless nothing changed, and analyze_fullwiki.py reports the result.
Mock and smoke records are not frozen.

  python harness/package3/freeze_fullwiki.py            (refused if a freeze or confirmatory records exist)
  python harness/package3/freeze_fullwiki.py --verify
"""
import hashlib
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True          # never write bytecode next to package 2's modules
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FREEZE = ROOT / "results" / "package3" / "FREEZE_fullwiki.json"
CONFIRM_RECORDS = ROOT / "natural_data" / "package3" / "confirm_fullwiki" / "records.jsonl"
SAMPLE = ROOT / "natural_data" / "package3" / "sample.json"
FILES = [
    "harness/package3/PROTOCOL_FULLWIKI.md",
    "harness/package3/fullwiki_data.py",
    "harness/package3/run_fullwiki.py",
    "harness/package3/analyze_fullwiki.py",
    "harness/package3/freeze_fullwiki.py",
    "harness/package2/run_qa.py",
    "harness/package2/analyze_qa.py",
    "harness/package2/rank_local.py",
    "harness/replication/transport.py",
    "harness/replication/design.json",
    "natural_data/hotpot_dev_fullwiki.parquet",
    "natural_data/package3/sample.json",
    "natural_data/package3/items_confirm.jsonl",
    "natural_data/package3/items_smoke.jsonl",
    "natural_data/package3/idf_fullwiki.json",
    "natural_data/package3/rankings_local_confirm.jsonl",
    "natural_data/package3/rankings_local_smoke.jsonl",
    "natural_data/package3/local_models.json",
]


def digest(rel):
    h = hashlib.sha256()
    with open(ROOT / rel, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check():
    """Problems with the freeze (empty list = every frozen file present and unchanged)."""
    if not FREEZE.exists():
        return ["no freeze (results/package3/FREEZE_fullwiki.json)"]
    fz = json.loads(FREEZE.read_text(encoding="utf-8"))
    problems = ["not in the freeze: %s" % f for f in FILES if f not in fz["sha256"]]
    for rel, h in fz["sha256"].items():
        if not (ROOT / rel).exists():
            problems.append("missing %s" % rel)
        elif digest(rel) != h:
            problems.append("changed %s" % rel)
    return problems


def parameters(sample):
    sys.path.insert(0, str(HERE))
    import analyze_fullwiki as AF
    import fullwiki_data as D
    RF, Q = AF.RF, AF.Q
    c = sample["counts"]
    n = c["confirm"]
    return {
        "source": sample["source"],
        "seeds": {"sample_draw": D.SEED, "rankgpt_o1_shuffle": Q.SEED, "bootstrap": 20261005},
        "sample": {"confirm": n, "smoke": c["smoke"], "eligibility": sample["eligibility"],
                   "excluded_as_used_before": c["excluded"], "ineligible_skipped_in_draw": c["ineligible_skipped_in_draw"]},
        "subgroup": {"definition": sample["subgroup"], "sufficient": c["confirm_sufficient"],
                     "complement": c["confirm_complement"], "supporting_in_pool": c["confirm_supporting_in_pool"]},
        "budget_K": RF.K, "rankers": list(Q.RANKED), "conditions": list(RF.CONDITIONS),
        "answer_models": list(Q.ANSWER_MODELS), "rank_model": Q.RANK_MODEL,
        "rank_orders": {"o0": "file order, used for answering", "o1": "seeded shuffle, stability only"},
        "lanes_per_model": RF.LANES,
        "requests": {"ranking": 2 * n, "answer": len(RF.CONDITIONS) * len(Q.ANSWER_MODELS) * n,
                     "total": (2 + len(RF.CONDITIONS) * len(Q.ANSWER_MODELS)) * n, "per_smoke_question": 26},
        "families": {"primary": "15 contrasts, all questions, level 1 - 0.05/15",
                     "secondary": "30 contrasts (15 sufficient + 15 complement), level 1 - 0.05/30",
                     "evidence_criterion": "5 support-recall contrasts, all questions, level 1 - 0.05/5",
                     "worst_case": "primary family, missing RankGPT answer F1 0, missing comparator answer F1 1"},
        "bootstrap": {"resamples": 4000, "seed": 20261005, "method": "analyze_qa.boot_mean (paired, percentile)"},
        "majority_threshold": AF.MAJORITY,
        "disk_guard_MB": {"refuse_live_start_below": RF.MIN_FREE_START // RF.MB, "stop_lanes_below": RF.MIN_FREE_RUN // RF.MB},
    }


def freeze():
    if FREEZE.exists():
        raise SystemExit("already frozen at %s; a freeze is never rewritten" %
                         json.loads(FREEZE.read_text(encoding="utf-8"))["frozen_at_utc"])
    if CONFIRM_RECORDS.exists() and CONFIRM_RECORDS.stat().st_size > 0:
        raise SystemExit("confirmatory records exist: a freeze after data collection is refused")
    missing = [f for f in FILES if not (ROOT / f).exists()]
    if missing:
        raise SystemExit("cannot freeze, missing: " + ", ".join(missing))
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or None
    except OSError:
        commit = None
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    fz = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "harness_commit": commit,
          "note": "SHA-256 of the files as they are on disk; package 3's files are not committed at freeze time",
          "parameters": parameters(sample),
          "sample": {"confirm": sample["confirm"], "smoke": sample["smoke"]},
          "sha256": {f: digest(f) for f in FILES}}
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    with open(FREEZE, "w", encoding="utf-8", newline="\n") as fh:     # LF: the bytes Git stores (eol=lf)
        fh.write(json.dumps(fz, indent=1) + "\n")
    print("frozen at %s: %d files; FREEZE_fullwiki.json SHA-256 %s" % (
        fz["frozen_at_utc"], len(FILES), digest(FREEZE.relative_to(ROOT).as_posix())))


def main():
    if "--verify" in sys.argv:
        problems = check()
        if problems:
            print("freeze NOT verified: " + "; ".join(problems))
            return 1
        fz = json.loads(FREEZE.read_text(encoding="utf-8"))
        print("freeze %s: verified, nothing changed (%d files; FREEZE_fullwiki.json SHA-256 %s)" % (
            fz["frozen_at_utc"], len(fz["sha256"]), digest(FREEZE.relative_to(ROOT).as_posix())))
        return 0
    freeze()
    return 0


if __name__ == "__main__":
    sys.exit(main())
