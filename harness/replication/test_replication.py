r"""Checks that the replication measures what the published harness measured, and that its record
keeping, enforcement and analysis work. No network: the transport is intercepted or mocked.

  1. transport.build_request reproduces measure_blackwell._azure_complete's request byte for byte,
     for the Anthropic, Responses and chat-completions endpoint styles;
  2. run_replication.request_text reproduces the prompt measure_blackwell.run_one sends, for every
     scheduled task and condition;
  3. the schedule is balanced and every block holds exactly its task's conditions;
  4. a mock collection (canned replies through the real extraction and both graders) records every
     request, and the analysis runs on it;
  5. the bound for unequal windows is the weighted Hoeffding bound;
  6. the analysis reconciles against the full schedule: missing windows, provisional versus final,
     worst case over every planned window;
  7. the freeze is enforced: design, schedule, code and metadata;
  8. a saved response survives an interruption, is graded on resumption and is never requested
     again; worker failures propagate;
  9. the call budget, the window boundaries and the lock are enforced; lanes keep blocks together.

Usage:  python harness/replication/test_replication.py
"""
import copy
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import measure_blackwell as mb  # noqa: E402
import transport  # noqa: E402
import run_replication as rr  # noqa: E402
import make_schedule  # noqa: E402
import analyze  # noqa: E402
import freeze as frz  # noqa: E402
import records  # noqa: E402
import stats  # noqa: E402

FAILS = []
DESIGN = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
TEST_WINDOWS = [{"id": "t1", "start": "2030-01-01T09:00:00+03:00", "end": "2030-01-01T14:00:00+03:00"},
                {"id": "t2", "start": "2030-01-01T15:00:00+03:00", "end": "2030-01-01T20:00:00+03:00"},
                {"id": "t3", "start": "2030-01-02T09:00:00+03:00", "end": "2030-01-02T14:00:00+03:00"}]


def check(cond, label):
    print(("  ok    " if cond else "  FAIL  ") + label)
    if not cond:
        FAILS.append(label)


def raises(fn, exc=SystemExit):
    try:
        fn()
    except exc as e:
        return str(e) or True
    return False


class _Captured(Exception):
    pass


def capture_original(prompt, model, endpoint):
    seen = []

    def fake(req, timeout=None):
        seen.append(req)
        raise _Captured()

    real_open, real_sleep = urllib.request.urlopen, time.sleep
    urllib.request.urlopen, time.sleep = fake, (lambda s: None)
    os.environ["AZURE_OPENAI_ENDPOINT"], os.environ["AZURE_OPENAI_KEY"] = endpoint, "k-test"
    try:
        mb._azure_complete(prompt, model)
    except _Captured:
        pass
    finally:
        urllib.request.urlopen, time.sleep = real_open, real_sleep
    return seen[0]


def same_request(a, b):
    return (a.full_url == b.full_url and a.get_method() == b.get_method() and
            sorted(a.header_items()) == sorted(b.header_items()) and a.data == b.data)


def fast_grade(task, code):
    ok = code.strip() == rr._PASS[task["id"]].strip()
    return {"published": ok, "current": ok}


def small(n_windows=2, n_models=2, bpw=3, **extra):
    d = copy.deepcopy(DESIGN)
    d["windows"] = copy.deepcopy(TEST_WINDOWS[:n_windows])
    d["models"] = d["models"][:n_models]
    d["blocks_per_window"] = bpw
    d.update(extra)
    return d


def setup(tmp, d, frozen=False):
    dp = os.path.join(tmp, "design.json")
    json.dump(d, open(dp, "w", encoding="utf-8", newline="\n"), indent=2)
    if frozen:
        frz.freeze(design_path=dp, out_dir=tmp, root=ROOT, allow_dirty=True)
    else:
        make_schedule.main(design_path=dp, out_dir=tmp)
    return dp


def run(tmp, dp, w, **kw):
    kw.setdefault("mock", True)
    kw.setdefault("grade_fn", fast_grade)
    return rr.run_window(w, design_path=dp, sched_dir=tmp, out_dir=os.path.join(tmp, "records"), **kw)


def fixed(s):
    t = datetime.fromisoformat(s)
    return lambda: t


