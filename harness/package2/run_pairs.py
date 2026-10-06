r"""Pilot runner for the independent-pair experiment and the original-task controls.

Cells
  pairs     cache, inventory, audit: each pair's A-decisive and B-decisive task under the arms
            none, A, B, AB (A then B) and BA (B then A);
  controls  the original ledger pair's two API tasks under W1, W1plus, W1plus_rev (order) and
            W1pad (character-matched padding), for the multi-model extension of the Haiku controls.

Design: randomized blocks. A block is one request per arm of one task for one model, in random
order; blocks are interleaved at random per model and split over two concurrent lanes; the six
models run in parallel. Requests are built exactly as the paper's harness builds them (source text,
blank line, task prompt, the 'raw Python only' suffix, whitespace collapsed) and sent with the
replication transport (same endpoints and keys: BW_ENDPOINT_*/BW_KEY_* per model; keys are never
printed or stored). Records: issued -> receipt (raw reply and response envelope, before grading)
-> grade. A request issued without a receipt (run stopped in flight) is never resent.

This is a PILOT: development data for checking that the experiment works and measures what it
should. It is not the confirmatory run.

  python harness/package2/run_pairs.py --mock --n 2
  python harness/package2/run_pairs.py --n 5 --out results/package2/pilot_pairs
  python harness/package2/run_pairs.py --summary results/package2/pilot_pairs
"""
import argparse
import hashlib
import io
import json
import os
import random
import shutil
import sys
import tempfile
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
import measure_blackwell as mb  # noqa: E402
import transport  # noqa: E402

SUFFIX = " Return ONLY the raw Python file content, no markdown fences, no prose."
DESIGN = json.load(open(HERE.parent / "replication" / "design.json", encoding="utf-8"))
MODELS = {m["label"]: m for m in DESIGN["models"]}
CONTROL_TASKS = ("api_post_ok", "api_argorder")
CONTROL_ARMS = ("W1", "W1plus", "W1plus_rev", "W1pad")
# Hardened checks for the two ledger tasks (exact types; primary in package 2); the published
# checks are kept as recorded.
LEDGER_HARD = {
    "api_post_ok": (mb._LEDGER_STUB + "from solution import record\n"
                    "eid=record('cash',500,'lunch')\n"
                    "assert type(eid) is int and eid>=1, 'bad id'\n"
                    "c=led._CALLS[-1]\n"
                    "assert [type(x) for x in c]==[str,int,str] and c==('cash',500,'lunch'), 'wrong call'\n"),
    "api_argorder": (mb._LEDGER_STUB + "from solution import transfer\n"
                     "eid=transfer('ar',1230,'rebalance')\n"
                     "assert type(eid) is int and eid>=1, 'bad id'\n"
                     "c=led._CALLS[-1]\n"
                     "assert [type(x) for x in c]==[str,int,str] and c==('ar',1230,'rebalance'), 'wrong call'\n"),
}


def cells(pairs=("cache", "inventory", "audit"), controls=True):
    out = []
    for pid in pairs:
        for t in P.PAIRS[pid]["tasks"]:
            out.append({"group": pid, "task": t["id"], "arms": list(P.ARMS)})
    if controls:
        for tid in CONTROL_TASKS:
            out.append({"group": "ledger_controls", "task": tid, "arms": list(CONTROL_ARMS)})
    return out


def request_text(group, task_id, arm):
    """The request, the as-designed (published) check and the hardened check."""
    if group == "ledger_controls":
        task = next(t for t in mb.TASKS if t["id"] == task_id)
        ctx, prompt, verify, hard = mb.ARMS[arm], task["prompt"], task["verify"], LEDGER_HARD[task_id]
    else:
        task = next(t for t in P.PAIRS[group]["tasks"] if t["id"] == task_id)
        ctx, prompt = P.context(group, arm), task["prompt"]
        verify, hard = P.verifier(group, task), P.verifier_hardened(group, task)
    text = ((ctx + "\n\n") if ctx else "") + prompt
    return " ".join((text + SUFFIX).split()), (verify, hard)


