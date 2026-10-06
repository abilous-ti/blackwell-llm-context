r"""Package 3 runner: listwise reranking on HotpotQA's retrieved candidates (fullwiki setting), as
fixed in PROTOCOL_FULLWIKI.md. Package 2's code is imported, not copied: run_qa's prompts, RankGPT
parsing and repair rule, request records and transport; rank_local's rankers.

Phases
  local   the five local rankers over each question's 10 released candidates: package 2's
          rank_local.main unchanged, with BM25's IDF taken over every paragraph of the fullwiki file
          (natural_data/package3/idf_fullwiki.json). Needs sentence-transformers (the venv Python);
          run once before the freeze and refused after it.
  rank    RankGPT: Haiku-4.5 ranks the 10 candidates with run_qa's listwise prompt in two input
          orders, o0 = file order (used for answering) and o1 = run_qa's seeded shuffle (stability
          only): 2 requests per question.
  answer  Haiku-4.5, GPT-5.5 and DeepSeek-V4-Pro answer under none | full (all 10 candidates) |
          bm25 | mmr | bge | e5 | minilm | rankgpt (each ranker's top K = 2, in rank order):
          24 requests per question. A question whose o0 ranking failed gets no RankGPT answers.

Modes (exactly one)
  --mock      deterministic fabricated replies; no network, no key is read. Confirmatory items;
              records in natural_data/package3/mock_fullwiki (never frozen, never the confirmatory
              directory).
  --smoke N   a small real run on the first N smoke items (drawn after the 300 confirmatory
              questions, so never a confirmatory question); natural_data/package3/smoke_fullwiki.
  --confirm   the confirmatory run, refused unless the freeze verifies (freeze_fullwiki.py);
              natural_data/package3/confirm_fullwiki.
  --dry-run with a mode checks everything (freeze, disk, credentials by name) and sends nothing.

Safety. A request is issued at most once and its reply is saved (written and synced) before that
lane's next request; rerunning the same command resumes. A live run is refused with less than
300 MB free on the records' drive; with less than 100 MB free every lane stops before its next
request (no reply is lost) and the run resumes once space is freed. Ctrl+C stops the same way.
Three consecutive transport failures halt a lane (package 2's rule). One run per record directory
(run.lock). Keys come only from the BW_* environment variables and are never printed or stored.

  python harness/package3/run_fullwiki.py --mock
  python harness/package3/run_fullwiki.py --smoke 2
  python harness/package3/run_fullwiki.py --confirm --dry-run
  python harness/package3/run_fullwiki.py --confirm
  python harness/package3/run_fullwiki.py --confirm --summary
  C:/Users/AndriyBilous/stv/Scripts/python.exe harness/package3/run_fullwiki.py --phase local
"""
import argparse
import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True          # never write bytecode next to package 2's modules
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "package2"))
import run_qa as Q  # noqa: E402  (imports harness/replication/transport.py and design.json)

transport = Q.transport
P3 = ROOT / "natural_data" / "package3"
SETS = {
    "confirm": {"items": P3 / "items_confirm.jsonl", "rankings": P3 / "rankings_local_confirm.jsonl",
                "out": P3 / "confirm_fullwiki"},
    "smoke": {"items": P3 / "items_smoke.jsonl", "rankings": P3 / "rankings_local_smoke.jsonl",
              "out": P3 / "smoke_fullwiki"},
    "mock": {"items": P3 / "items_confirm.jsonl", "rankings": P3 / "rankings_local_confirm.jsonl",
             "out": P3 / "mock_fullwiki"},
}
IDF = P3 / "idf_fullwiki.json"
LOCAL = ("bm25", "mmr", "bge", "e5", "minilm")
CONDITIONS = ("none", "full") + Q.RANKED                 # 8 conditions
K = Q.BUDGET["hotpotqa"]                                 # 2
LANES = 4                                                # package 2's confirmatory qa_lanes
MB = 2 ** 20
MIN_FREE_START = 300 * MB                                # a live run is refused below this
MIN_FREE_RUN = 100 * MB                                  # every lane stops below this
ANSWER_LINE = re.compile(r"(?:final answer|answer)\s*[:\-]", re.I)    # analyze_qa's compliance test


