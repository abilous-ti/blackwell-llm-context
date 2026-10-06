r"""Runner for the declarative label experiment (PROTOCOL_LABELS.md).

Every block draws a hidden state (A-state and B-state independently, uniformly, with replacement)
with operating-system entropy; the three arms of the block (none, A, B) share it. The schedule,
states included, is written once before any request and is never regenerated: a resumed run reads
it back. For the confirmatory directory it is created with --schedule-only and hashed by
freeze_labels.py before the first request; a live run there is refused unless the freeze verifies.

  python harness/package2/run_labels.py --mock --n 3 --lanes 2 --out results/package2/_mock_labels
  python harness/package2/run_labels.py --n 1 --lanes 4 --out results/package2/smoke_labels
  python harness/package2/run_labels.py --schedule-only --n 40
  python harness/package2/run_labels.py --n 40 --lanes 4
  python harness/package2/run_labels.py --summary results/package2/confirm_labels
"""
import argparse
import hashlib
import io
import json
import os
import random
import sys
import threading
from collections import defaultdict
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "replication"))
import pairs as P  # noqa: E402
import labels as L  # noqa: E402
import run_pairs as RP  # noqa: E402   (MODELS, _records; nothing is changed)
import transport  # noqa: E402

MODELS = RP.MODELS
N_BLOCKS = 40
LANES = 4
DEFAULT_OUT = ROOT / "results" / "package2" / "confirm_labels"
MOCK_OUT = ROOT / "results" / "package2" / "_mock_labels"


def make_schedule(models, n, lanes=LANES):
    rng = random.SystemRandom()
    rows = []
    for m in models:
        blocks = []
        for pid in L.PAIR_IDS:
            a_all, b_all = P.states(P.PAIRS[pid]["A_space"]), P.states(P.PAIRS[pid]["B_space"])
            for x in ("A", "B"):
                for b in range(n):
                    a_state, b_state = rng.choice(a_all), rng.choice(b_all)
                    arms = list(L.ARMS)
                    rng.shuffle(arms)
                    blocks.append((pid, x, b, a_state, b_state, arms))
        rng.shuffle(blocks)
        for pos, (pid, x, b, a_state, b_state, arms) in enumerate(blocks):
            tid = L.TASKS[(pid, x)]["id"]
            for j, arm in enumerate(arms):
                rows.append({"id": "%s|%s|%s|%03d|%s" % (m, pid, tid, b, arm), "model": m, "group": pid,
                             "task": tid, "source": x, "block": b, "arm": arm,
                             "a_state": a_state, "b_state": b_state,
                             "a_key": P.key_of(a_state), "b_key": P.key_of(b_state),
                             "truth": L.truth(pid, x, a_state, b_state),
                             "block_pos": pos, "in_block": j, "lane": pos % lanes})
    return rows


