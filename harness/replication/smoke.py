r"""Live verification of the replication harness on one model, kept apart from the replication.

It copies design.json and keeps one model (default Haiku-4.5, the cheapest), one window that opens
now and closes after --minutes, and --blocks blocks per task (16 requests at the default 2), with a
call budget of three attempts per request. It freezes that copy in its own directory (the code
need not be committed: this is a plumbing check, not the replication), runs the window in strict
mode through the real transport, closes it, analyses it with the freeze check, and prints what a
live run must show: every request received, HTTP statuses, the provider's model field, response
ids, usage and stop reasons, latency, PASS by condition under both graders, and calls used.

The output goes to results/replication/smoke/<UTC time>/ and never enters the replication's
analysis, which reads results/replication/records only.

Usage:  python harness/replication/smoke.py [--model Haiku-4.5] [--blocks 2] [--minutes 45]
        python harness/replication/smoke.py --mock          (canned replies, no network)
The model's endpoint and key come from its variables in design.json (BW_ENDPOINT_HAIKU and
BW_KEY_HAIKU for Haiku-4.5); they are read from the environment and never printed.
"""
import argparse
import copy
import io
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import freeze as frz  # noqa: E402
import records  # noqa: E402
import run_replication as rr  # noqa: E402


def main(model="Haiku-4.5", blocks=2, minutes=45, mock=False, out_root=None):
    design = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
    cfg = next((m for m in design["models"] if m["label"] == model), None)
    if cfg is None:
        raise SystemExit("no model %r in design.json" % model)
    if not mock:
        missing = [v for v in (cfg["endpoint_env"], cfg["key_env"]) if not os.environ.get(v)]
        if missing:
            raise SystemExit("set %s in the environment first (values are never printed)" % " and ".join(missing))
    now = datetime.now(timezone.utc).replace(microsecond=0)
    d = copy.deepcopy(design)
    d["purpose"] = "Live plumbing check on one model; not part of the replication."
    d["models"] = [cfg]
    d["windows"] = [{"id": "smoke", "start": (now - timedelta(minutes=1)).isoformat(),
                     "end": (now + timedelta(minutes=minutes)).isoformat()}]
    d["blocks_per_window"] = blocks
    d["budget"] = dict(d["budget"], max_api_calls=3 * frz.n_requests(d))
    for k in ("windows_note", "blocks_per_window_note"):
        d.pop(k, None)
    out = os.path.join(out_root or os.path.join(ROOT, "results", "replication", "smoke"),
                       now.strftime("%Y%m%dT%H%M%SZ") + "-" + model + ("-mock" if mock else ""))
    os.makedirs(out, exist_ok=True)
    dp = os.path.join(out, "design.json")
    json.dump(d, open(dp, "w", encoding="utf-8", newline="\n"), indent=2)
    frz.freeze(design_path=dp, out_dir=out, root=ROOT, allow_dirty=True)
    rec_dir = os.path.join(out, "records")
    try:
        rr.run_window("smoke", mock=mock, strict=True, design_path=dp, sched_dir=out, out_dir=rec_dir,
                      grade_fn=None)
    except RuntimeError as e:             # a halted model: close the check and report what failed
        print("collection stopped: %s" % e)
        rr.run_window("smoke", mock=mock, strict=False, design_path=dp, sched_dir=out, out_dir=rec_dir,
                      grade_fn=None, close=True)
    doc = analyze.main(design_path=dp, base=out, records_dir=rec_dir, check_freeze=True, write=True)
    return report(d, rec_dir, doc, out)


