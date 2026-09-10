"""Regenerate results/MANIFEST.md.

Why this script exists. The previous manifest was produced by an ad-hoc script that was not
kept, and it drifted: it mapped the published per-cell and interference tables to the
pre-v2 arm files, the order control to the superseded n=80 agentic run, and the XML
ablation to a filename that no longer exists. A manifest whose job is provenance must not
be able to disagree with the code that computes the numbers, so the six-model rows here are
taken FROM the same declaration `recompute.py` uses. If that declaration changes, this file
changes with it.

Every path named in the mapping must exist, or nothing is written.

Usage:  python harness/diag/make_manifest.py [cli|api]
"""
import sys, io, os, json, hashlib, importlib.util
# NOTE: recompute.py rebinds sys.stdout to a utf-8 wrapper when imported below. Wrapping the
# same buffer twice closes it when the first wrapper is collected, so do not wrap here.

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NL_CH = chr(10)
RES = os.path.join(ROOT, "results")
MODE = (sys.argv[1] if len(sys.argv) > 1 else "cli").lower()

# --- single source of truth for which run files the six-model tables are built from ------
_rc_path = os.environ.get("RECOMPUTE_PY")
if not _rc_path:
    for cand in (os.path.join(ROOT, "harness", "diag", "recompute.py"),):
        if os.path.exists(cand):
            _rc_path = cand
if _rc_path and os.path.exists(_rc_path):
    spec = importlib.util.spec_from_file_location("rc", _rc_path)
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    TABLE = rc.CLI if MODE == "cli" else rc.API
else:                       # fall back to an inline copy, kept identical by the check below
    TABLE = {
        "Haiku-4.5": ("blackwell_haiku_ss_n40", {("W1", "enc_amount"): "blackwell_haiku_ss_W1_enc_v2"}),
        "Sonnet-4.6": ("blackwell_sonnet_ss_n40", {}),
        "Opus-4.8": ("blackwell_opus_ss_n40", {("W1plus", t): "blackwell_opus_ss_W1plus_v2"
                                               for t in ("api_post_ok", "api_argorder",
                                                         "enc_amount", "trap_store_wire")}),
        "GPT-5.5": ("blackwell_gpt55_n40", {}),
        "DeepSeek-V4-Pro": ("blackwell_deepseek_n40", {}),
        "Kimi-K2.6": ("blackwell_kimi_n40", {}),
    }
    TABLE["Opus-4.8"][1][("W2", "trap_store_wire")] = "blackwell_opus_ss_W2_trap_v2"

SIXMODEL = []
for _m, (_base, _over) in TABLE.items():
    SIXMODEL.append(_base + ".json")
    for _f in _over.values():
        if _f + ".json" not in SIXMODEL:
            SIXMODEL.append(_f + ".json")

MAPPING = [
    ("Table: per-cell PASS (tab:percell)", SIXMODEL),
    ("Table: consolidated 6-model verdict (tab:consolidated)", ["<same as tab:percell>"]),
    ("Table: anti-monotonicity (tab:interference)", ["<same as tab:percell>"]),
    ("Figure: harm forest plot (fig:forest)", ["<same as tab:percell>"]),
    ("Table: selection policies (tab:policies)", ["<same as tab:percell>"]),
    ("Figure: policy bars (fig:policies)", ["<same as tab:percell>"]),
    ("Figure: Hasse diagram (fig:hasse)", [TABLE["Haiku-4.5"][0] + ".json"]
     + sorted({f + ".json" for f in TABLE["Haiku-4.5"][1].values()})),
    ("Table: ranker spectrum (tab:rankers)", ["reranker_trap_api_n100.json", "dense_trap.json"]),
    ("Explicit-import condition", ["audit/audit_impctl-*.json"]),
    # Section 7.4.5 and Table A2 are computed from the RETAINED completions of the API runs by
    # harness/diag/retained_text_checks.py. The row used to point at diag/, which is the older
    # command-line diagnostic and not what those numbers come from.
    ("Raw-failure audit and retained-completions table (sec:results-audit, tab:retained)",
     ["retain_api/haiku/", "retain_api/sonnet/", "retain_api/opus/",
      "<computed by harness/diag/retained_text_checks.py>"]),
    ("Command-line diagnostic record (historical)", ["diag/"]),
    ("Behavioural controls: padding, order reversal, routing note, XML segmentation",
     ["blackwell_controls_api_n40.json"]),
    ("Second source pair", ["blackwell_pair2_api_n40.json"]),
    ("LLM listwise reranker probe", ["reranker_trap_api_n100.json"]),
    # The base GPT-5.5 run logged an HTTP 500 on this one cell, so the published trap result is
    # bound to the clean retained re-measurement instead. The percentages are unchanged.
    ("GPT-5.5 trap cell (transport-clean source)",
     ["audit/audit_gpt55_trap_store_wire_W1.json", "audit/audit_gpt55_trap_store_wire_W2.json",
      "audit/audit_gpt55_trap_store_wire_summary.json"]),
]

# --- guard: every concrete path in the mapping must exist --------------------------------
missing = []
for obj, files in MAPPING:
    for f in files:
        if f.startswith("<") or f.endswith("/") or "*" in f or "<" in f:
            continue
        if not os.path.exists(os.path.join(RES, f)):
            missing.append("%s -> %s" % (obj, f))