def schedule(models, n, seed, pairs, controls, lanes=2):
    rng = random.Random(seed)
    rows = []
    for m in models:
        blocks = []
        for c in cells(pairs, controls):
            for b in range(n):
                arms = c["arms"][:]
                rng.shuffle(arms)
                blocks.append((c, b, arms))
        rng.shuffle(blocks)
        for pos, (c, b, arms) in enumerate(blocks):
            for j, arm in enumerate(arms):
                rows.append({"id": "%s|%s|%s|%03d|%s" % (m, c["group"], c["task"], b, arm),
                             "model": m, "group": c["group"], "task": c["task"], "block": b,
                             "arm": arm, "block_pos": pos, "in_block": j, "lane": pos % lanes})
    return rows


# ---- mock replies: a passing program when the decisive source is present, a wrong one otherwise --
def _mock_reply(row):
    g, t, arm = row["group"], row["task"], row["arm"]
    if g == "ledger_controls":
        good = {"api_post_ok": "import ledger\ndef record(acct, cents, note):\n    return ledger.post(acct, cents, memo=note)\n",
                "api_argorder": "import ledger\ndef transfer(acct, cents, reason):\n    return ledger.post(acct, cents, memo=reason)\n"}[t]
        return good if arm in ("W1", "W1pad") else "def broken():\n    pass\n"
    task = next(x for x in P.PAIRS[g]["tasks"] if x["id"] == t)
    present = (task["decisive"] in arm) if arm != "none" else False
    if not present:
        return "def broken():\n    pass\n"
    if g == "cache":
        return {"cache_put_ok": "import cache\ndef store(k, v, secs):\n    return cache.put(k, v, ttl=secs)\n",
                "key_norm": ("import re\ndef make_key(label):\n    s=re.sub(r'[^0-9a-z]+','_',label.lower()).strip('_')\n"
                             "    return 'kx7-'+s\n")}[t]
    state = P.PAIRS[g]["A_real"] if task["decisive"] == "A" else P.PAIRS[g]["B_real"]
    return task["reference"](state)


def _records(out_dir):
    st = {"issued": {}, "receipt": {}, "grade": {}}
    f = out_dir / "records.jsonl"
    if f.exists():
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue                          # a truncated last line: its request is interrupted
            if r.get("type") in st:
                st[r["type"]][r["id"]] = r
    return st