def load_schedule(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def write_schedule(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def request(row):
    return L.prompt(row["group"], row["source"], row["arm"], row["a_state"], row["b_state"])


def _mock_response(row, mid):
    rng = random.Random(row["id"])
    n = len(L.menu_states(row["group"], row["source"]))
    k = row["truth"] if row["arm"] == row["source"] else rng.randint(1, n)
    return {"text": "Mock reasoning.\nAnswer: %d" % k, "returned_model": mid, "response_id": "mock",
            "usage": {}, "stop_reason": "mock", "response": None, "transport_failed": False,
            "attempts": [{"attempt": 1, "start_utc": transport.utc_now(), "end_utc": transport.utc_now(),
                          "http_status": 200, "error": None}]}


def freeze_guard(out_dir):
    if Path(out_dir).resolve() != DEFAULT_OUT.resolve():
        return
    import freeze_labels as FZ
    problems = FZ.check()
    if problems:
        raise SystemExit("confirmatory run refused: " + "; ".join(problems))


def run(out_dir, n, models, mock=False, lanes=LANES, max_requests=None):
    L.certify()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sched_path = out_dir / "schedule.jsonl"
    if sched_path.exists():
        rows = load_schedule(sched_path)
        bad = [r["id"] for r in rows[:50] if r["truth"] != L.truth(r["group"], r["source"], r["a_state"], r["b_state"])]
        if bad:
            raise SystemExit("schedule inconsistent with labels.py: %s" % bad[:3])
    else:
        if Path(out_dir).resolve() == DEFAULT_OUT.resolve():
            raise SystemExit("create the confirmatory schedule with --schedule-only and freeze it first")
        rows = make_schedule(models, n, lanes)
        write_schedule(sched_path, rows)
    rows = [r for r in rows if r["model"] in models]
    st = RP._records(out_dir)
    lock = threading.Lock()
    rpath = out_dir / "records.jsonl"
    torn = False
    if rpath.exists() and rpath.stat().st_size > 0:
        with open(rpath, "rb") as fb:
            fb.seek(-1, os.SEEK_END)
            torn = fb.read(1) != b"\n"
    fh = open(rpath, "a", encoding="utf-8", newline="\n")
    if torn:
        fh.write("\n")
        fh.flush()
    budget = {"left": max_requests if max_requests is not None else float("inf")}

    def write(rec):
        with lock:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    if not mock:
        missing = [m for m in models if not (os.environ.get(MODELS[m]["endpoint_env"])
                                             and os.environ.get(MODELS[m]["key_env"]))]
        if missing:
            raise SystemExit("no endpoint or key for: %s (set %s)" % (", ".join(missing), ", ".join(
                "%s/%s" % (MODELS[m]["endpoint_env"], MODELS[m]["key_env"]) for m in missing)))

    by_id = {r["id"]: r for r in rows}
    for i, rc in st["receipt"].items():         # a saved reply is graded on resumption, never re-requested
        if i in by_id and i not in st["grade"] and not rc.get("transport_failed"):
            r = by_id[i]
            write(dict(L.grade(rc.get("raw_text"), r["group"], r["source"], r["a_state"], r["b_state"]),
                       type="grade", id=i))

    def worker(m, lane):
        mid = MODELS[m]["id"]
        ep = key = None
        if not mock:
            ep, key = os.environ.get(MODELS[m]["endpoint_env"]), os.environ.get(MODELS[m]["key_env"])
        fails = 0
        for r in rows:
            if r["model"] != m or r["lane"] != lane or r["id"] in st["issued"]:
                continue
            with lock:
                if budget["left"] <= 0:
                    return
                budget["left"] -= 1
            text = request(r)
            write({"type": "issued", "id": r["id"], "utc": transport.utc_now()})
            resp = _mock_response(r, mid) if mock else transport.post(text, mid, ep, key)
            write({"type": "receipt", "id": r["id"], "model": m, "group": r["group"], "task": r["task"],
                   "source": r["source"], "arm": r["arm"], "block": r["block"], "a_key": r["a_key"],
                   "b_key": r["b_key"], "lane": lane, "requested_model": mid,
                   "returned_model": resp.get("returned_model"), "response_id": resp.get("response_id"),
                   "usage": resp.get("usage"), "stop_reason": resp.get("stop_reason"),
                   "attempts": resp.get("attempts"), "transport_failed": resp.get("transport_failed"),
                   "prompt_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                   "raw_text": resp.get("text"), "response": resp.get("response")})
            if resp.get("transport_failed"):
                fails += 1
                if fails >= 3:
                    write({"type": "halt", "id": "%s|lane%d" % (m, lane), "model": m,
                           "reason": "three consecutive transport failures"})
                    return
                continue
            fails = 0
            write(dict(L.grade(resp.get("text"), r["group"], r["source"], r["a_state"], r["b_state"]),
                       type="grade", id=r["id"]))

    threads = [threading.Thread(target=worker, args=(m, lane)) for m in models for lane in range(lanes)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    fh.close()
    return summary(out_dir)


def summary(out_dir):
    out_dir = Path(out_dir)
    rows = {r["id"]: r for r in load_schedule(out_dir / "schedule.jsonl")}
    st = RP._records(out_dir)
    grades = {}
    for line in open(out_dir / "records.jsonl", encoding="utf-8"):
        try:
            g = json.loads(line)
        except ValueError:
            continue
        if g.get("type") == "grade":
            grades[g["id"]] = g
    agg = defaultdict(lambda: [0, 0])
    for i, g in grades.items():
        r = rows[i]
        agg[(r["model"], r["task"], r["arm"])][0] += bool(g["correct"])
        agg[(r["model"], r["task"], r["arm"])][1] += 1
    fails = sum(1 for rc in st["receipt"].values() if rc.get("transport_failed"))
    lines = ["scheduled %d, issued %d, received %d, graded %d, transport failures %d" % (
        len(rows), len(st["issued"]), len(st["receipt"]), len(grades), fails)]
    for (m, t, arm), (k, n) in sorted(agg.items()):
        lines.append("  %-16s %-18s %-4s %3d/%3d" % (m, t, arm, k, n))
    text = "\n".join(lines)
    print(text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N_BLOCKS)
    ap.add_argument("--lanes", type=int, default=LANES)
    ap.add_argument("--out", default=None)
    ap.add_argument("--models", nargs="*", default=list(MODELS))
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--max-requests", type=int, default=None)
    ap.add_argument("--schedule-only", action="store_true")
    ap.add_argument("--summary", default=None)
    a = ap.parse_args()
    if a.summary:
        summary(a.summary)
        return
    unknown = [m for m in a.models if m not in MODELS]
    if unknown:
        raise SystemExit("unknown models: %s" % unknown)
    out = Path(a.out) if a.out else (MOCK_OUT if a.mock else DEFAULT_OUT)
    if a.schedule_only:
        L.certify()
        out.mkdir(parents=True, exist_ok=True)
        path = out / "schedule.jsonl"
        if path.exists():
            raise SystemExit("schedule exists: %s (never regenerated)" % path)
        rows = make_schedule(a.models, a.n, a.lanes)
        write_schedule(path, rows)
        print("schedule written: %s (%d rows)" % (path, len(rows)))
        return
    if a.mock and out.resolve() == DEFAULT_OUT.resolve():
        raise SystemExit("mock runs may not write into the confirmatory directory")
    if not a.mock:
        freeze_guard(out)
    run(out, a.n, a.models, mock=a.mock, lanes=a.lanes, max_requests=a.max_requests)


if __name__ == "__main__":
    main()
