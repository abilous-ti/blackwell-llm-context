r"""Audit of the replication's stored responses: the figures reported in the manuscript's
replication audit (Section 5.6 and Appendix B.2). Reads the records only; makes no model call.

Reported:
  1. retention: for every graded observation, the raw reply text, response envelope, returned
     model field, response identifier, stop reason, transport attempts and prompt hash;
  2. replies that stopped at the output limit, and those among them with empty final text;
  3. syntactic validity (ast.parse) of the extracted code of the augmented (W1plus) responses on
     the two API tasks, and empty extractions;
  4. agreement of the primary (published) and current graders;
  5. returned model fields; API attempts and reported token usage;
  6. output-token inflation of the W1plus arm over W1 on the two API tasks.

Usage:  python harness/replication/audit_responses.py [records_dir]
"""
import ast
import io
import json
import os
import sys
from collections import Counter, defaultdict

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import records  # noqa: E402

FIELDS = ("raw_text", "response", "returned_model", "response_id", "stop_reason", "attempts", "prompt_sha256")
LIMIT_STOPS = ("length", "max_tokens", "max_output_tokens", "incomplete")


def main(records_dir=None):
    st = records.read_dir(records_dir or os.path.join(ROOT, "results", "replication", "records"))
    R, G = st["receipts"], st["grades"]
    graded = sorted(s for s in G if s in R and not R[s]["transport_failed"])
    print("graded observations: %d (receipts %d, issued %d)" % (len(graded), len(R), len(st["issued"])))

    # 1. retention
    missing = Counter(f for s in graded for f in FIELDS if R[s].get(f) is None)
    print("1. graded observations lacking a retained field: %s" % (dict(missing) or "none"))
    no_usage = [s for s in graded if not R[s].get("usage")]
    no_stop = [s for s in graded if not R[s].get("stop_reason")]
    print("   without a usage count: %s; without a stop reason: %s" % (no_usage or "none", no_stop or "none"))

    # 2. output-limit stops and empty final text
    limit, empty = Counter(), Counter()
    limit_pass = 0
    for s in graded:
        r = R[s]
        key = (r["model"], r["task"], r["condition"])
        if r["stop_reason"] in LIMIT_STOPS:
            limit[key] += 1
            limit_pass += bool(G[s]["pass_published"])
            if not r["raw_text"].strip():
                empty[key] += 1
    print("2. replies stopped at the output limit: %d (passing: %d); with empty final text: %d" % (
        sum(limit.values()), limit_pass, sum(empty.values())))
    for k in sorted(limit):
        print("   %-40s limit %3d  empty %3d" % ("|".join(k), limit[k], empty[k]))
    other_empty = sum(1 for s in graded if not R[s]["raw_text"].strip()
                      and R[s]["stop_reason"] not in LIMIT_STOPS)
    print("   empty final text without an output-limit stop: %d" % other_empty)

    # 3. syntax of the augmented API responses
    aug = [s for s in graded if R[s]["condition"] == "W1plus" and R[s]["task"] in ("api_post_ok", "api_argorder")]
    bad, blank = [], 0
    for s in aug:
        code = G[s].get("code") or ""
        blank += not code.strip()
        try:
            ast.parse(code)
        except SyntaxError as e:
            bad.append((s, "%s (line %s)" % (e.msg, e.lineno)))
    print("3. augmented API responses: %d; syntactically valid: %d; empty extraction: %d" % (
        len(aug), len(aug) - len(bad), blank))
    for s, why in bad:
        print("   does not parse: %s  %s" % (s, why))

    # 4. grader agreement
    dis = [s for s in graded if G[s]["pass_published"] != G[s]["pass_current"]]
    print("4. graders agree on %d of %d" % (len(graded) - len(dis), len(graded)))
    for s in dis:
        print("   differ: %s  published=%s current=%s" % (s, G[s]["pass_published"], G[s]["pass_current"]))

    # 5. returned model fields, attempts, tokens
    ret = defaultdict(Counter)
    for s in graded:
        ret[R[s]["requested_model"]][R[s]["returned_model"]] += 1
    print("5. returned model field by requested model:")
    for m in sorted(ret):
        print("   %-20s %s" % (m, dict(ret[m])))
    design = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
    cap = design.get("retry_policy", {}).get("max_attempts", 3)
    attempts = sum(len(r["attempts"]) for r in R.values())
    retried = sum(1 for r in R.values() if len(r["attempts"]) > 1)
    interrupted = sum(1 for s in st["issued"] if s not in R)
    tin = sum((r.get("usage") or {}).get("input_tokens", (r.get("usage") or {}).get("prompt_tokens", 0)) or 0
              for r in R.values())
    tout = sum((r.get("usage") or {}).get("output_tokens", (r.get("usage") or {}).get("completion_tokens", 0)) or 0
               for r in R.values())
    print("   attempts recorded for stored responses: %d (requests retried: %d); interrupted requests: %d "
          "(at most %d attempts each); at most %d attempts in all" % (
              attempts, retried, interrupted, cap, attempts + cap * interrupted))
    print("   reported tokens: input %d, output %d" % (tin, tout))

    # 6. output-token inflation of the augmented arm on the two API tasks (Appendix B.3)
    out = defaultdict(list)
    for r in R.values():
        u = r.get("usage") or {}
        o = u.get("output_tokens", u.get("completion_tokens"))
        if o is not None:
            out[(r["model"], r["task"], r["condition"])].append(o)
    ratios = []
    print("6. mean output tokens, W1 -> W1plus:")
    for m in sorted({k[0] for k in out}):
        cells = []
        for t in ("api_post_ok", "api_argorder"):
            a, b = out[(m, t, "W1")], out[(m, t, "W1plus")]
            if a and b:
                pct = 100.0 * (sum(b) / len(b)) / (sum(a) / len(a)) - 100.0
                ratios.append(pct)
                cells.append("%s %+.0f%%" % (t, pct))
        print("   %-16s %s" % (m, "; ".join(cells)))
    if ratios:
        print("   range over the cells: %+.0f%% to %+.0f%%" % (min(ratios), max(ratios)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
