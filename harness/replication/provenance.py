r"""Provenance of the original (published) measurements, rebuilt from the evidence the repository
actually holds: run logs, result JSONs, retained completions and git history.

What counts as evidence, and what does not:
  * the order in which a run log prints its cell lines is a direct record of the order in which the
    cells COMPLETED (the driver prints each line when its cell finishes);
  * the order of draws inside a cell, the worker count and every request time were never recorded;
    the arm-major loop in the driver (harness/measure_blackwell.py, measure()) is inferred, not observed,
    and whether a cell's draws were sent one after another or concurrently depends on the driver's
    --workers option (default 1), whose value no log records, so concurrency is not established;
  * a field a script filled in itself is not provider metadata: the audit driver's model_served is a
    copy of the requested deployment name (harness/diag/audit_any.py, complete());
  * a git commit time is an upper bound on when a record existed, never a request time; file
    modification times are not used at all (a checkout rewrites them).

Usage:  python harness/replication/provenance.py
Writes results/replication/provenance_original.md and .json.
"""
import hashlib, io, json, os, re, subprocess, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "replication")

# Each record the manuscript's tables are computed from, with the harness commit that produced it.
# The pin is evidence-based: the July records were added in the first commit, whose client is the
# generic HTTP one for non-Claude models; the Anthropic HTTP records were finalised in 5a5dbcc, the
# commit that introduced the HTTP path for Claude models and the [HTTP-API] log marker.
RECORDS = [
    # label, result stem, requested model as logged, harness commit, interface (from the code path)
    ("Haiku-4.5 grid", "blackwell_haiku_api_n40", "5a5dbcc", "Anthropic Messages API (HTTP)"),
    ("Sonnet-4.6 grid", "blackwell_sonnet_api_n40", "5a5dbcc", "Anthropic Messages API (HTTP)"),
    ("Opus-4.8 grid", "blackwell_opus_api_n40", "5a5dbcc", "Anthropic Messages API (HTTP)"),
    ("GPT-5.5 grid", "blackwell_gpt55_n40", "65e6843", "Azure-hosted endpoint, generic client (URL not logged)"),
    ("DeepSeek-V4-Pro grid", "blackwell_deepseek_n40", "65e6843", "Azure-hosted endpoint, generic client (URL not logged)"),
    ("Kimi-K2.6 grid", "blackwell_kimi_n40", "65e6843", "Azure-hosted endpoint, generic client (URL not logged)"),
    ("Haiku controls", "blackwell_controls_api_n40", "5a5dbcc", "Anthropic Messages API (HTTP)"),
    ("Haiku second pair", "blackwell_pair2_api_n40", "5a5dbcc", "Anthropic Messages API (HTTP)"),
]
AUDIT_GPT_TRAP = "audit/audit_gpt55_trap_store_wire"


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def added_and_last(path):
    log = git("log", "--format=%h %ad", "--date=iso", "--", path).strip().split("\n")
    log = [l for l in log if l.strip()]
    return (log[-1], log[0]) if log else ("", "")


def log_facts(stem):
    p = os.path.join(RES, stem + ".log")
    if not os.path.exists(p):
        return {}
    txt = open(p, encoding="utf-8", errors="replace").read()
    head = txt.split("\n")[0]
    m_model = re.search(r"model = (\S+)", txt)
    cells = re.findall(r"^\s*arm=(\S+)\s+(\S+)\s+PASS", txt, re.M)
    arm_order = []
    for a, _t in cells:
        if not arm_order or arm_order[-1] != a:
            arm_order.append(a)
    return {
        "header": head,
        "requested_model": m_model.group(1) if m_model else "",
        "markers": [m for m in ("[HTTP-API]", "[RETAIN]", "[SINGLE-SHOT]") if m in txt],
        "n_cells_logged": len(cells),
        "cell_completion_order": ["%s|%s" % c for c in cells],
        "arm_blocks_in_log_order": arm_order,
        "arm_major": len(arm_order) == len(set(arm_order)),
        "timestamps_in_log": bool(re.search(r"\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T", txt)),
        "workers_in_log": bool(re.search(r"worker", txt, re.I)),
    }


