r"""Freeze the replication before any collection, and verify the freeze afterwards.

freeze() requires concrete window boundaries (ISO 8601 with a UTC offset, increasing and
non-overlapping), a schedule that fits the call budget with the declared retry headroom, the
interruption rules, committed code, no earlier freeze and no collected records. It sets the design's
status, freezing time and harness commit, generates the frozen schedule, and writes FREEZE.json with
the SHA-256 of the design, of the schedule and of every code file the collection and the analysis run.

verify() re-hashes all of it and returns the list of problems; an empty list means the freeze holds.
run_replication.py refuses a live window, and analyze.py refuses a final status, unless it is empty.
Code identity is checked by content hash, so later commits (of records, say) do not break it.

Usage:  python harness/replication/freeze.py          (after fixing blocks_per_window and the windows)
"""
import hashlib
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
CODE = ["harness/measure_blackwell.py", "harness/replication/transport.py",
        "harness/replication/grading.py", "harness/replication/records.py",
        "harness/replication/run_replication.py", "harness/replication/make_schedule.py",
        "harness/replication/stats.py", "harness/replication/analyze.py",
        "harness/replication/freeze.py"]


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def n_requests(design):
    return (len(design["windows"]) * len(design["models"]) * design["blocks_per_window"] *
            sum(len(v) for v in design["cells"].values()))


def parse_time(s):
    t = datetime.fromisoformat(s)
    if t.tzinfo is None:
        raise ValueError("no UTC offset in %r" % s)
    return t


def check_design(design):
    """Problems that must be fixed before freezing (and that verify() re-checks)."""
    problems = []
    prev_end = None
    for w in design["windows"]:
        try:
            start, end = parse_time(w.get("start") or ""), parse_time(w.get("end") or "")
        except (TypeError, ValueError) as e:
            problems.append("window %s: boundaries missing or invalid (%s)" % (w["id"], e))
            continue
        if not start < end:
            problems.append("window %s: start is not before end" % w["id"])
        if prev_end is not None and start < prev_end:
            problems.append("window %s: starts before the previous window ends" % w["id"])
        prev_end = end
    b = design.get("budget", {})
    cap, head = b.get("max_api_calls"), b.get("min_retry_headroom_fraction", 0.0)
    if not cap:
        problems.append("no call budget (budget.max_api_calls)")
    elif n_requests(design) > cap * (1 - head):
        problems.append("schedule of %d requests leaves less than %.0f%% of the %d-call budget for "
                        "retries" % (n_requests(design), 100 * head, cap))
    lanes = design.get("max_in_flight_per_model", 1)
    if not isinstance(lanes, int) or lanes < 1:
        problems.append("max_in_flight_per_model must be a positive integer")
    if not design.get("interruption_rules"):
        problems.append("no interruption rules")
    return problems


def _rel(p, root):
    try:
        return os.path.relpath(p, root).replace(os.sep, "/")
    except ValueError:            # another drive
        return os.path.abspath(p)


def freeze(design_path=os.path.join(HERE, "design.json"),
           out_dir=os.path.join(ROOT, "results", "replication"), root=ROOT, force=False,
           allow_dirty=False):
    import make_schedule
    import records
    fz = os.path.join(out_dir, "FREEZE.json")
    if os.path.exists(fz) and not force:
        sys.exit("already frozen (%s); a change after freezing is a deviation, not a re-freeze" % fz)
    st = records.read_dir(os.path.join(out_dir, "records"))
    if st["issued"] or st["receipts"]:
        sys.exit("records already exist in %s: collection has started" % os.path.join(out_dir, "records"))
    design = json.load(open(design_path, encoding="utf-8"))
    problems = check_design(design)
    if not allow_dirty:
        dirty = subprocess.run(["git", "-C", root, "status", "--porcelain", "--"] + CODE,
                               capture_output=True, text=True).stdout.strip()
        if dirty:
            problems.append("code not committed:\n    " + dirty.replace("\n", "\n    "))
    if problems:
        sys.exit("cannot freeze:\n  " + "\n  ".join(problems))
    commit = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    design["status"] = "frozen"
    design["frozen_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    design["harness_commit"] = commit
    json.dump(design, open(design_path, "w", encoding="utf-8", newline="\n"), indent=2)
    sched, man = make_schedule.main(design_path=design_path, out_dir=out_dir)
    record = {"frozen_at_utc": design["frozen_at_utc"], "harness_commit": commit,
              "design_file": _rel(design_path, root), "design_sha256": sha256_file(design_path),
              "schedule_file": os.path.basename(sched), "schedule_sha256": man["schedule_sha256"],
              "n_requests": man["n_requests"], "call_budget": design["budget"]["max_api_calls"],
              "code_sha256": {p: sha256_file(os.path.join(root, p)) for p in CODE}}
    json.dump(record, open(fz, "w", encoding="utf-8", newline="\n"), indent=1)
    print("frozen: %d requests; design %s; schedule %s" % (man["n_requests"],
          record["design_sha256"][:12], record["schedule_sha256"][:12]))
    return record


def verify(design_path=os.path.join(HERE, "design.json"),
           out_dir=os.path.join(ROOT, "results", "replication"), root=ROOT):
    fz = os.path.join(out_dir, "FREEZE.json")
    if not os.path.exists(fz):
        return ["no FREEZE.json: the design has not been frozen"]
    rec = json.load(open(fz, encoding="utf-8"))
    need = ("design_sha256", "schedule_file", "schedule_sha256", "code_sha256", "harness_commit",
            "frozen_at_utc")
    missing = [k for k in need if not rec.get(k)]
    if missing:
        return ["FREEZE.json lacks %s" % ", ".join(missing)]
    design = json.load(open(design_path, encoding="utf-8"))
    problems = []
    if design.get("status") != "frozen" or not design.get("frozen_at_utc") or not design.get("harness_commit"):
        problems.append("design.json lacks the freeze metadata (status, frozen_at_utc, harness_commit)")
    if sha256_file(design_path) != rec["design_sha256"]:
        problems.append("design.json changed after freezing")
    sched = os.path.join(out_dir, rec["schedule_file"])
    if not os.path.exists(sched) or sha256_file(sched) != rec["schedule_sha256"]:
        problems.append("the schedule changed after freezing")
    missing_code = [p for p in CODE if p not in rec["code_sha256"]]
    if missing_code:
        problems.append("FREEZE.json does not hash %s" % ", ".join(missing_code))
    for p, h in rec["code_sha256"].items():
        q = os.path.join(root, p)
        if not os.path.exists(q) or sha256_file(q) != h:
            problems.append("%s changed after freezing" % p)
    problems += check_design(design)
    return problems


if __name__ == "__main__":
    freeze(force="--force" in sys.argv)