class Ticking:
    """A clock that advances by step seconds on every reading."""
    def __init__(self, start, step):
        self.t, self.step, self.lock = datetime.fromisoformat(start), timedelta(seconds=step), threading.Lock()

    def __call__(self):
        with self.lock:
            t = self.t
            self.t += self.step
            return t


def tmpdir():
    return tempfile.mkdtemp(prefix="bwrep_test_")


def main():
    print("1. request identity with the published client")
    for ep in ("https://x.services.ai.azure.com/anthropic/v1/messages",
               "https://x.openai.azure.com/openai/responses?api-version=2025-04-01-preview",
               "https://x.services.ai.azure.com/openai/v1/"):
        orig = capture_original("hello prompt", "some-model", ep)
        mine = transport.build_request("hello prompt", "some-model", ep, "k-test")
        check(same_request(orig, mine), "identical request for %s" % ep.split("/")[2].split(".")[1])

    chat = {"id": "c1", "model": "m", "system_fingerprint": "fp_1", "created": 1,
            "choices": [{"message": {"content": "CODE", "reasoning_content": "why"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3}}
    msgs = {"id": "a1", "model": "m", "content": [{"type": "text", "text": "CODE"}], "stop_reason": "end_turn",
            "usage": {"output_tokens": 3}}
    resp = {"id": "r1", "model": "m", "status": "completed", "output_text": "CODE",
            "output": [{"type": "message", "content": [{"type": "output_text", "text": "CODE"}]}]}
    envs = [transport.envelope(x, transport.parse_response(x)["text"]) for x in (chat, msgs, resp)]
    check(all("CODE" not in json.dumps(e) and "<raw_text>" in json.dumps(e) for e in envs)
          and envs[0]["system_fingerprint"] == "fp_1" and envs[0]["choices"][0]["message"]["reasoning_content"] == "why",
          "the whole response is kept for all three styles, the reply text once, provider extras included")
    hid = rr.host_id("https://my-resource.services.ai.azure.com/openai/v1/chat/completions")
    check(hid.endswith(".services.ai.azure.com") and "my-resource" not in hid,
          "the endpoint is recorded by provider domain with the resource name hashed")

    print("2. prompt identity with run_one")
    sent = []
    real = mb._azure_complete
    mb._azure_complete = lambda p, m: (sent.append(p), ("", 0))[1]
    try:
        ok = True
        for task_id, conds in DESIGN["cells"].items():
            task = next(t for t in mb.TASKS if t["id"] == task_id)
            for c in conds:
                sent.clear()
                mb.run_one(task, c, False, 0, "m")
                ok &= bool(sent) and sent[0] == rr.request_text(task_id, c)[1]
        check(ok, "prompt identical for all %d task-condition pairs" % sum(len(v) for v in DESIGN["cells"].values()))
    finally:
        mb._azure_complete = real

    print("3. schedule balance")
    rows = make_schedule.build(DESIGN)
    blocks = {}
    for r in rows:
        blocks.setdefault((r["window"], r["model"], r["task"], r["block"]), []).append(r["condition"])
    check(all(sorted(v) == sorted(DESIGN["cells"][k[2]]) for k, v in blocks.items()),
          "every block holds exactly its task's conditions (%d blocks)" % len(blocks))
    check(len(rows) == frz.n_requests(DESIGN), "request count matches the design (%d)" % len(rows))
    check(make_schedule.build(DESIGN) == rows, "schedule reproducible from the scheduler seed")
    first = {}
    for r in rows:
        if r["position"] == 0:
            first[r["condition"]] = first.get(r["condition"], 0) + 1
    check(len(first) == len({c for v in DESIGN["cells"].values() for c in v}),
          "every condition appears first in some block (order randomized)")
    check(frz.check_design(DESIGN) == [], "the draft design.json passes every pre-freeze check")

    print("4. mock collection with the real graders, and the analysis")
    tmp = tmpdir()
    try:
        d = small()
        dp = setup(tmp, d)
        rr.MOCK_REQUESTS.clear()
        for w in d["windows"]:
            run(tmp, dp, w["id"], grade_fn=None)
        st = records.read_dir(os.path.join(tmp, "records"))
        n = frz.n_requests(d)
        check(len(st["receipts"]) == n and len(st["issued"]) == n, "one issued and one receipt record per request (%d)" % n)
        need = {"start_utc", "end_utc", "attempts", "returned_model", "response_id", "usage", "stop_reason",
                "raw_text", "actual_seq", "seq_in_window", "prompt_sha256", "window", "block",
                "requested_model", "endpoint_host", "response"}
        check(all(need <= set(r) for r in st["receipts"].values()), "every receipt carries the required fields")
        ok_rc = [s for s, r in st["receipts"].items() if not r["transport_failed"]]
        check(set(ok_rc) == set(st["grades"]), "every received response is graded, nothing else")
        g = [st["grades"][s] for s in ok_rc]
        check(all(x["pass_published"] == x["pass_current"] for x in g),
              "published and current graders agree on the canned replies")
        check(any(x["pass_published"] for x in g) and not all(x["pass_published"] for x in g),
              "canned replies both pass and fail the real verifiers")
        orders = {}
        for r in st["receipts"].values():
            orders.setdefault((r["window"], r["model"], r["lane"]), []).append((r["actual_seq"], r["seq_in_window"]))
        check(all(sorted(v) == sorted(v, key=lambda x: x[1]) for v in orders.values()),
              "actual order follows the scheduled order within each lane (%d lanes per model)"
              % d["max_in_flight_per_model"])
        doc = analyze.main(design_path=dp, base=tmp, records_dir=os.path.join(tmp, "records"), check_freeze=False)
        check(len(doc["results"]) == 2 * 4, "analysis reports every contrast for every model")
        check(doc["status"] == "final", "complete collection with every window closed is final")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("5. weighted Hoeffding bound for unequal windows")
    a = 0.05 / 24
    check(abs(stats.weighted_hoeffding_halfwidth([1, 32, 32, 32, 32, 32], a) - 0.6297) < 5e-4,
          "windows of 1 and 5 x 32 blocks: half-width 0.630, not the unweighted 0.277")
    check(abs(stats.weighted_hoeffding_halfwidth([32] * 6, a) - stats.hoeffding_halfwidth(192, a)) < 1e-12,
          "equal windows reduce to the plain bound")
    dd = {"w1": [1]}
    dd.update({"w%d" % i: [1] * 16 + [0] * 16 for i in range(2, 7)})
    s = stats.contrast_summary(dd, a, +1, planned_windows=["w%d" % i for i in range(1, 8)])
    check(abs(s["halfwidth"] - 0.6297) < 5e-4 and s["windows_missing"] == ["w7"],
          "contrast_summary uses the weighted bound and lists the planned window without data")

    print("6. reconciliation against the full schedule")
    tmp = tmpdir()
    try:
        d = small(n_windows=3)
        dp = setup(tmp, d)
        run(tmp, dp, "t1")
        run(tmp, dp, "t2", close=True)                      # closed without collecting anything
        doc = analyze.main(design_path=dp, base=tmp, records_dir=os.path.join(tmp, "records"), check_freeze=False)
        per_w = frz.n_requests(d) // 3
        check(doc["status"] == "provisional" and any("t3" in p for p in doc["problems"]),
              "a planned window never started keeps the analysis provisional")
        check(doc["request_status"]["pending"] == per_w and doc["request_status"]["not collected"] == per_w,
              "unstarted window counted as pending, closed empty window as not collected")
        run(tmp, dp, "t3", close=True)
        doc = analyze.main(design_path=dp, base=tmp, records_dir=os.path.join(tmp, "records"), check_freeze=False)
        check(doc["status"] == "final", "final once every planned window is closed")
        a1 = next(r for r in doc["results"] if r["contrast"] == "A1")
        h1 = next(r for r in doc["results"] if r["contrast"] == "H1")
        check(a1["windows_missing"] == ["t2", "t3"], "primary lists the windows without complete blocks")
        wc = a1["worst_case"]
        check(wc["n_blocks"] == 3 * d["blocks_per_window"] and wc["windows_missing"] == [],
              "worst case covers every scheduled block of every planned window")
        check(wc["by_window"]["t2"]["estimate"] == -1 and h1["worst_case"]["by_window"]["t3"]["estimate"] == 1,
              "a lost window enters the worst case at the least favourable value")
        check(abs(wc["halfwidth"] - stats.weighted_hoeffding_halfwidth([3, 3, 3], d["analysis"]["per_statement_alpha"])) < 1e-12,
              "worst-case bound uses the planned window sizes")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("7. freeze enforcement")
    per_block = frz.n_requests(DESIGN) // DESIGN["blocks_per_window"]
    over = int(DESIGN["budget"]["max_api_calls"] * (1 - DESIGN["budget"]["min_retry_headroom_fraction"]) / per_block) + 1
    check(any("budget" in p for p in frz.check_design(dict(copy.deepcopy(DESIGN), blocks_per_window=over))),
          "a schedule over the call budget (%d blocks per window) cannot be frozen" % over)
    t = small()
    t["windows"][1]["start"] = "2030-01-01T13:00:00+03:00"
    check(any("previous window" in p for p in frz.check_design(t)), "overlapping windows cannot be frozen")
    t = small()
    t["windows"][0]["end"] = "2030-01-01T14:00:00"
    check(any("boundaries" in p for p in frz.check_design(t)), "a boundary without a UTC offset cannot be frozen")
    t = small()
    t["interruption_rules"] = []
    check(any("interruption" in p for p in frz.check_design(t)), "a design without interruption rules cannot be frozen")
    tmp = tmpdir()
    try:
        d = small()
        dp = setup(tmp, d, frozen=True)
        check(frz.verify(dp, tmp, ROOT) == [], "a fresh freeze verifies")
        check(bool(raises(lambda: frz.freeze(dp, tmp, ROOT, allow_dirty=True))), "a second freeze is refused")
        base_design = open(dp, encoding="utf-8").read()
        base_freeze = open(os.path.join(tmp, "FREEZE.json"), encoding="utf-8").read()

        def tamper(edit):
            x = json.loads(base_design)
            edit(x)
            json.dump(x, open(dp, "w", encoding="utf-8", newline="\n"), indent=2)

        def restore():
            open(dp, "w", encoding="utf-8", newline="\n").write(base_design)
            open(os.path.join(tmp, "FREEZE.json"), "w", encoding="utf-8", newline="\n").write(base_freeze)

        tamper(lambda x: x["models"][0].update(id="another-model"))
        check(any("design.json changed" in p for p in frz.verify(dp, tmp, ROOT)), "a changed model id is detected")
        msg = raises(lambda: run(tmp, dp, "t1", strict=True, clock=fixed("2030-01-01T10:00:00+03:00")))
        check(bool(msg) and "freeze check failed" in str(msg), "the runner refuses a changed model id")
        tamper(lambda x: x["analysis"].update(per_statement_alpha=0.05))
        check(any("design.json changed" in p for p in frz.verify(dp, tmp, ROOT)), "a changed alpha is detected")
        tamper(lambda x: x.update(frozen_at_utc=None))
        check(any("freeze metadata" in p for p in frz.verify(dp, tmp, ROOT)), "missing freeze metadata is detected")
        restore()
        fzp = os.path.join(tmp, "FREEZE.json")
        f = json.loads(base_freeze)
        f["code_sha256"]["harness/replication/stats.py"] = "0" * 64
        json.dump(f, open(fzp, "w", encoding="utf-8"))
        check(any("stats.py changed" in p for p in frz.verify(dp, tmp, ROOT)), "a changed code file is detected")
        f = json.loads(base_freeze)
        del f["code_sha256"]["harness/replication/records.py"]
        json.dump(f, open(fzp, "w", encoding="utf-8"))
        check(any("does not hash" in p for p in frz.verify(dp, tmp, ROOT)), "a code file missing from the freeze is detected")
        f = json.loads(base_freeze)
        f["harness_commit"] = ""
        json.dump(f, open(fzp, "w", encoding="utf-8"))
        check(any("FREEZE.json lacks" in p for p in frz.verify(dp, tmp, ROOT)), "incomplete FREEZE.json is detected")
        os.remove(fzp)
        check(frz.verify(dp, tmp, ROOT) == ["no FREEZE.json: the design has not been frozen"], "a missing FREEZE.json is detected")
        restore()
        run(tmp, dp, "t1", strict=True, clock=fixed("2030-01-01T10:00:00+03:00"))
        check(bool(raises(lambda: frz.freeze(dp, tmp, ROOT, force=True, allow_dirty=True))),
              "re-freezing after collection started is refused")
        tamper(lambda x: x["models"][1].update(id="another-model"))
        doc = analyze.main(design_path=dp, base=tmp, records_dir=os.path.join(tmp, "records"), check_freeze=True,
                           write=False)
        check(doc["status"] == "provisional" and any(p.startswith("freeze:") for p in doc["problems"]),
              "the analysis cannot be final when the freeze is broken")
        check(any("inconsistent" in p for p in doc["problems"]),
              "receipts that no longer match the design's model id are flagged")
        restore()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("8. receipts before grading, resumption, failure propagation")
    tmp = tmpdir()
    try:
        d = small()
        dp = setup(tmp, d)
        rr.MOCK_REQUESTS.clear()
        calls = [0]

        def crash_on_fifth(task, code):
            calls[0] += 1
            if calls[0] == 5:
                raise RuntimeError("simulated crash while grading")
            return fast_grade(task, code)

        msg = raises(lambda: run(tmp, dp, "t1", grade_fn=crash_on_fifth), RuntimeError)
        st = records.read_dir(os.path.join(tmp, "records"))
        ungraded = [s for s, r in st["receipts"].items() if not r["transport_failed"] and s not in st["grades"]]
        check(bool(msg) and any(e["type"] == "window_incomplete" for e in st["events"]),
              "a worker failure fails the run and is recorded")
        check(len(ungraded) >= 1, "the response whose grading crashed was saved before grading")
        victim = sorted(set(rr.MOCK_REQUESTS) - set(st["receipts"]))
        path = os.path.join(tmp, "records", "t1.jsonl")
        open(path, "a", encoding="utf-8", newline="\n").write('{"type": "receipt", "schedule_id": "t1|')
        check(records.read_dir(os.path.join(tmp, "records"))["truncated"] != [],
              "a partial last line is tolerated and reported")
        run(tmp, dp, "t1")
        st = records.read_dir(os.path.join(tmp, "records"))
        check(all(s in st["grades"] for s in ungraded), "saved responses are graded on resumption")
        dup = len(rr.MOCK_REQUESTS) - len(set(rr.MOCK_REQUESTS))
        check(dup == 0, "no scheduled request was sent twice")
        check(any(e["type"] == "truncated_line" for e in st["events"]) and not st["truncated"],
              "the partial line is kept as data and the file parses again")
        check(any(e["type"] == "window_end" for e in st["events"] if e.get("window") == "t1"), "the resumed window ends")
        check(victim == [], "no request was left issued without a receipt by the grading crash")

        victim_sid = next(r["schedule_id"] for r in make_schedule.build(d) if r["window"] == "t2")
        sent = []
        rng = __import__("random").Random(1)

        def crash_in_flight(text, row, allow):
            sent.append(row["schedule_id"])
            if row["schedule_id"] == victim_sid:
                raise ConnectionError("simulated crash in flight")
            return rr.mock_post(text, "m", row["task"], row["condition"], rng, allow, row["schedule_id"])

        check(bool(raises(lambda: run(tmp, dp, "t2", post_fn=crash_in_flight, mock=False, strict=False), RuntimeError)),
              "a crash in flight fails the run")
        run(tmp, dp, "t2", post_fn=crash_in_flight, mock=False, strict=False)
        check(sent.count(victim_sid) == 1, "the request lost in flight is not requested again")
        doc = analyze.main(design_path=dp, base=tmp, records_dir=os.path.join(tmp, "records"), check_freeze=False,
                           write=False)
        check(doc["request_status"]["interrupted"] == 1 and doc["request_status"]["ungraded"] == 0,
              "the analysis counts it as interrupted, and nothing is left ungraded")
        st = records.read_dir(os.path.join(tmp, "records"))
        used = records.calls_used(st)
        check(used == sum(len(r["attempts"]) for r in st["receipts"].values()) + 3,
              "the budget ledger charges an interrupted request its maximum attempts")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    tmp = tmpdir()
    try:
        d = small(n_windows=1, n_models=1, bpw=1)
        dp = setup(tmp, d)
        odd = "\ud800" + rr._PASS["api_post_ok"]

        def odd_post(text, row, allow):
            allow()
            return {"text": odd, "output_tokens": 1, "returned_model": "m", "response_id": "r", "usage": {},
                    "stop_reason": "end_turn", "transport_failed": False, "budget_stop": False,
                    "attempts": [{"attempt": 1, "start_utc": "", "end_utc": "", "http_status": 200, "error": None}]}

        run(tmp, dp, "t1", post_fn=odd_post, mock=False, strict=False, grade_fn=None)
        st = records.read_dir(os.path.join(tmp, "records"))
        check(len(st["grades"]) == frz.n_requests(d) and not any(g["pass_published"] for g in st["grades"].values()),
              "a reply with a lone surrogate is saved, graded with the real graders and fails")
        check(all(r["raw_text"] == odd for r in st["receipts"].values()), "the raw reply is stored exactly")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("9. call budget, window boundaries, lock, lanes")
    tmp = tmpdir()
    try:
        d = small(budget={"max_api_calls": 40, "min_retry_headroom_fraction": 0.05})
        dp = setup(tmp, d)
        run(tmp, dp, "t1")
        st = records.read_dir(os.path.join(tmp, "records"))
        closed = [e for e in st["events"] if e["type"] == "window_closed"]
        check(records.calls_used(st) <= 40 and closed and closed[0]["reason"] == "call budget exhausted",
              "collection stops at the global call budget (%d of 40 calls)" % records.calls_used(st))
        msg = raises(lambda: run(tmp, dp, "t2"))
        check(bool(msg) and "budget is spent" in str(msg), "no later window starts once the budget is spent")
        run(tmp, dp, "t2", close=True)
        doc = analyze.main(design_path=dp, base=tmp, records_dir=os.path.join(tmp, "records"), check_freeze=False,
                           write=False)
        check(doc["status"] == "final" and doc["request_status"]["not collected"] >= frz.n_requests(d) // 2,
              "the budget-closed windows are reconciled as not collected")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    tmp = tmpdir()
    try:
        d = small()
        dp = setup(tmp, d, frozen=True)
        msg = raises(lambda: run(tmp, dp, "t1", strict=True, clock=fixed("2030-01-01T08:59:59+03:00")))
        check(bool(msg) and "runs from" in str(msg), "a window cannot start before its start time")
        msg = raises(lambda: run(tmp, dp, "t1", strict=True, clock=fixed("2030-01-01T14:00:00+03:00")))
        check(bool(msg) and "runs from" in str(msg), "a window cannot start at or after its end")
        msg = raises(lambda: run(tmp, dp, "t1", strict=True, close=True, clock=fixed("2030-01-01T13:00:00+03:00")))
        check(bool(msg) and "close it after" in str(msg), "a window cannot be closed before its end")
        tick = Ticking("2030-01-01T13:40:00+03:00", 60)          # passes 14:00 after 20 readings
        run(tmp, dp, "t1", strict=True, clock=tick)
        st = records.read_dir(os.path.join(tmp, "records"))
        issued = [x for x in st["issued"].values() if x["window"] == "t1"]
        ev = [e for e in st["events"] if e.get("window") == "t1" and e["type"] == "window_closed"]
        check(0 < len(issued) < frz.n_requests(d) // 2 and ev and ev[0]["reason"] == "end time reached",
              "requests stop at the window's end and the window closes (%d issued)" % len(issued))
        check(len(ev[0]["not_collected"]) == frz.n_requests(d) // 2 - len(issued),
              "every unissued request of the window is recorded as not collected")
        check(bool(raises(lambda: run(tmp, dp, "t1", strict=True, clock=fixed("2030-01-01T10:00:00+03:00")))),
              "a closed window cannot be resumed")
        open(os.path.join(tmp, "records", ".run.lock"), "w").write("x")
        msg = raises(lambda: run(tmp, dp, "t2", strict=True, clock=fixed("2030-01-01T16:00:00+03:00")))
        check(bool(msg) and "another run holds" in str(msg), "a second concurrent run is refused")
        os.remove(os.path.join(tmp, "records", ".run.lock"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    tmp = tmpdir()
    try:
        d = small(max_in_flight_per_model=2)
        dp = setup(tmp, d)
        run(tmp, dp, "t1")
        st = records.read_dir(os.path.join(tmp, "records"))
        lanes = {}
        for r in st["receipts"].values():
            lanes.setdefault((r["model"], r["task"], r["block"]), set()).add(r["lane"])
        check(all(len(v) == 1 for v in lanes.values()) and {l for v in lanes.values() for l in v} == {0, 1},
              "with two lanes, each block stays in one lane and both lanes are used")
        seqs = {}
        for x in st["issued"].values():
            seqs.setdefault(x["model"], []).append(x["actual_seq"])
        check(all(sorted(v) == list(range(len(v))) for v in seqs.values()), "issue order is recorded without gaps")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("10. live verification script, offline")
    tmp = tmpdir()
    try:
        import smoke
        check(smoke.main(mock=True, out_root=tmp) is True,
              "smoke.py runs freeze, a strict window, both graders and a final analysis end to end")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    tmp = tmpdir()
    real_mock = rr.mock_post
    try:
        def rejected(prompt, model, task_id, condition, rng, allow_attempt=None, sid=None):
            att = []
            for i in range(3):
                if allow_attempt is not None and not allow_attempt():
                    break
                att.append({"attempt": i + 1, "start_utc": "", "end_utc": "", "http_status": 400,
                            "error": "HTTPError: HTTP Error 400: Bad Request",
                            "error_body": '{"error": {"message": "Unsupported parameter: max_tokens"}}'})
            return rr._no_response(att, True, False)

        rr.mock_post = rejected
        ok = smoke.main(mock=True, out_root=tmp)
        rep = open(os.path.join(tmp, os.listdir(tmp)[0], "VERIFICATION.md"), encoding="utf-8").read()
        check(ok is False and "Unsupported parameter" in rep and "no transport failure: NO" in rep,
              "a halted model is reported with the provider's reason instead of crashing the check")
    finally:
        rr.mock_post = real_mock
        shutil.rmtree(tmp, ignore_errors=True)
    real_open, real_sleep = urllib.request.urlopen, time.sleep

    def http400(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {},
                                     io.BytesIO(b'{"error": {"message": "Unsupported parameter"}}'))

    urllib.request.urlopen, time.sleep = http400, (lambda s: None)
    try:
        r400 = transport.post("p", "m", "https://x.services.ai.azure.com/openai/v1/", "k")
    finally:
        urllib.request.urlopen, time.sleep = real_open, real_sleep
    check(r400["transport_failed"] and all("Unsupported parameter" in (a["error_body"] or "") for a in r400["attempts"]),
          "transport keeps the provider's error body on every failed attempt")

    print("11. a dead endpoint is halted before it spends the budget")
    tmp = tmpdir()
    try:
        d = small(n_windows=1)
        dp = setup(tmp, d)
        dead = d["models"][0]["label"]
        rng3 = __import__("random").Random(3)

        def half_dead(text, row, allow):
            if row["model"] != dead:
                return rr.mock_post(text, "m", row["task"], row["condition"], rng3, allow, row["schedule_id"])
            att = []
            for i in range(3):
                if not allow():
                    break
                att.append({"attempt": i + 1, "start_utc": "", "end_utc": "", "http_status": 401,
                            "error": "HTTPError: HTTP Error 401: Unauthorized"})
            return {"text": None, "output_tokens": None, "returned_model": None, "response_id": None,
                    "usage": None, "stop_reason": None, "response": None, "attempts": att,
                    "transport_failed": True, "budget_stop": False}

        msg = raises(lambda: run(tmp, dp, "t1", post_fn=half_dead, mock=False, strict=False), RuntimeError)
        st = records.read_dir(os.path.join(tmp, "records"))
        failed = [s for s, r in st["receipts"].items() if r["model"] == dead]
        lanes = d["max_in_flight_per_model"]
        check(bool(msg) and "halted" in str(msg) and 3 <= len(failed) <= 3 + lanes - 1,
              "a model whose requests keep failing is halted after 3 (%d failed requests, %d calls)"
              % (len(failed), records.calls_used(st)))
        others = [r for r in make_schedule.build(d) if r["model"] != dead]
        check(all(r["schedule_id"] in st["receipts"] for r in others), "the other models finish their requests")
        check("t1" not in records.closed_windows(st), "the window stays open to be fixed and resumed")
        rr.MOCK_REQUESTS.clear()
        run(tmp, dp, "t1")
        st = records.read_dir(os.path.join(tmp, "records"))
        check("t1" in records.closed_windows(st) and not set(failed) & set(rr.MOCK_REQUESTS),
              "after the fix the window completes, and the failed requests are not requested again")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n%s" % ("ALL CHECKS PASSED" if not FAILS else "%d FAILED" % len(FAILS)))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