def rel(p):
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def write_lf(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:      # LF, as the repository stores text
        fh.write(text)


def free_bytes(path):
    p = Path(path).resolve()
    while not p.exists():
        p = p.parent
    return shutil.disk_usage(str(p)).free


def load_items(mode, n=None):
    items = [json.loads(l) for l in open(SETS[mode]["items"], encoding="utf-8") if l.strip()]
    return items[:n] if n else items


def load_local(mode):
    out = {}
    for line in open(SETS[mode]["rankings"], encoding="utf-8"):
        r = json.loads(line)
        out[(r["id"], r["ranker"])] = r["order"]
    return out


def failure_class(rc):
    """'http400' when every attempt ended in HTTP 400 (where content-filter refusals fall), else 'other'."""
    st = [a.get("http_status") for a in (rc.get("attempts") or [])]
    return "http400" if st and all(s == 400 for s in st) else "other"


# ---- requests (package 2's formats) -------------------------------------------------------------
def rank_requests(items):
    """As run_qa.build_rank_requests for ranking items (checked against it in --mock): o0 = the
    candidates in file order, o1 = the same seeded shuffle (run_qa.SEED and the question id)."""
    reqs = []
    for it in items:
        pool = list(range(len(it["paragraphs"])))
        orders = [pool, pool[:]]
        random.Random("%s|%s" % (Q.SEED, it["id"])).shuffle(orders[1])
        for j, o in enumerate(orders):
            reqs.append({"id": "rank|%s|%s|o%d" % (Q.RANK_MODEL, it["id"], j), "kind": "rank",
                         "model": Q.RANK_MODEL, "item": it["id"], "pool": o, "order_idx": j, "size": len(o)})
    return reqs


def answer_requests(items, rankings):
    """As run_qa.run's answer phase: no RankGPT answers for a question without an o0 ranking."""
    reqs = []
    for it in items:
        for cond in CONDITIONS:
            if cond == "rankgpt" and (it["id"], "rankgpt") not in rankings:
                continue                     # its ranking request failed: recorded, not imputed
            for m in Q.ANSWER_MODELS:
                reqs.append({"id": "ans|%s|%s|%s" % (m, it["id"], cond), "kind": "answer", "model": m,
                             "item": it["id"], "cond": cond, "role": it["role"], "dataset": it["dataset"],
                             "prompt": Q.answer_prompt(it, cond, rankings)})
    return reqs


# ---- mock replies (fabricated, deterministic; exercise every path of the analysis) --------------
def _u(*parts):
    h = hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") / 2.0 ** 64


MOCK_SHIFT = {"Haiku-4.5": -0.05, "GPT-5.5": 0.05, "DeepSeek-V4-Pro": 0.0}


def mock_response(req, it, mid):
    now = transport.utc_now()
    rid = req["id"]
    if _u("fail", rid) < (0.01 if req["kind"] == "rank" else 0.004):        # simulated missing outcome
        filt = _u("filter", rid) < 0.6
        att = [{"attempt": a + 1, "start_utc": now, "end_utc": now, "http_status": 400 if filt else None,
                "error": "HTTPError: HTTP Error 400: Bad Request (mock)" if filt else "TimeoutError: timed out (mock)",
                "error_body": "mock content filter" if filt else None} for a in range(3)]
        return {"text": None, "returned_model": None, "response_id": None, "usage": None, "stop_reason": None,
                "response": None, "attempts": att, "transport_failed": True}
    if req["kind"] == "rank":
        pool = req["pool"]
        order = sorted(range(len(pool)), key=lambda k: -(_u("rank", rid, pool[k]) +
                                                         (0.9 if it["paragraphs"][pool[k]]["supporting"] else 0.0)))
        if _u("short", rid) < 0.05:
            order = order[:7]                # an incomplete reply: the repair rule appends the rest
        text = " > ".join("[%d]" % (k + 1) for k in order)
    else:
        n_sup = sum(1 for p in it["paragraphs"] if p["supporting"] and ("] %s: " % p["title"]) in req["prompt"])
        p = (0.30 if req["cond"] == "none" else (0.25, 0.55, 0.80)[min(n_sup, 2)]) + MOCK_SHIFT[req["model"]]
        u = _u("answer", rid)
        ans = it["answers"][0] if u < p else ("%s, probably" % it["answers"][0] if u < p + 0.10 else "unknown")
        text = ("Mock reply without an answer line (fabricated).\n%s" % ans if _u("format", rid) < 0.03
                else "Mock reasoning (fabricated; no model was called).\nAnswer: %s" % ans)
    return {"text": text, "returned_model": mid, "response_id": "mock", "stop_reason": "mock", "response": None,
            "usage": {"input_tokens": len(req["prompt"]) // 4, "output_tokens": max(1, len(text) // 4)},
            "attempts": [{"attempt": 1, "start_utc": now, "end_utc": now, "http_status": 200, "error": None}],
            "transport_failed": False}


# ---- credentials (names only; values are never printed) -----------------------------------------
def endpoint(m):
    spec = Q.MODELS[m]
    return spec["id"], os.environ.get(spec["endpoint_env"]), os.environ.get(spec["key_env"])


def credential_vars(models):
    return [v for m in models for v in (Q.MODELS[m]["endpoint_env"], Q.MODELS[m]["key_env"])]


def missing_credentials(models):
    return [v for v in credential_vars(models) if not os.environ.get(v)]


# ---- the record writer and the lanes ------------------------------------------------------------
class Runner:
    def __init__(self, out_dir, mock, lanes):
        self.out_dir, self.mock, self.lanes = Path(out_dir), mock, lanes
        self.path = self.out_dir / "records.jsonl"
        self.lockfile = self.out_dir / "run.lock"
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.stop_reason = None
        self.unsaved = []
        self.fd = None
        self.dirty = False
        self.locked = False

    def start(self):
        self.out_dir.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.lockfile), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise SystemExit("%s exists: another run may be active on this directory. If none is (for example "
                             "after a crash), delete that file by hand and rerun." % rel(self.lockfile))
        os.write(fd, ("pid %d since %s\n" % (os.getpid(), transport.utc_now())).encode("ascii"))
        os.close(fd)
        self.locked = True
        if self.path.exists() and self.path.stat().st_size > 0:
            with open(self.path, "rb") as fb:
                fb.seek(-1, os.SEEK_END)
                self.dirty = fb.read(1) != b"\n"     # a line cut by a crash is closed before appending
        self.fd = os.open(str(self.path), os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o644)

    def write(self, rec):
        """Append one record and sync it (package 2's json.dumps(rec, sort_keys=True) lines)."""
        data = (json.dumps(rec, sort_keys=True) + "\n").encode("utf-8")
        with self.lock:
            if self.dirty:
                data = b"\n" + data
            try:
                view = memoryview(data)
                while view:
                    view = view[os.write(self.fd, view):]
                os.fsync(self.fd)
                self.dirty = False
            except OSError:
                self.dirty = True
                raise

    def try_write(self, rec):
        try:
            self.write(rec)
            return True
        except OSError:
            return False

    def halt(self, reason):
        with self.lock:
            first = not self.stop.is_set()
            self.stop.set()
            if first:
                self.stop_reason = reason
        if first:
            self.try_write({"type": "halt", "id": "run|%s" % transport.utc_now(), "reason": reason})
            print("STOP: %s. Every lane stops before its next request; replies in flight are saved. Rerun the "
                  "same command to resume." % reason, flush=True)

    def execute(self, reqs, st, by_id):
        todo = defaultdict(list)
        for k, r in enumerate(reqs):
            if r["id"] not in st["issued"]:
                todo[(r["model"], k % self.lanes)].append(r)
        if not todo or self.stop.is_set():
            return
        if not self.mock:
            miss = missing_credentials(sorted({m for m, _ in todo}))
            if miss:
                raise SystemExit("not set in this terminal: %s (values are never printed)" % ", ".join(miss))
        total = sum(len(v) for v in todo.values())
        print("%s phase: %d requests to issue (%d lanes)" % (reqs[0]["kind"], total, len(todo)), flush=True)
        done = [0]

        def worker(m, lane):
            mid, ep, key = (Q.MODELS[m]["id"], None, None) if self.mock else endpoint(m)
            fails = 0
            for r in todo[(m, lane)]:
                if self.stop.is_set():
                    return
                free = free_bytes(self.out_dir)
                if free < MIN_FREE_RUN:
                    self.halt("%.0f MB free on the records' drive, below %d MB" % (free / MB, MIN_FREE_RUN // MB))
                    return
                if not self.try_write({"type": "issued", "id": r["id"], "utc": transport.utc_now()}):
                    self.halt("a request could not be recorded, so it was not sent")
                    return
                t0 = time.perf_counter()
                resp = mock_response(r, by_id[r["item"]], mid) if self.mock else transport.post(r["prompt"], mid, ep, key)
                rec = {k: v for k, v in r.items() if k != "prompt"}
                rec.update({"type": "receipt", "wall_s": round(time.perf_counter() - t0, 3),
                            "prompt_sha256": hashlib.sha256(r["prompt"].encode("utf-8")).hexdigest(),
                            "prompt_chars": len(r["prompt"]), "requested_model": mid,
                            "returned_model": resp.get("returned_model"), "response_id": resp.get("response_id"),
                            "usage": resp.get("usage"), "stop_reason": resp.get("stop_reason"),
                            "attempts": resp.get("attempts"), "transport_failed": resp.get("transport_failed"),
                            "raw_text": resp.get("text"), "response": resp.get("response")})
                if not self.try_write(rec):
                    with self.lock:
                        self.unsaved.append(rec)
                    self.halt("a reply could not be saved")
                    return
                with self.lock:
                    done[0] += 1
                    d = done[0]
                if d % 250 == 0 or d == total:
                    print("  %d/%d" % (d, total), flush=True)
                fails = fails + 1 if resp.get("transport_failed") else 0
                if fails >= 3:
                    self.try_write({"type": "halt", "id": "%s|lane%d" % (m, lane),
                                    "reason": "three consecutive transport failures"})
                    print("lane %d of %s halted after three consecutive transport failures (rerun to resume)" % (lane, m),
                          flush=True)
                    return

        def guarded(m, lane):
            try:
                worker(m, lane)
            except Exception as e:  # noqa: BLE001 - any bug stops every lane instead of one silently
                import traceback
                traceback.print_exc()
                self.halt("unexpected error in lane %d of %s: %s: %s" % (lane, m, type(e).__name__, e))

        threads = [threading.Thread(target=guarded, args=key) for key in sorted(todo)]
        for t in threads:
            t.start()
        interrupted = False
        while True:
            try:
                alive = [t for t in threads if t.is_alive()]
                if not alive:
                    break
                alive[0].join(timeout=0.5)
            except KeyboardInterrupt:
                if not interrupted:
                    interrupted = True
                    self.halt("stopped by Ctrl+C")
                else:
                    print("waiting for the requests in flight; their replies are saved as they arrive", flush=True)

    def finish(self):
        if self.unsaved:
            left = [rec for rec in self.unsaved if not self.try_write(rec)]
            if left:
                print("%d replies could not be saved to %s. They follow as JSON lines prefixed 'UNSAVED '; append "
                      "them (without the prefix) to that file once space is free." % (len(left), rel(self.path)))
                for rec in left:
                    print("UNSAVED " + json.dumps(rec, sort_keys=True))
            self.unsaved = left
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        if self.locked:
            try:
                os.remove(str(self.lockfile))
            except OSError:
                pass
            self.locked = False


# ---- phases --------------------------------------------------------------------------------------
def freeze_guard():
    import freeze_fullwiki as FZ
    problems = FZ.check()
    if problems:
        raise SystemExit("confirmatory run refused, the freeze does not verify: " + "; ".join(problems))
    return json.loads(FZ.FREEZE.read_text(encoding="utf-8"))["frozen_at_utc"]


LOCAL_MODELS = ("BAAI/bge-small-en-v1.5", "intfloat/e5-small-v2", "cross-encoder/ms-marco-MiniLM-L-6-v2")


def local_phase():
    import freeze_fullwiki as FZ
    if FZ.FREEZE.exists():
        raise SystemExit("package 3 is frozen: the local rankings are not recomputed")
    os.environ["HF_HUB_OFFLINE"] = "1"          # before any Hugging Face import: the local cache only,
    os.environ["TRANSFORMERS_OFFLINE"] = "1"    # never the network (rank_local's own setting)
    import rank_local as RL
    try:
        import sentence_transformers  # noqa: F401
        from huggingface_hub import snapshot_download
    except ImportError:
        raise SystemExit("the local phase needs sentence-transformers: run it with the venv Python, "
                         "C:/Users/AndriyBilous/stv/Scripts/python.exe")
    d = json.loads(IDF.read_text(encoding="utf-8"))
    n = d["paragraphs"]
    idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in d["df"].items()}   # rank_local.idf_table's formula
    RL.idf_table = lambda dataset: (idf, n)     # rank_local.main runs unchanged, with the fullwiki IDF
    for mode in ("confirm", "smoke"):
        RL.main(str(SETS[mode]["items"]), str(SETS[mode]["rankings"]))
    write_lf(P3 / "local_models.json", json.dumps(model_provenance(snapshot_download), indent=1) + "\n")
    print("model provenance -> %s" % rel(P3 / "local_models.json"))
    return 0


def model_provenance(snapshot_download):
    """The cached checkpoints the local rankings come from: revision and SHA-256 of every file."""
    prov = {"offline": {v: os.environ.get(v) for v in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}, "models": {}}
    for name in LOCAL_MODELS:
        snap = Path(snapshot_download(name, local_files_only=True))
        prov["models"][name] = {"revision": snap.name, "sha256": {
            f.relative_to(snap).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(snap.rglob("*")) if f.is_file()}}
    return prov


def run(mode, out_dir, n=None, lanes=LANES, phases=("rank", "answer"), dry_run=False):
    mock = mode == "mock"
    frozen_at = freeze_guard() if mode == "confirm" else None
    items = load_items(mode, n)
    by_id = {it["id"]: it for it in items}
    local = load_local(mode)
    gaps = [(it["id"], rk) for it in items for rk in LOCAL if (it["id"], rk) not in local]
    if gaps:
        raise SystemExit("local rankings missing for %d (question, ranker) pairs: run --phase local first" % len(gaps))
    if mock and Q.build_rank_requests([dict(it, role="hotpot_rank") for it in items]) != rank_requests(items):
        raise SystemExit("rank requests differ from run_qa.build_rank_requests")
    rec_path = out_dir / "records.jsonl"
    st = Q.load_records(rec_path)
    free = free_bytes(out_dir)
    if dry_run:
        rankings = dict(local)
        rankings.update(Q.rankgpt_rankings(st, by_id))
        n_rank = sum(1 for r in rank_requests(items) if r["id"] not in st["issued"])
        n_ans = sum(1 for r in answer_requests(items, rankings) if r["id"] not in st["issued"])
        waiting = sum(1 for it in items if "rank|%s|%s|o0" % (Q.RANK_MODEL, it["id"]) not in st["issued"])
        print("mode %s: %d questions; records %s" % (mode, len(items), rel(rec_path)))
        print("freeze: %s" % ("verified (frozen at %s)" % frozen_at if frozen_at else "not required for this mode"))
        print("free space on the records' drive: %.0f MB (a live run needs at least %d MB; lanes stop below %d MB)" % (
            free / MB, MIN_FREE_START // MB, MIN_FREE_RUN // MB))
        print("ranking requests to issue: %d of %d" % (n_rank, 2 * len(items)))
        print("answer requests to issue: %d now, plus up to %d RankGPT answers once their o0 rankings arrive "
              "(%d planned in all; total planned %d)" % (n_ans, 3 * waiting, 24 * len(items), 26 * len(items)))
        if not mock:
            names = credential_vars(Q.ANSWER_MODELS)
            miss = set(missing_credentials(Q.ANSWER_MODELS))
            print("credentials (names only): set %s; not set %s" % (
                [v for v in names if v not in miss] or "none", sorted(miss) or "none"))
        print("dry run: no request was made")
        return 0
    if not mock and free < MIN_FREE_START:
        raise SystemExit("live run refused: %.0f MB free on the records' drive (%s); at least %d MB are required" % (
            free / MB, rel(out_dir), MIN_FREE_START // MB))
    runner = Runner(out_dir, mock, lanes)
    runner.start()
    try:
        if "rank" in phases:
            reqs = rank_requests(items)
            for r in reqs:
                r["prompt"] = Q.rank_prompt(by_id[r["item"]], r["pool"])
            runner.execute(reqs, st, by_id)
            st = Q.load_records(rec_path)
        if "answer" in phases and not runner.stop.is_set():
            rankings = dict(local)
            rankings.update(Q.rankgpt_rankings(st, by_id))
            runner.execute(answer_requests(items, rankings), st, by_id)
    finally:
        runner.finish()
    summary(mode, out_dir, items)
    if runner.stop_reason or runner.unsaved:
        print("run stopped (%s); rerun the same command to resume" % runner.stop_reason)
        return 2
    return 0


# ---- summary (counts; analyze_fullwiki.py gives the analysis) ----------------------------------
def summary(mode, out_dir, items=None):
    rec_path = Path(out_dir) / "records.jsonl"
    st = Q.load_records(rec_path)
    R = st["receipt"]
    if items is None:
        items = load_items(mode)
        if mode == "smoke":
            seen = {i.split("|")[2] for i in st["issued"]}
            items = [it for it in items if it["id"] in seen]
    by_id = {it["id"]: it for it in items}
    halts = []
    if rec_path.exists():
        for line in open(rec_path, encoding="utf-8"):
            if '"halt"' in line:
                try:
                    halts.append(json.loads(line)["reason"])
                except (ValueError, KeyError):
                    pass
    kinds = Counter((r.split("|")[0]) for r in st["issued"])
    got = Counter(rc["kind"] for rc in R.values())
    failed = [rc for rc in R.values() if rc.get("transport_failed")]
    cls = Counter(failure_class(rc) for rc in failed)
    L = ["%s: %d questions; records %s" % (mode, len(items), rel(rec_path)),
         "ranking requests: planned %d, issued %d, received %d" % (2 * len(items), kinds["rank"], got["rank"]),
         "answer requests: planned up to %d, issued %d, received %d" % (24 * len(items), kinds["ans"], got["answer"]),
         "transport failures: %d (HTTP 400 on every attempt %d, other %d); interrupted (issued, no receipt) %d" % (
             len(failed), cls["http400"], cls["other"], sum(1 for i in st["issued"] if i not in R))]
    if halts:
        L.append("halts: %d (last: %s)" % (len(halts), halts[-1]))
    ranks = [rc for rc in R.values() if rc.get("kind") == "rank" and not rc.get("transport_failed")]
    if ranks:
        comp = sum(Q.parse_ranking(rc.get("raw_text"), len(rc["pool"]))[1]["complete"] for rc in ranks)
        L.append("RankGPT complete parses %d/%d" % (comp, len(ranks)))
    acc, fmt = defaultdict(list), defaultdict(lambda: [0, 0])
    for rc in R.values():
        if rc.get("kind") == "answer" and not rc.get("transport_failed") and rc["item"] in by_id:
            acc[(rc["model"], rc["cond"])].append(Q.score(rc.get("raw_text"), by_id[rc["item"]]["answers"])[1])
            fmt[rc["model"]][0] += 1
            fmt[rc["model"]][1] += bool(ANSWER_LINE.search(rc.get("raw_text") or ""))
    if acc:
        L.append("mean F1 (n) by answer model and condition; intervals and contrasts: analyze_fullwiki.py")
        L.append("  %-16s" % "" + "".join("%13s" % c for c in CONDITIONS))
        for m in Q.ANSWER_MODELS:
            L.append("  %-16s" % m + "".join("%13s" % ("%.2f (%d)" % (sum(v) / len(v), len(v)) if v else "-")
                                             for v in (acc.get((m, c), []) for c in CONDITIONS)))
        L.append("answer-line compliance: " + "; ".join("%s %d/%d" % (m, v[1], v[0]) for m, v in fmt.items()))
    text = "\n".join(L)
    if Path(out_dir).exists():
        write_lf(Path(out_dir) / "summary.txt", text + "\n")
    print(text)
    return text


def main():
    ap = argparse.ArgumentParser(description="Package 3 runner (PROTOCOL_FULLWIKI.md); see the module docstring.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--mock", action="store_true", help="fabricated replies, no network, no keys")
    g.add_argument("--smoke", type=int, metavar="N", help="real run on the first N smoke items")
    g.add_argument("--confirm", action="store_true", help="the confirmatory run (requires a verified freeze)")
    ap.add_argument("--phase", choices=("all", "local", "rank", "answer"), default="all")
    ap.add_argument("--lanes", type=int, default=LANES, help="concurrent requests per model (default 4)")
    ap.add_argument("--dry-run", action="store_true", help="check freeze, disk and credentials; send nothing")
    ap.add_argument("--summary", action="store_true", help="print the counts of a record directory")
    ap.add_argument("--out", default=None, help="record directory for --mock or --smoke (never the confirmatory one)")
    a = ap.parse_args()
    if a.phase == "local":
        if a.mock or a.confirm or a.smoke is not None:
            ap.error("--phase local takes no mode: it ranks the confirmatory and smoke items once, before the freeze")
        return local_phase()
    mode = "mock" if a.mock else "smoke" if a.smoke is not None else "confirm" if a.confirm else None
    if mode is None:
        ap.error("choose one of --mock, --smoke N, --confirm")
    n_smoke = sum(1 for l in open(SETS["smoke"]["items"], encoding="utf-8") if l.strip())
    if mode == "smoke" and not 1 <= a.smoke <= n_smoke:
        ap.error("--smoke N takes 1 <= N <= %d" % n_smoke)
    if a.out and mode == "confirm":
        ap.error("--out is for --mock and --smoke only")
    out = Path(a.out) if a.out else SETS[mode]["out"]
    if mode != "confirm" and out.resolve() == SETS["confirm"]["out"].resolve():
        ap.error("mock and smoke runs never write into the confirmatory directory")
    if a.lanes < 1:
        ap.error("--lanes must be at least 1")
    if a.summary:
        summary(mode, out)
        return 0
    phases = ("rank", "answer") if a.phase == "all" else (a.phase,)
    return run(mode, out, n=a.smoke if mode == "smoke" else None, lanes=a.lanes, phases=phases, dry_run=a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