def retained(stem):
    d = json.load(open(os.path.join(RES, stem + ".json"), encoding="utf-8"))
    out = ["per-cell counts"]
    if "draws" in d:
        out.append("per-draw PASS by draw index (not by time)")
    if "errs" in d:
        out.append("per-draw transport-error flags")
    if "runtime_tokens" in d:
        out.append("mean output tokens per cell")
    model_dir = {"blackwell_haiku_api_n40": "haiku", "blackwell_sonnet_api_n40": "sonnet",
                 "blackwell_opus_api_n40": "opus"}.get(stem)
    if model_dir:
        rdir = os.path.join(RES, "retain_api", model_dir)
        n = len(os.listdir(rdir)) if os.path.isdir(rdir) else 0
        out.append("raw reply text of all %d draws (results/retain_api/%s)" % (n, model_dir))
    return out


def sha10(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:10]


def versions():
    """Hash the experiment-defining source at each pinned commit and at HEAD."""
    import ast

    def seg(src, name):
        for node in ast.parse(src).body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return ast.get_source_segment(src, node)
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == name for t in node.targets):
                return ast.get_source_segment(src, node)
        return ""

    def http_prompt(src):
        """The HTTP branch of run_one: prompt assembly and whitespace normalization, indentation aside."""
        lines = [l.strip() for l in seg(src, "run_one").split("\n")]
        out = [l for l in lines if l.startswith('prompt = ((ctx')]
        for i, l in enumerate(lines):
            if l.startswith('" ".join((prompt + " Return ONLY'):
                out += [l, lines[i + 1]]
                break
        return "\n".join(out) if len(out) == 3 else ""

    rows = {}
    for c in ("65e6843", "5a5dbcc", "HEAD"):
        src = git("show", "%s:harness/measure_blackwell.py" % c)
        rows[c] = {k: sha10(seg(src, k)) for k in ("TASKS", "_LEDGER_STUB", "W1", "W2", "W1plus",
                                                    "_extract_code", "verify_in")}
        rows[c]["run_one HTTP prompt"] = sha10(http_prompt(src)) if http_prompt(src) else "not found"
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    ver = versions()
    rows = []
    for label, stem, commit, interface in RECORDS:
        lf = log_facts(stem)
        first, last = added_and_last("results/%s.json" % stem)
        rows.append({
            "record": label, "file": "results/%s.json" % stem,
            "requested_model": lf.get("requested_model", ""),
            "interface": interface, "harness_commit": commit,
            "request_settings": "one user message; max tokens 8000; temperature, top-p and seed not set "
                                "(provider defaults); prompt suffix 'Return ONLY the raw Python file "
                                "content, no markdown fences, no prose.'",
            "log_markers": lf.get("markers", []),
            "execution_order_recorded": "cell completion order printed in the log (%d cells); arm-major: %s"
                                        % (lf.get("n_cells_logged", 0), lf.get("arm_major")),
            "execution_order_inferred": "all draws of one arm-task cell before the next (driver loop); "
                                        "within a cell, one after another (--workers 1, the default) "
                                        "or concurrently (--workers > 1)",
            "concurrency": "not established: the worker count was not recorded",
            "collection_time": "not recorded; record existed by %s (first added %s)" % (last, first),
            "retained": retained(stem),
            "unavailable": ["request start and end times", "order of draws inside a cell",
                            "worker count", "served model identifier or snapshot",
                            "provider request identifiers", "input token counts",
                            "sampling seed (none was set)"],
        })
    # the GPT-5.5 trap cells are read from a later, retained re-measurement
    first, last = added_and_last("results/%s_summary.json" % AUDIT_GPT_TRAP)
    draws = json.load(open(os.path.join(RES, AUDIT_GPT_TRAP + "_W1.json"), encoding="utf-8"))
    served = sorted({(r.get("model_requested"), r.get("model_served")) for r in draws})
    rows.append({
        "record": "GPT-5.5 trap cells (substitution)", "file": "results/%s_*.json" % AUDIT_GPT_TRAP,
        "requested_model": "gpt-5.5", "interface": "Azure-hosted endpoint, generic client",
        "harness_commit": "audit driver harness/diag/audit_any.py (Azure path the same in every version up to 2ed070e, which added the record)",
        "request_settings": "as above, except that the prompt was sent without whitespace "
                            "normalization: it keeps the blank line between source and task, and "
                            "the line breaks of the texts, that the grid prompt collapses to spaces",
        "log_markers": [], "execution_order_recorded": "none",
        "execution_order_inferred": "one condition after the other; within a condition, up to "
                                    "--workers concurrent requests (default 3)",
        "concurrency": "not established: the worker count was not recorded",
        "collection_time": "not recorded; record existed by %s" % last,
        "retained": ["per-draw raw reply, extracted code and verifier stderr",
                     "a model_served field the audit script filled with the requested deployment "
                     "name (%s); it is not a value returned by the endpoint" % served],
        "unavailable": ["request times", "worker count", "any model field returned by the endpoint",
                        "provider request identifiers", "sampling seed (none set)"],
    })
    doc = {"versions_by_commit": ver, "records": rows}
    json.dump(doc, open(os.path.join(OUT, "provenance_original.json"), "w", encoding="utf-8"), indent=1)

    same = lambda k: len({ver[c][k] for c in ver}) == 1
    md = ["# Provenance of the original measurements", "",
          "Generated by `harness/replication/provenance.py` from run logs, result files, retained",
          "completions and git history. A commit time bounds when a record existed; it is never a",
          "request time. No file modification time is used.", "",
          "## Experiment-defining source by harness commit", "",
          "| Component | 65e6843 (July runs) | 5a5dbcc (Anthropic HTTP runs) | HEAD | Unchanged |",
          "|---|---|---|---|---|"]
    for k in ("TASKS", "_LEDGER_STUB", "W1", "W2", "W1plus", "_extract_code", "run_one HTTP prompt",
              "verify_in"):
        md.append("| `%s` | %s | %s | %s | %s |" % (k, ver["65e6843"][k], ver["5a5dbcc"][k],
                                                   ver["HEAD"][k], "yes" if same(k) else "**no**"))
    md += ["", "`verify_in` differs only at HEAD: the published records were graded by process exit",
           "status; the current code requires a parent-generated token (Appendix C of the manuscript).",
           "The checks themselves are the task strings in `TASKS` and `_LEDGER_STUB`, unchanged.",
           "`run_one HTTP prompt` is the prompt assembly of the HTTP path (source, blank line, task,",
           "suffix, then whitespace collapsed to single spaces), compared with indentation removed.", "",
           "## Records", ""]
    for r in rows:
        md += ["### %s" % r["record"], "",
               "- File: `%s`" % r["file"],
               "- Requested model: `%s`; interface: %s; harness commit `%s`" % (
                   r["requested_model"], r["interface"], r["harness_commit"]),
               "- Request settings: %s" % r["request_settings"],
               "- Execution order, recorded: %s" % r["execution_order_recorded"],
               "- Execution order, inferred from the driver: %s" % r["execution_order_inferred"],
               "- Concurrency: %s" % r["concurrency"],
               "- Collection time: %s" % r["collection_time"],
               "- Retained: %s" % "; ".join(r["retained"]),
               "- Unavailable: %s" % "; ".join(r["unavailable"]), ""]
    open(os.path.join(OUT, "provenance_original.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))
    print("wrote results/replication/provenance_original.{md,json}: %d records" % len(rows))
    for k in ver["HEAD"]:
        print("  %-14s %s" % (k, "unchanged 65e6843 -> 5a5dbcc -> HEAD" if same(k) else
                             "CHANGED: %s" % [ver[c][k] for c in ver]))
    for r in rows[:6]:
        print("  %-22s model=%-18s order recorded: %s" % (r["record"], r["requested_model"],
                                                         r["execution_order_recorded"]))


if __name__ == "__main__":
    main()