def grade(code_text, verify):
    wd = Path(tempfile.mkdtemp(prefix="p2_"))
    try:
        (wd / "solution.py").write_text(mb._extract_code(code_text or ""), encoding="utf-8")
        return mb.verify_in(wd, verify)
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def run(out_dir, n, models, seed=20261005, pairs=("cache", "inventory", "audit"), controls=True,
        mock=False, lanes=2, max_requests=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = schedule(models, n, seed, pairs, controls, lanes)
    sched_path = out_dir / "schedule.jsonl"
    if not sched_path.exists():
        with open(sched_path, "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
    st = _records(out_dir)
    lock = threading.Lock()
    fh = open(out_dir / "records.jsonl", "a", encoding="utf-8", newline="\n")
    budget = {"left": max_requests if max_requests is not None else float("inf")}

    def write(rec):
        with lock:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def endpoint(m):
        spec = MODELS[m]
        return spec["id"], os.environ.get(spec["endpoint_env"]), os.environ.get(spec["key_env"])

    if not mock:
        missing = [m for m in models if not all(endpoint(m)[1:])]
        if missing:
            raise SystemExit("no endpoint or key for: %s (set %s)" % (", ".join(missing), ", ".join(
                "%s/%s" % (MODELS[m]["endpoint_env"], MODELS[m]["key_env"]) for m in missing)))

    def worker(m, lane):
        mid, ep, key = endpoint(m)
        fails = 0
        for r in rows:
            if r["model"] != m or r["lane"] != lane or r["id"] in st["issued"]:
                continue
            with lock:
                if budget["left"] <= 0:
                    return
                budget["left"] -= 1
            prompt, verify = request_text(r["group"], r["task"], r["arm"])
            write({"type": "issued", "id": r["id"], "utc": transport.utc_now()})
            if mock:
                text = _mock_reply(r)
                resp = {"text": text, "returned_model": mid, "response_id": "mock", "usage": {},
                        "stop_reason": "mock", "response": None, "transport_failed": False,
                        "attempts": [{"attempt": 1, "start_utc": transport.utc_now(),
                                      "end_utc": transport.utc_now(), "http_status": 200, "error": None}]}
            else:
                resp = transport.post(prompt, mid, ep, key)
            write({"type": "receipt", "id": r["id"], "model": m, "group": r["group"], "task": r["task"],
                   "arm": r["arm"], "lane": lane, "requested_model": mid,
                   "returned_model": resp.get("returned_model"), "response_id": resp.get("response_id"),
                   "usage": resp.get("usage"), "stop_reason": resp.get("stop_reason"),
                   "attempts": resp.get("attempts"), "transport_failed": resp.get("transport_failed"),
                   "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                   "raw_text": resp.get("text"), "response": resp.get("response")})
            if resp.get("transport_failed"):
                fails += 1
                if fails >= 3:
                    write({"type": "halt", "id": "%s|lane%d" % (m, lane), "model": m,
                           "reason": "three consecutive transport failures"})
                    return
                continue
            fails = 0
            ok = grade(resp.get("text"), verify[0])
            hard = ok if verify[1] == verify[0] else grade(resp.get("text"), verify[1])
            write({"type": "grade", "id": r["id"], "pass": bool(ok), "pass_hardened": bool(hard)})

    threads = [threading.Thread(target=worker, args=(m, lane)) for m in models for lane in range(lanes)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    fh.close()
    return summary(out_dir)


def summary(out_dir):
    st = _records(out_dir)
    k, n = defaultdict(int), defaultdict(int)
    for i, g in st["grade"].items():
        r = st["receipt"][i]
        key = (r["model"], r["group"], r["task"], r["arm"])
        n[key] += 1
        k[key] += bool(g.get("pass_hardened", g["pass"]))
    issued, rec = len(st["issued"]), len(st["receipt"])
    failed = sum(1 for r in st["receipt"].values() if r.get("transport_failed"))
    lines = ["issued %d, received %d (transport failures %d), graded %d, issued without receipt %d" % (
        issued, rec, failed, len(st["grade"]), sum(1 for i in st["issued"] if i not in st["receipt"]))]
    models = sorted({key[0] for key in n})
    for (g, t) in sorted({(key[1], key[2]) for key in n}):
        arms = list(P.ARMS) if g != "ledger_controls" else list(CONTROL_ARMS)
        lines.append("")
        lines.append("%-36s" % ("%s / %s" % (g, t)) + "".join("%12s" % a for a in arms))
        for m in models:
            lines.append("  %-34s" % m + "".join(
                "%12s" % ("%d/%d" % (k[(m, g, t, a)], n[(m, g, t, a)]) if n[(m, g, t, a)] else "-") for a in arms))
    text = "\n".join(lines)
    (out_dir / "summary.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5, help="blocks per task, arm set and model")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--pairs", default="cache,inventory,audit")
    ap.add_argument("--no-controls", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--seed", type=int, default=20261005)
    ap.add_argument("--max-requests", type=int, default=None)
    ap.add_argument("--lanes", type=int, default=2, help="concurrent requests per model")
    ap.add_argument("--summary", default=None, help="only print the summary of a record directory")
    a = ap.parse_args()
    if a.summary:
        summary(Path(a.summary))
        return
    out = Path(a.out) if a.out else ROOT / "results" / "package2" / ("pilot_pairs_mock" if a.mock else "pilot_pairs")
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    unknown = [m for m in models if m not in MODELS]
    if unknown:
        raise SystemExit("unknown model label(s): %s; known: %s" % (unknown, ", ".join(MODELS)))
    run(out, a.n, models, a.seed, tuple(a.pairs.split(",")), not a.no_controls, a.mock,
        lanes=a.lanes, max_requests=a.max_requests)


if __name__ == "__main__":
    main()
