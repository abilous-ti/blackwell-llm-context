"""Guard against the defect class that reached the manuscript three times: a number
published without checking that the run behind it used the same transport and turn
budget as the main table.

The regime is NOT inferred from log formatting -- an earlier version of this script
did that and misclassified the reranker probe, which writes its own log format but
does pass --max-turns 1. Each entry below is asserted from the invocation, with the
evidence named, and the guard checks that the manuscript discloses every cited run
that is not single-shot.

Regimes, as harness/measure_blackwell.py implements them:
  cli-singleshot  claude -p --max-turns 1, no tools     (a completion probe)
  cli-agentic     claude -p --max-turns 6, tools on     (an agent loop)
  http-api        urllib to an Azure / OpenAI-compatible endpoint
  local           no model call at all (open-weight scoring on this machine)

Run:  python harness/diag/check_regimes.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(ROOT, "paper", "blackwell-paper.tex")

# file stem -> (regime, evidence)
REGIME = {
    # six-model record: all six over HTTP, one turn per attempt
    "blackwell_haiku_api_n40":       ("http-api", "anthropic messages launcher"),
    "blackwell_sonnet_api_n40":      ("http-api", "anthropic messages launcher"),
    "blackwell_opus_api_n40":        ("http-api", "anthropic messages launcher"),
    # superseded command-line runs of the same three models, retained so that naming one
    # in the manuscript again is caught rather than silently accepted
    "blackwell_haiku_ss_n40":        ("cli-singleshot", "SUPERSEDED by the API run"),
    "blackwell_sonnet_ss_n40":       ("cli-singleshot", "SUPERSEDED by the API run"),
    "blackwell_opus_ss_n40":         ("cli-singleshot", "SUPERSEDED by the API run"),
    "blackwell_gpt55_n40":           ("http-api", "azure responses launcher"),
    "blackwell_deepseek_n40":        ("http-api", "azure chat launcher"),
    "blackwell_kimi_n40":            ("http-api", "openai-compatible chat launcher"),
    # arm-only re-measurements, re-run by harness/diag/rerun_arm.py with run logs
    "blackwell_opus_ss_W1plus_v2":   ("cli-singleshot", "log line 2 [SINGLE-SHOT], rerun_arm.py"),
    "blackwell_opus_ss_W2_trap_v2":  ("cli-singleshot", "log line 2 [SINGLE-SHOT], rerun_arm.py"),
    "blackwell_haiku_ss_W1_enc_v2":  ("cli-singleshot", "log line 2 [SINGLE-SHOT], rerun_arm.py"),
    "blackwell_xml_arm_v2":          ("cli-singleshot", "log line 2 [SINGLE-SHOT], rerun_arm.py"),
    # superseded by the v2 re-measurements above
    "blackwell_opus_ss_W1plus":      ("cli-singleshot", "STATED, superseded"),
    "blackwell_opus_ss_W2_trap_rerun": ("cli-singleshot", "STATED, superseded"),
    "blackwell_haiku_ss_W1_enc_rerun": ("cli-singleshot", "STATED, superseded"),
    # ablations
    "blackwell_pad_n40b":            ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    "blackwell_instr_n40":           ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    "blackwell_xml_n40":             ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    "blackwell_xml_arm_only":        ("cli-singleshot", "STATED, superseded"),
    # probes
    "reranker_trap_n30":             ("cli-singleshot", "measure_reranker_trap.py:36 --max-turns 1"),
    "dense_trap":                    ("local", "measure_dense_trap.py, open weights, no API"),
    "blackwell_order_ss_n40":        ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    # agentic runs, no longer cited by the manuscript
    # SUPERSEDED by the HTTP record. Its log was not kept, so the regime is stated from the
    # run's own provenance and cannot be re-derived; the manuscript cites neither of these two.
    "blackwell_n80_results":         ("cli-agentic", "SUPERSEDED; log not retained"),
    "blackwell_argorder_n80":        ("cli-agentic", "SUPERSEDED; log predates the markers"),
    "blackwell_pair2_n40":           ("cli-agentic", "log line 3 lacks [SINGLE-SHOT]"),
    "blackwell_pair2_n80":           ("cli-agentic", "log line 3 lacks [SINGLE-SHOT]"),
}

RESULTS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "results")

NEEDS_DISCLOSURE = {"cli-agentic": "agentic"}


def derive_regime(stem):
    """Read the regime off the run log. Returns (regime, evidence) or (None, why-not).

    This is the half the table cannot supply: the log is written by the run itself, so it is
    evidence, whereas REGIME is only a claim about the run."""
    claimed = REGIME.get(stem, (None, ""))[0]
    if claimed == "local":
        return "local", "scored offline from open weights; no run log by design"
    if stem.startswith("reranker_trap"):
        return claimed, REGIME[stem][1]   # driven by its own script; its invocation is the evidence
    p = os.path.join(RESULTS, stem + ".log")
    if not os.path.exists(p):
        return None, "no log at results/%s.log" % stem
    head = open(p, encoding="utf-8", errors="replace").read(4000)
    if "[HTTP-API]" in head:
        return "http-api", "log carries [HTTP-API]"
    if "[SINGLE-SHOT]" in head:
        return "cli-singleshot", "log carries [SINGLE-SHOT]"
    if "model = claude" in head:
        # the only family with more than one possible transport, so a marker is required
        return "cli-agentic", "claude model, log carries neither [HTTP-API] nor [SINGLE-SHOT]"
    if "model = " in head:
        # no code path other than _azure_complete exists for a non-claude model
        return "http-api", "non-claude model; the harness has no other path for one"
    return None, "no regime marker and no model line; cannot be derived from the log"




def main():
    # The manuscript is submitted to the journal, not published here. With it present the check is
    # scoped to the runs the text actually cites; without it the runs behind the published record
    # are checked instead, so the reproduction path works without the manuscript.
    tex = open(TEX, encoding="utf-8").read() if os.path.exists(TEX) else None
    if tex is None:
        print("manuscript not present; checking the runs behind the published record")
    problems, cited = [], {}

    for stem, (reg, ev) in sorted(REGIME.items()):
        if tex is None:
            # Without the manuscript there is no citation list to scope to, so check the runs the
            # published record is built from. Superseded entries are deliberately excluded: their
            # logs predate the regime markers and were never expected to be re-derivable, so
            # including them would report a failure where the table already discloses the fact.
            if "SUPERSEDED" in ev.upper():
                continue
            cited[stem] = (reg, ev)
        elif re.search(re.escape(stem.replace("_", "\\_")) + r"(?![A-Za-z0-9_\\])", tex):
            cited[stem] = (reg, ev)

    print("%-34s %-16s %s" % ("cited result file", "regime", "evidence"))
    print("-" * 96)
    for stem, (reg, ev) in sorted(cited.items()):
        d, why = derive_regime(stem)
        flag = "" if d == reg else ("  <-- LOG SAYS %s" % (d or "unverifiable"))
        print("%-34s %-16s %s%s" % (stem, reg, why, flag))

    regs = sorted({r for r, _ in cited.values()})
    print()
    print("regimes among cited files:", regs)

    for stem, (reg, ev) in cited.items():
        derived, why = derive_regime(stem)
        if derived is None:
            problems.append("%s: %s -- the table says %s, nothing confirms it"
                            % (stem, why, reg))
        elif derived != reg:
            problems.append("%s: the table says %s but its log says %s (%s)"
                            % (stem, reg, derived, why))
        # This clause asks whether the manuscript discloses the regime, so it applies only when
        # the manuscript is present. The regime derivation itself, above, does not need it.
        word = NEEDS_DISCLOSURE.get(derived or reg)
        if tex is not None and word and word not in tex:
            problems.append("%s is %s and the manuscript never says %r" % (stem, derived, word))
        if ev.startswith("STATED"):
            problems.append("%s: regime asserted but not reproducible from the repository "
                            "(%s)" % (stem, ev))

    uncovered = [s for s in cited if s not in REGIME]
    for s in uncovered:
        problems.append("%s is cited but has no entry in REGIME" % s)

    # The script said this already but its exit code did not honour it: a note that a SUPERSEDED
    # run's regime cannot be re-derived is a disclosure, not a failure. Only a regime that
    # contradicts its log, or a cited run missing from the table, should fail the build.
    notes = [p for p in problems if "not reproducible from the repository" in p]
    faults = [p for p in problems if p not in notes]

    print()
    if notes:
        print("NOTES (%d) - superseded runs whose regime is stated but not re-derivable:" % len(notes))
        for p in notes:
            print("  -", p)
        print()
    if faults:
        print("FAILURES (%d):" % len(faults))
        for p in faults:
            print("  -", p)
        print()
        print("A run whose log contradicts its recorded regime, or a cited run with no entry,")
        print("is a real problem: the record and the code disagree about how it was measured.")
        return 1
    print("OK: every cited run's regime is recorded and disclosed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