def report(d, rec_dir, doc, out):
    st = records.read_dir(rec_dir)
    rcs = sorted(st["receipts"].values(), key=lambda r: (r["lane"], r["actual_seq"]))
    ok = [r for r in rcs if not r["transport_failed"]]
    t = lambda s: datetime.fromisoformat(s)
    lat = sorted((t(r["end_utc"]) - t(r["start_utc"])).total_seconds() for r in rcs)
    http = Counter(a["http_status"] for r in rcs for a in r["attempts"])
    meta_gaps = [r["schedule_id"] for r in ok if not (r["response_id"] and r["usage"] and r["stop_reason"])]
    use = lambda r, *keys: next(((r["usage"] or {}).get(k) for k in keys if (r["usage"] or {}).get(k)), 0)
    ins = sum(use(r, "input_tokens", "prompt_tokens") for r in ok)          # Messages/Responses, chat
    outs = sum(use(r, "output_tokens", "completion_tokens") for r in ok)
    cells = defaultdict(lambda: [0, 0, 0])
    for sid, g in st["grades"].items():
        c = cells[(g["task"], g["condition"])]
        c[0] += g["pass_published"]
        c[1] += g["pass_current"]
        c[2] += 1
    checks = [
        ("every scheduled request was issued and received", doc["request_status"]["graded"] + doc["request_status"]["failed"] == doc["n_scheduled"]),
        ("no transport failure", doc["request_status"]["failed"] == 0),
        ("every received response was graded", doc["request_status"]["ungraded"] == 0),
        ("the provider returned a model field on every response", all(r["returned_model"] for r in ok)),
        ("response id, usage and stop reason kept on every response", not meta_gaps),
        ("analysis is final (window closed, freeze holds, records match the design)", doc["status"] == "final"),
        ("calls used within the budget", doc["calls_used"] <= d["budget"]["max_api_calls"]),
    ]
    lines = ["# Live verification: %s, %d requests" % (d["models"][0]["id"], doc["n_scheduled"]), ""]
    lines += ["- %s: %s" % (label, "yes" if good else "NO") for label, good in checks]
    errs = Counter((a["http_status"], (a.get("error_body") or a.get("error") or "").strip()[:240])
                   for r in rcs for a in r["attempts"] if a.get("error"))
    if errs:
        lines += ["", "Failed attempts (status and the provider's reason):"]
        lines += ["- %dx HTTP %s: %s" % (n, s, m) for (s, m), n in errs.most_common(5)]
    lines += ["", "HTTP statuses of all attempts: %s" % dict(http),
              "Model field returned: %s (requested %s)" % (dict(Counter(r["returned_model"] for r in ok)), d["models"][0]["id"]),
              "Stop reasons: %s" % dict(Counter(r["stop_reason"] for r in ok)),
              "Response fields kept: %s" % (", ".join(sorted({k for r in ok for k in (r.get("response") or {})}))
                                            or "none"),
              "Backend fingerprint: %s" % (lambda f: dict(f) if any(f) else "not sent by the provider")(
                  Counter((r.get("response") or {}).get("system_fingerprint") for r in ok)),
              "Endpoint as recorded: %s" % ", ".join(sorted({r["endpoint_host"] for r in rcs})),
              "Latency per request (s): median %.1f, max %.1f" % (lat[len(lat) // 2], lat[-1]) if lat else "no latency",
              "Tokens: %d input, %d output (%.0f output per request)" % (ins, outs, outs / max(1, len(ok))),
              "Calls used: %d of %d" % (doc["calls_used"], d["budget"]["max_api_calls"]),
              "Graders agree on %d of %d graded replies" % tuple(doc["grader_agreement"]), "",
              "| Task | Condition | PASS (published grader) | PASS (current grader) |", "|---|---|---|---|"]
    for (task, cond), (p, c, n) in sorted(cells.items()):
        lines.append("| %s | %s | %d/%d | %d/%d |" % (task, cond, p, n, c, n))
    lines += ["", "Records, schedule, freeze and analysis: %s" % os.path.relpath(out, ROOT).replace(os.sep, "/"),
              "This check is not part of the replication and never enters its analysis."]
    text = "\n".join(lines) + "\n"
    open(os.path.join(out, "VERIFICATION.md"), "w", encoding="utf-8", newline="\n").write(text)
    print(text)
    return all(good for _l, good in checks)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Haiku-4.5")
    ap.add_argument("--blocks", type=int, default=2)
    ap.add_argument("--minutes", type=int, default=45)
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if main(a.model, a.blocks, a.minutes, a.mock) else 1)
