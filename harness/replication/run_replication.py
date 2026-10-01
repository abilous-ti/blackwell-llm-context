r"""Execute one collection window of the frozen schedule and keep a complete record of every request.

Within a window each model works through its own rows in scheduled order with at most
max_in_flight_per_model requests in flight (design.json): lane j takes the blocks whose position in
the window is j modulo that number, so the requests of one block stay back to back. The models run in
parallel. Every request is a fresh, stateless, single-turn call built exactly as the published
harness builds it. Record types are described in records.py; every line is flushed and fsynced
before the next step, and a response is saved before it is graded.

Rules (the interruption rules of design.json), enforced in a live run:
  * the freeze holds: design, schedule and code hashes match FREEZE.json (freeze.verify);
  * requests are issued only between the window's start and its end, and a window is resumed only
    before its end;
  * a scheduled request is issued at most once: a saved response is graded on resumption and never
    requested again; a request issued but not saved (the run stopped in flight) is 'interrupted', one
    whose transport attempts were exhausted is 'failed', and neither is requested again;
  * one global call budget counts every attempt, retries included, across all windows; once it is
    spent no further attempt is made in any window;
  * a window whose requests were not all issued is closed with --close after its end (or once the
    budget is spent); its unissued requests are 'not collected' and never move to another window;
  * one run at a time per record directory (a lock file; after a crash, make sure no run is active,
    then delete it).

Usage:  python harness/replication/run_replication.py --window d1-am
        python harness/replication/run_replication.py --window d1-am --close   (after its end time)
        python harness/replication/run_replication.py --window d1-am --mock    (no network; tests)
"""
import argparse
import hashlib
import io
import json
import os
import platform
import random
import subprocess
import sys
import threading
from datetime import datetime, timezone
from urllib.parse import urlparse

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import measure_blackwell as mb  # noqa: E402
import freeze as frz  # noqa: E402
import grading  # noqa: E402
import records  # noqa: E402
import transport  # noqa: E402
from transport import utc_now  # noqa: E402

DESIGN = os.path.join(HERE, "design.json")
OUTDIR = os.path.join(ROOT, "results", "replication")
SUFFIX = " Return ONLY the raw Python file content, no markdown fences, no prose."


def request_text(task_id, condition):
    """The prompt exactly as harness/measure_blackwell.py::run_one sends it."""
    task = next(t for t in mb.TASKS if t["id"] == task_id)
    ctx = mb.ARMS[condition]
    prompt = ((ctx + "\n\n") if ctx else "") + task["prompt"]
    return task, " ".join((prompt + SUFFIX).split())


# ---- mock transport: canned replies through the real extraction and graders ---------------------
_PASS = {
    "api_post_ok": "import ledger\ndef record(acct, cents, note):\n    return ledger.post(acct, cents, memo=note)\n",
    "api_argorder": "import ledger\ndef transfer(acct, cents, reason):\n    return ledger.post(acct, cents, memo=reason)\n",
    "enc_amount": ("def encode_amount(dollars):\n    s = dollars.strip()\n    neg = s.startswith('-')\n"
                   "    whole, _, frac = s.lstrip('+-').partition('.')\n"
                   "    cents = int(whole or '0') * 100 + int((frac + '00')[:2])\n"
                   "    digits = str(cents)\n    check = sum(int(c) for c in digits) % 10\n"
                   "    return ('-' if neg and cents else '+') + digits + '#' + str(check)\n"),
}
_FAIL = {
    "api_post_ok": "import ledger\ndef record(acct, cents, note):\n    return ledger.post(acct, cents, note)\n",
    "api_argorder": "import ledger\ndef transfer(acct, cents, reason):\n    return ledger.post(cents, acct, memo=reason)\n",
    "enc_amount": "def encode_amount(dollars):\n    return dollars\n",
}
_MOCK_RATE = {("api_post_ok", "W1"): .95, ("api_post_ok", "W2"): .02, ("api_post_ok", "W1plus"): .05,
              ("enc_amount", "W1"): .02, ("enc_amount", "W2"): .80,
              ("api_argorder", "none"): .05, ("api_argorder", "W1"): .85, ("api_argorder", "W1plus"): .10}
