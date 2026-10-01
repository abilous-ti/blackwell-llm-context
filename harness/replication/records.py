r"""The replication's append-only record files: one JSON object per line, one file per window.

Record types, in the order the runner writes them:
  run_start          one per run segment of a window: commit, hashes, endpoint hosts, calls used so far;
  issued             written before the first attempt of a scheduled request;
  receipt            the response, or the exhausted transport failure, written before any grading;
  grade              extracted code and PASS under both graders;
  window_end         every scheduled request of the window was issued;
  window_closed      the window ended, or the call budget ran out, with requests left uncollected;
  window_incomplete  a worker failed; the window stays open for resumption within its time.

A crash can truncate only the last line of a file; such a line is ignored, so its request counts as
issued without a receipt. A malformed line anywhere else is an error.
"""
import json
import os

CLOSING = ("window_end", "window_closed")


def empty():
    return {"issued": {}, "receipts": {}, "grades": {}, "events": [], "truncated": []}


def read_file(path, into=None):
    st = into if into is not None else empty()
    if not os.path.exists(path):
        return st
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    last = max((i for i, l in enumerate(lines) if l.strip()), default=-1)
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            if i == last:
                st["truncated"].append(path)
                continue
            raise ValueError("%s: malformed record on line %d" % (path, i + 1))
        t = r.get("type")
        if t == "issued":
            st["issued"][r["schedule_id"]] = r
        elif t == "receipt":
            st["receipts"][r["schedule_id"]] = r
        elif t == "grade":
            st["grades"][r["schedule_id"]] = r
        else:
            st["events"].append(r)
    return st


def read_dir(d):
    st = empty()
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".jsonl"):
                read_file(os.path.join(d, f), st)
    return st


def closed_windows(st):
    return {e["window"] for e in st["events"] if e.get("type") in CLOSING}


def calls_used(st, max_attempts=3):
    """Attempts spent so far: every attempt of every receipt, and max_attempts for a request issued
    without a receipt (the run stopped in flight, so how many attempts it made is unknown)."""
    n = sum(len(r["attempts"]) for r in st["receipts"].values())
    return n + max_attempts * sum(1 for s in st["issued"] if s not in st["receipts"])