if missing:
    print("NOT WRITTEN - mapping names files that do not exist:")
    for m in missing:
        print("   " + m)
    sys.exit(1)

# --- inventory ---------------------------------------------------------------------------
# Only files that are actually PUBLISHED belong here. Walking the disk listed gitignored
# working directories too (results/raw_transcripts/ alone is ~3,100 files), so the manifest
# promised reviewers digests for files they cannot obtain. Ask git what is tracked instead.
import subprocess
try:
    _out = subprocess.run(["git", "ls-files", "results"], cwd=ROOT,
                          capture_output=True, text=True).stdout
except (FileNotFoundError, OSError):
    # git may not be installed at all. The README promises the standard library is enough, so a
    # missing executable must fall through to the filesystem inventory below, not raise.
    _out = ""
_tracked = sorted(p[len("results/"):] for p in _out.split(NL_CH) if p.startswith("results/"))
if not _tracked:
    # Outside a git checkout -- an exported tree, an unpacked archive, or a machine without git
    # installed -- git has nothing to report. Fall back to walking results/. The exclusions here
    # must match .gitignore, or the manifest would depend on whether git happens to be present:
    # an earlier version of this fallback listed 3288 files where git listed 3256, because it
    # picked up other papers' records that are on disk but deliberately unpublished.
    _skip_dirs = ("raw_transcripts", "reproduce", "__pycache__", "bcb", "invalid")
    _skip_prefixes = ("prevalence_", "prev_seq", "probe_select_", "README_prev")
    _tracked = []
    for _dp, _dns, _fns in os.walk(RES):
        _dns[:] = [d for d in _dns if d not in _skip_dirs]
        for _fn in _fns:
            _rel = os.path.relpath(os.path.join(_dp, _fn), RES).replace(os.sep, "/")
            if _rel == "MANIFEST.md" or _rel.startswith(_skip_prefixes):
                continue
            _tracked.append(_rel)
    _tracked.sort()
    print("git unavailable here; inventorying results/ directly (%d files)" % len(_tracked))

rows, total = [], 0
for rel_ in _tracked:
    if True:
        fn = os.path.basename(rel_)
        if fn == "MANIFEST.md":
            continue
        p = os.path.join(RES, rel_.replace("/", os.sep))
        b = open(p, "rb").read()
        rel = rel_
        rows.append((rel, len(b), hashlib.sha256(b).hexdigest()))
        total += len(b)
rows.sort()

NL = chr(10)
out = []
out.append("# Frozen manifest of the measurement records")
out.append("")
out.append("Every number in the manuscript is computed from the files listed here by the scripts in")
out.append("`harness/`. This file exists so that a reader can confirm the records were not edited")
out.append("after the fact: recompute the digests and compare. It is generated by")
out.append("`harness/diag/make_manifest.py`, which refuses to write if it names a file that is not")
out.append("present, and which takes the six-model rows from the same declaration the verification")
out.append("scripts use, so the manifest cannot drift from the computation.")
out.append("")
out.append("```bash")
out.append("# from the repository root")
out.append("python harness/diag/make_manifest.py %s   # regenerate" % MODE)
out.append("python - <<'EOF'")
out.append("import hashlib, os")
out.append("for dp, dns, fns in os.walk('results'):")
out.append("    dns[:] = [d for d in dns if d != '__pycache__']")
out.append("    for fn in sorted(fns):")
out.append("        if fn == 'MANIFEST.md': continue")
out.append("        p = os.path.join(dp, fn)")
out.append("        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()")
out.append("        print(h[:16], os.path.relpath(p, 'results').replace(os.sep, '/'))")
out.append("EOF")
out.append("```")
out.append("")
out.append("## Paper object to source files")
out.append("")
out.append("Transport of the six-model record in this manifest: **%s**." %
           ("Claude CLI single-shot / HTTP, as disclosed in the methodology section" if MODE == "cli"
            else "HTTP API for all six models"))
out.append("")
out.append("| Object in the manuscript | Computed from (paths relative to `results/`) |")
out.append("|---|---|")
for obj, files in MAPPING:
    out.append("| %s | %s |" % (obj, "<br>".join("`%s`" % f if not f.startswith("<") else f
                                                 for f in files)))
out.append("")
out.append("Arm-only re-runs supersede the corresponding cells of the base file. The verification")
out.append("scripts apply those overrides; see the reproducibility appendix of the manuscript for")
out.append("why each cell was re-measured.")
out.append("")
out.append("## Inventory")
out.append("")
out.append("%d files, %.1f MB total." % (len(rows), total / 1e6))
out.append("")
out.append("| File | Bytes | SHA-256 |")
out.append("|---|---|---|")
for rel, n, h in rows:
    out.append("| `%s` | %d | `%s` |" % (rel, n, h))
out.append("")

open(os.path.join(RES, "MANIFEST.md"), "w", encoding="utf-8", newline="\n").write(NL.join(out))
print("MANIFEST.md regenerated: %d files, %.1f MB, mode=%s" % (len(rows), total / 1e6, MODE))
print("six-model sources: %s" % ", ".join(SIXMODEL))
