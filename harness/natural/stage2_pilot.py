r"""Stage 2 of the natural-data evaluation: a small exploratory pilot. It tests the measurement
(requests, scoring, leakage, floor and ceiling), not the hypotheses; its items are development data.

  build   items from the Stage 1 audit, and a shuffled schedule per model (seed fixed)
  run     collect: two models, five conditions, three draws; needs each model's BW_ENDPOINT_* and
          BW_KEY_* (as for the replication); --mock uses canned replies and no network
  report  score every saved reply (scoring.py) and write the measurement report

Conditions: none (closed book), A alone, B alone, A then B, B then A. A is the TAT-QA table or the
first HotpotQA gold paragraph; B the TAT-QA text or the second paragraph. The request is the
replication's (transport.post: one user message, 8000 output tokens, provider-default decoding).
Every response is saved before it is scored; a run resumes without sending a request twice; a call
cap and a halt after three consecutive transport failures protect the budget.

Usage:  python harness/natural/stage2_pilot.py build
        python harness/natural/stage2_pilot.py run [--mock]
        python harness/natural/stage2_pilot.py report [--mock]
"""
import hashlib
import io
import json
import os
import random
import sys
import threading
from collections import Counter, defaultdict

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "harness", "replication"))
import records  # noqa: E402
import scoring  # noqa: E402
import transport  # noqa: E402
from transport import utc_now  # noqa: E402

S1 = os.path.join(ROOT, "natural_data", "stage1")
S2 = os.path.join(ROOT, "natural_data", "stage2")
SEED = 20261003
DRAWS = 3
CAP = 3000
CONDITIONS = ("none", "A", "B", "AB", "BA")
MODELS = [{"label": "Haiku-4.5", "id": "claude-haiku-4-5", "endpoint_env": "BW_ENDPOINT_HAIKU", "key_env": "BW_KEY_HAIKU"},
          {"label": "DeepSeek-V4-Pro", "id": "DeepSeek-V4-Pro", "endpoint_env": "BW_ENDPOINT_DEEPSEEK", "key_env": "BW_KEY_DEEPSEEK"}]
INSTR = ("Answer with only the answer: a number with its unit or scale, or a short phrase. If the question "
         "asks for a description or a reason, answer in one sentence using the wording of the context.")