MOCK_REQUESTS = []   # schedule ids the mock transport was asked for (tests look for re-requests)


def _no_response(attempts, failed, budget_stop):
    return {"text": None, "output_tokens": None, "returned_model": None, "response_id": None,
            "usage": None, "stop_reason": None, "response": None, "attempts": attempts,
            "transport_failed": failed, "budget_stop": budget_stop}


def mock_post(prompt, model, task_id, condition, rng, allow_attempt=None, sid=None):
    MOCK_REQUESTS.append(sid)
    outage = rng.random() < 0.01
    attempts = []
    for i in range(3 if outage else 1):
        if allow_attempt is not None and not allow_attempt():
            return _no_response(attempts, bool(attempts), True)
        attempts.append({"attempt": i + 1, "start_utc": utc_now(), "end_utc": utc_now(),
                         "http_status": 503 if outage else 200,
                         "error": "HTTPError: mock outage" if outage else None})
    if outage:
        return _no_response(attempts, True, False)
    ok = rng.random() < _MOCK_RATE[(task_id, condition)]
    code = (_PASS if ok else _FAIL)[task_id]
    text = ("```python\n" + code + "```") if rng.random() < 0.3 else code
    rid = "mock-%08x" % rng.getrandbits(32)
    usage = {"output_tokens": len(text) // 4}
    return {"text": text, "output_tokens": len(text) // 4, "returned_model": model, "response_id": rid,
            "usage": usage, "stop_reason": "end_turn", "attempts": attempts, "transport_failed": False,
            "budget_stop": False,
            "response": transport.envelope({"id": rid, "model": model, "usage": usage, "stop_reason": "end_turn",
                                            "content": [{"type": "text", "text": text}]}, text)}


# ---- setup ---------------------------------------------------------------------------------------
def load(design_path, sched_dir, strict):
    design = json.load(open(design_path, encoding="utf-8"))
    if strict:
        problems = frz.verify(design_path, sched_dir, ROOT)
        if problems:
            raise SystemExit("freeze check failed; refusing to run:\n  " + "\n  ".join(problems))
    tag = "" if design.get("status") == "frozen" else ".DRAFT"
    man_p = os.path.join(sched_dir, "schedule%s_manifest.json" % tag)
    if not os.path.exists(man_p):
        raise SystemExit("no schedule manifest at %s; run make_schedule.py first" % man_p)
    man = json.load(open(man_p, encoding="utf-8"))
    sched_p = os.path.join(sched_dir, man["schedule_file"])
    if hashlib.sha256(open(sched_p, "rb").read()).hexdigest() != man["schedule_sha256"]:
        raise SystemExit("schedule hash does not match its manifest: refusing to run")
    rows = [json.loads(l) for l in open(sched_p, encoding="utf-8") if l.strip()]
    return design, man, rows


def host_id(url):
    """The endpoint as recorded: the provider domain, with the resource name replaced by a short
    hash, so a change of endpoint is visible without publishing the resource name."""
    head, _, rest = urlparse(url).netloc.partition(".")
    return "%s.%s" % (hashlib.sha256(head.encode("utf-8")).hexdigest()[:10], rest)


def endpoint_for(model_cfg):
    """Endpoint and key from the model's own environment variables; there is no shared fallback."""
    return os.environ.get(model_cfg["endpoint_env"]), os.environ.get(model_cfg["key_env"])


def _repair_tail(path):
    """Cut a partial last line (a crash during a write) and return it; it is then kept as data."""
    if not os.path.exists(path):
        return None
    data = open(path, "rb").read()
    if not data or data.endswith(b"\n"):
        return None
    cut = data.rfind(b"\n") + 1
    with open(path, "r+b") as f:
        f.truncate(cut)
    return data[cut:].decode("utf-8", errors="replace")


def _acquire(out_dir):
    p = os.path.join(out_dir, ".run.lock")
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit("another run holds %s; if no run is active (after a crash), delete it" % p)
    os.write(fd, ("pid %d since %s\n" % (os.getpid(), utc_now())).encode("utf-8"))
    os.close(fd)
    return p


# ---- one window ----------------------------------------------------------------------------------
def run_window(window, mock=False, strict=None, models=None, design_path=DESIGN, sched_dir=OUTDIR,
               out_dir=None, mock_seed=0, clock=None, grade_fn=None, post_fn=None, close=False):
    """Collect (or, with close=True, close) one window. strict defaults to True for live runs.
    clock, grade_fn and post_fn(text, row, allow_attempt) can be injected by the tests."""
    strict = (not mock) if strict is None else strict
    clock = clock or (lambda: datetime.now(timezone.utc))
    grade_fn = grade_fn or grading.grade
    design, man, rows = load(design_path, sched_dir, strict)
    wcfg = next((w for w in design["windows"] if w["id"] == window), None)
    if wcfg is None:
        raise SystemExit("window %r is not in the design" % window)
    start = frz.parse_time(wcfg["start"]) if wcfg.get("start") else None
    end = frz.parse_time(wcfg["end"]) if wcfg.get("end") else None
    if strict and not (start and end):
        raise SystemExit("window %s has no start and end" % window)
    out_dir = out_dir or os.path.join(sched_dir, "records_mock" if mock else "records")
    os.makedirs(out_dir, exist_ok=True)
    lock_path = _acquire(out_dir)
    try:
        return _collect(window, wcfg, start, end, design, man, rows, mock, strict, models, design_path,
                        out_dir, mock_seed, clock, grade_fn, post_fn, close)
    finally:
        os.remove(lock_path)


def _collect(window, wcfg, start, end, design, man, rows, mock, strict, models, design_path, out_dir,
             mock_seed, clock, grade_fn, post_fn, close):
    path = os.path.join(out_dir, "%s.jsonl" % window)
    partial = _repair_tail(path)
    st = records.read_dir(out_dir)                  # every window: the global ledger and this state
    if window in records.closed_windows(st):
        raise SystemExit("window %s is already closed" % window)
    cap = design.get("budget", {}).get("max_api_calls")
    max_att = design.get("retry_policy", {}).get("max_attempts", 3)
    ledger = [records.calls_used(st, max_att)]
    lanes = max(1, int(design.get("max_in_flight_per_model", 1)))
    win_rows = [r for r in rows if r["window"] == window]
    cfg = {m["label"]: m for m in design["models"]}
    chosen = [m for m in cfg if not models or m in models]
    lock = threading.Lock()
    fh = open(path, "a", encoding="utf-8", newline="\n")

    def write(rec):
        with lock:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")   # ASCII escapes: any reply can be written
            fh.flush()
            os.fsync(fh.fileno())

    def unissued():
        return [r["schedule_id"] for r in win_rows
                if r["schedule_id"] not in st["issued"] and r["schedule_id"] not in st["receipts"]]

    def interrupted():
        return sorted(s for s, x in st["issued"].items() if x["window"] == window and s not in st["receipts"])

    def grade_and_write(rc, text):
        task = next(t for t in mb.TASKS if t["id"] == rc["task"])
        code = mb._extract_code(text or "")
        g = grade_fn(task, code)
        rec = {"type": "grade", "schedule_id": rc["schedule_id"], "window": rc["window"],
               "model": rc["model"], "task": rc["task"], "condition": rc["condition"],
               "block": rc["block"], "code": code, "pass_published": bool(g["published"]),
               "pass_current": bool(g["current"]), "graded_utc": utc_now()}
        write(rec)
        st["grades"][rc["schedule_id"]] = rec

    def grade_saved():
        """Responses saved earlier but never graded: graded now, never requested again."""
        for sid, rc in list(st["receipts"].items()):
            if rc["window"] == window and not rc["transport_failed"] and sid not in st["grades"]:
                grade_and_write(rc, rc["raw_text"])

    try:
        if partial is not None:
            write({"type": "truncated_line", "window": window, "utc": utc_now(), "content": partial})
        now = clock()
        exhausted = cap is not None and ledger[0] >= cap
        if close:
            if strict and now < end and not exhausted:
                raise SystemExit("window %s ends at %s; close it after that, or once the call budget "
                                 "is spent" % (window, wcfg["end"]))
            grade_saved()
            reason = ("end time passed" if end is not None and now >= end else
                      "call budget exhausted" if exhausted else "closed without a time check")
            write({"type": "window_closed", "window": window, "utc": utc_now(), "reason": reason,
                   "calls_used": ledger[0], "call_budget": cap, "not_collected": unissued(),
                   "interrupted": interrupted()})
            print("window %s closed (%s): %d not collected, %d interrupted" % (
                window, reason, len(unissued()), len(interrupted())))
            return path
        if strict and not (start <= now < end):
            raise SystemExit("window %s runs from %s to %s; it is now %s" % (
                window, wcfg["start"], wcfg["end"], now.isoformat(timespec="seconds")))
        if exhausted:
            raise SystemExit("the %d-call budget is spent; close the window with --close" % cap)
        eps, hosts = {}, {}
        for m in chosen:
            ep, key = (None, None) if mock or post_fn else endpoint_for(cfg[m])
            if not (mock or post_fn) and not (ep and key):
                raise SystemExit("no endpoint or key for %s (set %s and %s)" % (
                    m, cfg[m]["endpoint_env"], cfg[m]["key_env"]))
            eps[m], hosts[m] = (ep, key), (host_id(ep) if ep else "mock")
        commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True,
                                text=True).stdout.strip()
        write({"type": "run_start", "window": window, "utc": utc_now(), "mock": mock, "strict": strict,
               "window_start": wcfg.get("start"), "window_end": wcfg.get("end"), "models": chosen,
               "max_in_flight_per_model": lanes, "harness_commit": commit,
               "python": sys.version.split()[0], "platform": platform.platform(),
               "design_sha256": frz.sha256_file(design_path), "schedule_sha256": man["schedule_sha256"],
               "scheduler_seed": man["scheduler_seed"], "sampling_seed": None, "endpoint_hosts": hosts,
               "calls_used_before": ledger[0], "call_budget": cap,
               "received_before": sum(1 for rc in st["receipts"].values() if rc["window"] == window)})
        grade_saved()

        def allow():
            with lock:
                if cap is not None and ledger[0] >= cap:
                    return False
                ledger[0] += 1
                return True

        next_seq = {m: sum(1 for x in st["issued"].values() if x["window"] == window and x["model"] == m)
                    for m in chosen}
        errors, stops = [], {}
        fail_limit = int(design.get("retry_policy", {}).get("halt_after_consecutive_failures", 3))
        fails, halted = {m: 0 for m in chosen}, set()

        def worker(label, lane):
            mine = sorted((r for r in win_rows if r["model"] == label and r["block_seq"] % lanes == lane),
                          key=lambda r: r["seq_in_window"])
            rng = random.Random("%s|%s|%d|%d" % (window, label, lane, mock_seed))
            ep, key = eps[label]
            try:
                for r in mine:
                    sid = r["schedule_id"]
                    if sid in st["issued"] or sid in st["receipts"]:
                        continue                     # issued once already: never again
                    if label in halted:
                        stops["%s#%d" % (label, lane)] = "consecutive transport failures"
                        return
                    if strict and clock() >= end:
                        stops["%s#%d" % (label, lane)] = "end time reached"
                        return
                    if not allow():                  # reserves the first attempt
                        stops["%s#%d" % (label, lane)] = "call budget exhausted"
                        return
                    task, text = request_text(r["task"], r["condition"])
                    with lock:
                        seq = next_seq[label]
                        next_seq[label] += 1
                    iss = {"type": "issued", "schedule_id": sid, "window": window, "model": label,
                           "lane": lane, "actual_seq": seq, "utc": utc_now()}
                    write(iss)
                    st["issued"][sid] = iss
                    first = [True]

                    def allow_row():
                        if first[0]:
                            first[0] = False
                            return True
                        return allow()

                    if post_fn is not None:
                        resp = post_fn(text, r, allow_row)
                    elif mock:
                        resp = mock_post(text, cfg[label]["id"], r["task"], r["condition"], rng, allow_row, sid)
                    else:
                        resp = transport.post(text, cfg[label]["id"], ep, key, allow_attempt=allow_row)
                    rc = dict(r, type="receipt", actual_seq=seq, lane=lane, start_utc=iss["utc"],
                              end_utc=utc_now(), requested_model=cfg[label]["id"],
                              endpoint_host=hosts[label],
                              prompt_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                              returned_model=resp["returned_model"], response_id=resp["response_id"],
                              usage=resp["usage"], stop_reason=resp["stop_reason"],
                              attempts=resp["attempts"], transport_failed=resp["transport_failed"],
                              budget_stop=resp["budget_stop"], raw_text=resp["text"],
                              response=resp.get("response"))
                    write(rc)                        # saved before grading
                    st["receipts"][sid] = rc
                    with lock:                       # a dead endpoint must not spend the budget
                        fails[label] = fails[label] + 1 if resp["transport_failed"] else 0
                        if fails[label] >= fail_limit:
                            halted.add(label)
                    if not resp["transport_failed"]:
                        grade_and_write(rc, resp["text"])
                    if resp["budget_stop"]:
                        stops["%s#%d" % (label, lane)] = "call budget exhausted"
                        return
            except Exception as e:  # noqa: BLE001 - recorded below, and the run fails
                errors.append({"model": label, "lane": lane, "error": ("%s: %s" % (type(e).__name__, e))[:500]})

        threads = [threading.Thread(target=worker, args=(m, j), name="%s#%d" % (m, j))
                   for m in chosen for j in range(lanes)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        left, intr = unissued(), interrupted()
        final = {k: v for k, v in stops.items() if v in ("end time reached", "call budget exhausted")}
        if errors or (left and halted and not final):
            write({"type": "window_incomplete", "window": window, "utc": utc_now(), "errors": errors,
                   "halted": {m: "%d consecutive transport failures" % fail_limit for m in sorted(halted)},
                   "not_yet_issued": len(left), "interrupted": intr, "calls_used": ledger[0]})
            raise RuntimeError("window %s incomplete; fix and resume it before %s: %s" % (
                window, wcfg.get("end"), errors or "halted %s" % sorted(halted)))
        if not left:
            write({"type": "window_end", "window": window, "utc": utc_now(), "interrupted": intr,
                   "calls_used": ledger[0], "call_budget": cap})
        elif final:
            reason = ("call budget exhausted" if "call budget exhausted" in final.values()
                      else "end time reached")
            write({"type": "window_closed", "window": window, "utc": utc_now(), "reason": reason,
                   "stopped": stops, "calls_used": ledger[0], "call_budget": cap,
                   "not_collected": left, "interrupted": intr})
        print("window %s: %d issued, %d not issued, %d interrupted; %d calls used in total%s" % (
            window, len(win_rows) - len(left), len(left), len(intr), ledger[0],
            "" if cap is None else " of %d" % cap))
        return path
    finally:
        fh.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", required=True)
    ap.add_argument("--mock", action="store_true", help="canned replies, no network")
    ap.add_argument("--close", action="store_true", help="close the window after its end time")
    ap.add_argument("--models", default="", help="comma list of model labels (default: all)")
    a = ap.parse_args()
    run_window(a.window, mock=a.mock, models=[m for m in a.models.split(",") if m], close=a.close)
