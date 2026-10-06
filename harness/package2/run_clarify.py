r"""Runner for the clarified-contract experiment (PROTOCOL_CLARIFY.md).

The four contract tasks on which superset harm was found -- api_post_ok and api_argorder (ledger:
W1 contract, W2 encoding), cache_put_ok (cache pair) and inv_book (inventory pair) -- each under
four arms:
  A    the contract as originally run;
  AB   the superset as originally run (ledger: W1plus = W2 then W1; cache and inventory: A then B);
  Ac   the contract with one sentence fixing the boundary: the argument is passed unchanged and the
       API does any transformation itself (CLARIFY below; the same sentence in every arm that has it);
  AcB  the clarified contract with the other source, in the superset's order.
Randomized blocks (one request per arm of one task, random order), blocks interleaved per model.
The schedule is written once (operating-system entropy) and, for the confirmatory directory,
hashed by freeze_clarify.py before the first request. Checks: the hardened ledger and cache checks
of package 2 and the strict inventory check, exactly as in run_pairs.py.

  python harness/package2/run_clarify.py --mock --n 3 --lanes 2 --out results/package2/_mock_clarify
  python harness/package2/run_clarify.py --n 1 --lanes 4 --out results/package2/smoke_clarify
  python harness/package2/run_clarify.py --schedule-only --n 40
  python harness/package2/run_clarify.py --n 40 --lanes 4
  python harness/package2/run_clarify.py --summary results/package2/confirm_clarify
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
import measure_blackwell as mb  # noqa: E402
import pairs as P  # noqa: E402
import run_pairs as RP  # noqa: E402   (MODELS, SUFFIX, LEDGER_HARD, grade, _records; nothing is changed)
import transport  # noqa: E402

MODELS = RP.MODELS
N_BLOCKS = 40
LANES = 4
DEFAULT_OUT = ROOT / "results" / "package2" / "confirm_clarify"
MOCK_OUT = ROOT / "results" / "package2" / "_mock_clarify"
TASKS = (("ledger", "api_post_ok"), ("ledger", "api_argorder"), ("cache", "cache_put_ok"), ("inventory", "inv_book"))
ARMS = ("A", "AB", "Ac", "AcB")
CLARIFY = {
    "ledger": (" The `amount` argument is the integer number of cents exactly as the caller supplies it "
               "and is passed to post(...) unchanged: post(...) does any serialization itself, so no "
               "amount encoding is applied before the call."),
    "cache": (" The `key` argument is the caller's key exactly as supplied and is passed to put(...) "
              "unchanged: put(...) does any key normalization itself, so no normalization is applied "
              "before the call."),
    "inventory": (" The `sku` argument is the item code exactly as the caller supplies it and is passed "
                  "to reserve(...) unchanged: reserve(...) does any SKU conversion itself, so no code "
                  "conversion is applied before the call."),
}


def texts(group):
    if group == "ledger":
        a, b = mb.ARMS["W1"], mb.ARMS["W2"]

        def sup(x):
            return b + "\n\n" + x                 # W1plus as originally run: W2 then W1
        assert sup(a) == mb.ARMS["W1plus"]
    else:
        a, b = P.texts(group)

        def sup(x):
            return x + "\n\n" + b                 # package-2 AB: A then B
        assert sup(a) == P.context(group, "AB")
    ac = a + CLARIFY[group]
    return {"A": a, "AB": sup(a), "Ac": ac, "AcB": sup(ac)}


def request(group, tid, arm):
    """(prompt, check): the prompt assembled exactly as run_pairs.request_text does."""
    ctx = texts(group)[arm]
    if group == "ledger":
        task = next(t for t in mb.TASKS if t["id"] == tid)
        check = RP.LEDGER_HARD[tid]
    else:
        task = next(t for t in P.PAIRS[group]["tasks"] if t["id"] == tid)
        check = P.verifier_hardened(group, task)
    return " ".join((ctx + "\n\n" + task["prompt"] + RP.SUFFIX).split()), check


def self_check():
    """The A and AB arms must be byte-identical to the requests of package 2."""
    for group, tid in TASKS:
        if group == "ledger":
            same = {"A": "W1", "AB": "W1plus"}
            for arm, orig in same.items():
                assert request(group, tid, arm) == RP.request_text("ledger_controls", tid, orig)[:1] + (RP.LEDGER_HARD[tid],)
        else:
            for arm in ("A", "AB"):
                p0, (v, hard) = RP.request_text(group, tid, arm)
                assert request(group, tid, arm) == (p0, hard)
        p = {arm: request(group, tid, arm)[0] for arm in ARMS}
        assert len(set(p.values())) == 4


def make_schedule(models, n, lanes=LANES):
    rng = random.SystemRandom()
    rows = []
    for m in models:
        blocks = []
        for group, tid in TASKS:
            for b in range(n):
                arms = list(ARMS)
                rng.shuffle(arms)
                blocks.append((group, tid, b, arms))
        rng.shuffle(blocks)
        for pos, (group, tid, b, arms) in enumerate(blocks):
            for j, arm in enumerate(arms):
                rows.append({"id": "%s|%s|%s|%03d|%s" % (m, group, tid, b, arm), "model": m, "group": group,
                             "task": tid, "block": b, "arm": arm, "block_pos": pos, "in_block": j,
                             "lane": pos % lanes})
    return rows


def load_schedule(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def write_schedule(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


_MOCK = {
    "api_post_ok": ("import ledger\ndef record(acct, cents, note):\n    return ledger.post(acct, cents, memo=note)\n",
                    "import ledger\ndef record(acct, cents, note):\n    return ledger.post(acct, str(cents), memo=note)\n"),
    "api_argorder": ("import ledger\ndef transfer(acct, cents, reason):\n    return ledger.post(acct, cents, memo=reason)\n",
                     "import ledger\ndef transfer(acct, cents, reason):\n    return ledger.post(acct, str(cents), memo=reason)\n"),
    "cache_put_ok": ("import cache\ndef store(k, v, secs):\n    return cache.put(k, v, ttl=secs)\n",
                     "import cache\ndef store(k, v, secs):\n    return cache.put('kx7-' + k, v, ttl=secs)\n"),
    "inv_book": (P.inv_book_reference(P.INV_A_REAL),
                 P.inv_book_reference(P.INV_A_REAL).replace("reserve(n, code,", "reserve(n, 'iv9.' + code,")),
}


def _mock_response(row, mid):
    good, bad = _MOCK[row["task"]]
    text = bad if row["arm"] == "AB" else good
    return {"text": text, "returned_model": mid, "response_id": "mock", "usage": {}, "stop_reason": "mock",
            "response": None, "transport_failed": False,
            "attempts": [{"attempt": 1, "start_utc": transport.utc_now(), "end_utc": transport.utc_now(),
                          "http_status": 200, "error": None}]}


def freeze_guard(out_dir):
    if Path(out_dir).resolve() != DEFAULT_OUT.resolve():
        return
    import freeze_clarify as FZ
    problems = FZ.check()
    if problems:
        raise SystemExit("confirmatory run refused: " + "; ".join(problems))


def run(out_dir, n, models, mock=False, lanes=LANES, max_requests=None):
    self_check()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sched_path = out_dir / "schedule.jsonl"
    if sched_path.exists():
        rows = load_schedule(sched_path)
    else:
        if out_dir.resolve() == DEFAULT_OUT.resolve():
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
            write({"type": "grade", "id": i, "pass": bool(RP.grade(rc.get("raw_text"), request(r["group"], r["task"], r["arm"])[1]))})

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
            text, check = request(r["group"], r["task"], r["arm"])
            write({"type": "issued", "id": r["id"], "utc": transport.utc_now()})
            resp = _mock_response(r, mid) if mock else transport.post(text, mid, ep, key)
            write({"type": "receipt", "id": r["id"], "model": m, "group": r["group"], "task": r["task"],
                   "arm": r["arm"], "block": r["block"], "lane": lane, "requested_model": mid,
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
            write({"type": "grade", "id": r["id"], "pass": bool(RP.grade(resp.get("text"), check))})

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
    agg = defaultdict(lambda: [0, 0])
    for line in open(out_dir / "records.jsonl", encoding="utf-8"):
        try:
            g = json.loads(line)
        except ValueError:
            continue
        if g.get("type") == "grade" and g["id"] in rows:
            r = rows[g["id"]]
            agg[(r["model"], r["task"], r["arm"])][0] += bool(g["pass"])
            agg[(r["model"], r["task"], r["arm"])][1] += 1
    fails = sum(1 for rc in st["receipt"].values() if rc.get("transport_failed"))
    lines = ["scheduled %d, issued %d, received %d, transport failures %d" % (
        len(rows), len(st["issued"]), len(st["receipt"]), fails)]
    for (m, t, arm), (k, n) in sorted(agg.items()):
        lines.append("  %-16s %-13s %-4s %3d/%3d" % (m, t, arm, k, n))
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
        self_check()
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