def build():
    s = json.load(open(os.path.join(S1, "sample.json"), encoding="utf-8"))
    a = json.load(open(os.path.join(S1, "audit.json"), encoding="utf-8"))
    items = []
    tat = {f"T{k:02d}": it for k, it in enumerate(s["tatqa"])}
    for r in a["tatqa"]:
        if not r["verdict"].startswith("keep"):
            continue
        doc = tat[r["item"]]
        q = doc["questions"][r["kind"]]
        if r["verdict"].startswith("keep-f1"):
            kind = "long"
        elif q["answer_type"] in ("arithmetic", "count"):
            kind = "number"
        elif q["answer_type"] == "multi-span":
            kind = "multi"
        else:
            kind = "span"
        own = {"table": "A", "text": "B", "table-text": "AB"}[r["kind"]]
        items.append({"id": "%s-%s" % (r["item"], r["kind"]), "dataset": "tatqa", "task": r["kind"], "own": own,
                      "question": q["question"], "gold": q["answer"], "scale": q["scale"], "score_kind": kind,
                      "A": "Table:\n" + doc["table"], "B": "Text:\n" + doc["text"]})
    hot = {f"H{k:02d}": it for k, it in enumerate(s["hotpotqa"])}
    for r in a["hotpotqa"]:
        it = hot[r["item"]]
        A = "%s\n%s" % (it["gold_titles"][0], it["paragraphs"][it["gold_titles"][0]])
        B = "%s\n%s" % (it["gold_titles"][1], it["paragraphs"][it["gold_titles"][1]])
        pair_ok = len(r["subquestions"]) == 2 and all(q["verdict"] == "keep" for q in r["subquestions"])
        if pair_ok:
            for j, q in enumerate(r["subquestions"]):
                items.append({"id": "%s-sq%d" % (r["item"], j + 1), "dataset": "hotpotqa", "task": "single-%s" % it["type"],
                              "own": "AB"[j], "question": q["question"], "gold": q["aliases"], "scale": "",
                              "score_kind": "aliases", "A": A, "B": B})
        if r["original_verdict"].startswith("keep"):
            items.append({"id": "%s-orig" % r["item"], "dataset": "hotpotqa", "task": "original-%s" % it["type"],
                          "own": "AB", "question": it["question"], "gold": it["answer"], "scale": "",
                          "score_kind": "long" if r["original_verdict"].startswith("keep-f1") else "span", "A": A, "B": B})
    # every gold must pass its own scorer
    bad = []
    for it in items:
        g = it["gold"]
        reply = (g[0] if isinstance(g, list) and it["score_kind"] in ("aliases", "span") else
                 " and ".join(map(str, g)) if isinstance(g, list) else str(g))
        if not scoring.score(reply, g, it["score_kind"], it["scale"])[0]:
            bad.append(it["id"])
    os.makedirs(S2, exist_ok=True)
    json.dump(items, open(os.path.join(S2, "items.json"), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    rng = random.Random(SEED)
    rows = []
    for m in MODELS:
        mine = [{"schedule_id": "%s|%s|%s|%d" % (m["label"], it["id"], c, d), "window": "pilot", "model": m["label"],
                 "item": it["id"], "condition": c, "draw": d} for it in items for c in CONDITIONS for d in range(DRAWS)]
        rng.shuffle(mine)
        for k, r in enumerate(mine):
            r["seq"], r["lane"] = k, k % 2
        rows += mine
    with open(os.path.join(S2, "schedule.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print("items: %d (%s); requests: %d (%d per model); gold self-check failures: %s" % (
        len(items), dict(Counter(i["dataset"] for i in items)), len(rows), len(rows) // len(MODELS), bad or "none"))
    return items, rows


def prompt(it, cond):
    srcs = {"none": [], "A": [it["A"]], "B": [it["B"]], "AB": [it["A"], it["B"]], "BA": [it["B"], it["A"]]}[cond]
    ctx = ("Context:\n\n" + "\n\n".join(srcs) + "\n\n") if srcs else ""
    return ctx + "Question: " + it["question"] + "\n" + INSTR


def mock_reply(it, cond, rng):
    g = it["gold"]
    right = g[0] if isinstance(g, list) else g
    right = " and ".join(map(str, g)) if it["score_kind"] == "multi" else right
    p = 0.85 if (cond in ("AB", "BA") or cond == it["own"] or (it["own"] == "AB" and cond != "none")) else 0.05
    if it["own"] == "AB" and cond in ("A", "B"):
        p = 0.3
    return str(right) if rng.random() < p else "I cannot determine this from the context."


def run(mock=False):
    items = {i["id"]: i for i in json.load(open(os.path.join(S2, "items.json"), encoding="utf-8"))}
    rows = [json.loads(l) for l in open(os.path.join(S2, "schedule.jsonl"), encoding="utf-8") if l.strip()]
    out_dir = os.path.join(S2, "records_mock" if mock else "records")
    os.makedirs(out_dir, exist_ok=True)
    eps = {}
    for m in MODELS:
        ep, key = os.environ.get(m["endpoint_env"]), os.environ.get(m["key_env"])
        if not mock and not (ep and key):
            sys.exit("no endpoint or key for %s (set %s and %s)" % (m["label"], m["endpoint_env"], m["key_env"]))
        eps[m["label"]] = (ep, key)
    lock_p = os.path.join(out_dir, ".run.lock")
    try:
        fd = os.open(lock_p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        sys.exit("another run holds %s; if none is running, delete it" % lock_p)
    path = os.path.join(out_dir, "pilot.jsonl")
    st = records.read_dir(out_dir)
    ledger = [records.calls_used(st)]
    lock = threading.Lock()
    fh = open(path, "a", encoding="utf-8", newline="\n")

    def write(rec):
        with lock:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def allow():
        with lock:
            if ledger[0] >= CAP:
                return False
            ledger[0] += 1
            return True

    fails, halted, errors = Counter(), set(), []

    def worker(m, lane):
        rng = random.Random("%s|%d" % (m["label"], lane))
        ep, key = eps[m["label"]]
        try:
            for r in sorted((r for r in rows if r["model"] == m["label"] and r["lane"] == lane), key=lambda r: r["seq"]):
                sid = r["schedule_id"]
                if sid in st["issued"] or sid in st["receipts"] or m["label"] in halted:
                    continue
                if not allow():
                    return
                it = items[r["item"]]
                text = prompt(it, r["condition"])
                iss = {"type": "issued", "schedule_id": sid, "window": "pilot", "model": m["label"], "utc": utc_now()}
                write(iss)
                st["issued"][sid] = iss
                first = [True]

                def allow_row():
                    if first[0]:
                        first[0] = False
                        return True
                    return allow()

                if mock:
                    resp = {"text": mock_reply(it, r["condition"], rng), "returned_model": m["id"], "response_id": "mock",
                            "usage": {}, "stop_reason": "end_turn", "response": None, "transport_failed": False,
                            "attempts": [{"attempt": 1, "http_status": 200, "error": None}]}
                else:
                    resp = transport.post(text, m["id"], ep, key, allow_attempt=allow_row)
                rc = dict(r, type="receipt", start_utc=iss["utc"], end_utc=utc_now(), requested_model=m["id"],
                          prompt_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                          returned_model=resp["returned_model"], response_id=resp["response_id"], usage=resp["usage"],
                          stop_reason=resp["stop_reason"], attempts=resp["attempts"],
                          transport_failed=resp["transport_failed"], raw_text=resp["text"], response=resp.get("response"))
                write(rc)
                st["receipts"][sid] = rc
                with lock:
                    fails[m["label"]] = fails[m["label"]] + 1 if resp["transport_failed"] else 0
                    if fails[m["label"]] >= 3:
                        halted.add(m["label"])
        except Exception as e:  # noqa: BLE001
            errors.append("%s lane %d: %s: %s" % (m["label"], lane, type(e).__name__, e))

    try:
        threads = [threading.Thread(target=worker, args=(m, j)) for m in MODELS for j in (0, 1)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        fh.close()
        os.remove(lock_p)
    got = Counter(x["model"] for x in st["receipts"].values())
    print("pilot: %s received of %d each; calls used %d of %d%s%s" % (dict(got), len(rows) // len(MODELS), ledger[0], CAP,
          "; HALTED %s" % sorted(halted) if halted else "", "; ERRORS %s" % errors if errors else ""))
    if errors or halted:
        sys.exit(1)


def report(mock=False):
    items = {i["id"]: i for i in json.load(open(os.path.join(S2, "items.json"), encoding="utf-8"))}
    st = records.read_dir(os.path.join(S2, "records_mock" if mock else "records"))
    rows = []
    for rc in st["receipts"].values():
        it = items[rc["item"]]
        ok, f = (False, None) if rc["transport_failed"] else scoring.score(rc["raw_text"], it["gold"], it["score_kind"], it["scale"])
        rows.append(dict(model=rc["model"], item=rc["item"], dataset=it["dataset"], task=it["task"], own=it["own"],
                         cond=rc["condition"], ok=ok, f1=f, failed=rc["transport_failed"], kind=it["score_kind"],
                         reply=rc["raw_text"], gold=it["gold"], stop=rc["stop_reason"]))
    rel = lambda r: ("own" if r["cond"] == r["own"] else "none" if r["cond"] == "none" else
                     "both" if r["cond"] in ("AB", "BA") else "other")
    lines = ["# Stage 2 pilot: measurement report%s" % (" (MOCK DATA)" if mock else ""), "",
             "Development data: these numbers check the measurement and are not evidence for or against the claims.", ""]
    lines += ["Responses scored: %d; transport failures: %d; stop reasons: %s" % (
        len(rows), sum(r["failed"] for r in rows), dict(Counter(r["stop"] for r in rows))), ""]
    lines += ["## PASS rate by source condition (own = the source that holds the answer)", "",
              "| Model | Dataset | Task | none | own | other | both |", "|---|---|---|---|---|---|---|"]
    agg = defaultdict(lambda: [0, 0])
    for r in rows:
        if not r["failed"]:
            a = agg[(r["model"], r["dataset"], r["task"], rel(r) if r["own"] != "AB" else ("none" if r["cond"] == "none" else
                     "both" if r["cond"] in ("AB", "BA") else "other"))]
            a[0] += r["ok"]
            a[1] += 1
    for key in sorted({k[:3] for k in agg}):
        cells = []
        for c in ("none", "own", "other", "both"):
            v = agg.get(key + (c,))
            cells.append("%d/%d" % tuple(v) if v else "-")
        lines.append("| %s | %s | %s | %s |" % (key[0], key[1], key[2], " | ".join(cells)))
    leak = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["cond"] == "none" and not r["failed"]:
            leak[(r["model"], r["item"])][0] += r["ok"]
            leak[(r["model"], r["item"])][1] += 1
    leaky = sorted("%s %s %d/%d" % (k[0], k[1], v[0], v[1]) for k, v in leak.items() if v[0] >= 2)
    lines += ["", "## Closed-book leakage (no context, at least 2 of 3 draws pass)", "", ", ".join(leaky) or "none"]
    num = [r for r in rows if r["kind"] == "number" and not r["failed"]]
    unparsed = [r for r in num if not scoring.numbers_in(r["reply"] or "")]
    lines += ["", "## Format", "", "numeric replies without any number: %d of %d" % (len(unparsed), len(num))]
    f1s = [r["f1"] for r in rows if r["f1"] is not None and rel(r) in ("own", "both")]
    if f1s:
        f1s.sort()
        lines += ["long answers with the answering source present: median F1 %.2f, %d of %d at or above %.1f" % (
            f1s[len(f1s) // 2], sum(v >= scoring.F1_THRESHOLD for v in f1s), len(f1s), scoring.F1_THRESHOLD)]
    rng = random.Random(7)
    sample = rng.sample(rows, min(24, len(rows)))
    lines += ["", "## Random replies for a manual scoring check", "", "| Item | Model | Cond | PASS | Gold | Reply |", "|---|---|---|---|---|---|"]
    for r in sample:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (r["item"], r["model"], r["cond"], "yes" if r["ok"] else "no",
                     str(r["gold"])[:60].replace("|", "/"), str(r["reply"])[:90].replace("|", "/").replace("\n", " ")))
    tag = "_mock" if mock else ""
    open(os.path.join(S2, "REPORT%s.md" % tag), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    json.dump(rows, open(os.path.join(S2, "scored%s.json" % tag), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    mock = "--mock" in sys.argv
    {"build": build, "run": lambda: run(mock), "report": lambda: report(mock)}.get(cmd, lambda: sys.exit(__doc__))()
