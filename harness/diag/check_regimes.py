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
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(ROOT, "paper", "blackwell-paper.tex")

# file stem -> (regime, evidence)
REGIME = {
    # six-model record: three Claude models single-shot, three vendors over HTTP
    "blackwell_haiku_ss_n40":        ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    "blackwell_sonnet_ss_n40":       ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    "blackwell_opus_ss_n40":         ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    "blackwell_gpt55_n40":           ("http-api", "azure responses launcher"),
    "blackwell_deepseek_n40":        ("http-api", "azure chat launcher"),
    "blackwell_kimi_n40":            ("http-api", "openai-compatible chat launcher"),
    # arm-only re-measurements: producer scripts are NOT in the repository
    "blackwell_opus_ss_W1plus":      ("cli-singleshot", "STATED, producer script not in repo"),
    "blackwell_opus_ss_W2_trap_rerun": ("cli-singleshot", "STATED, producer script not in repo"),
    "blackwell_haiku_ss_W1_enc_rerun": ("cli-singleshot", "STATED, producer script not in repo"),
    # ablations
    "blackwell_pad_n40b":            ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    "blackwell_instr_n40":           ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    "blackwell_xml_n40":             ("cli-singleshot", "log line 3 [SINGLE-SHOT]"),
    "blackwell_xml_arm_only":        ("cli-singleshot", "STATED, producer script not in repo"),
    # probes
    "reranker_trap_n30":             ("cli-singleshot", "measure_reranker_trap.py:36 --max-turns 1"),
    "dense_trap":                    ("local", "measure_dense_trap.py, open weights, no API"),
    # agentic runs, reported as auxiliary
    "blackwell_n80_results":         ("cli-agentic", "log line 3 lacks [SINGLE-SHOT]"),
    "blackwell_argorder_n80":        ("cli-agentic", "log line 3 lacks [SINGLE-SHOT]"),
    "blackwell_pair2_n40":           ("cli-agentic", "log line 3 lacks [SINGLE-SHOT]"),
    "blackwell_pair2_n80":           ("cli-agentic", "log line 3 lacks [SINGLE-SHOT]"),
}

NEEDS_DISCLOSURE = {"cli-agentic": "agentic"}


def main():
    tex = open(TEX, encoding="utf-8").read()
    problems, cited = [], {}

    for stem, (reg, ev) in sorted(REGIME.items()):
        if stem.replace("_", r"\_") in tex:
            cited[stem] = (reg, ev)

    print("%-34s %-16s %s" % ("cited result file", "regime", "evidence"))
    print("-" * 96)
    for stem, (reg, ev) in sorted(cited.items()):
        print("%-34s %-16s %s" % (stem, reg, ev))

    regs = sorted({r for r, _ in cited.values()})
    print()
    print("regimes among cited files:", regs)

    for stem, (reg, ev) in cited.items():
        word = NEEDS_DISCLOSURE.get(reg)
        if word and word not in tex:
            problems.append("%s is %s and the manuscript never says %r" % (stem, reg, word))
        if ev.startswith("STATED"):
            problems.append("%s: regime asserted but not reproducible from the repository "
                            "(%s)" % (stem, ev))

    uncovered = [s for s in cited if s not in REGIME]
    for s in uncovered:
        problems.append("%s is cited but has no entry in REGIME" % s)

    print()
    if problems:
        print("ATTENTION (%d):" % len(problems))
        for p in problems:
            print("  -", p)
        print()
        print("Non-fatal where the note is only about reproducibility of the regime claim;")
        print("fatal if a cited agentic run is not disclosed as agentic in the manuscript.")
        return 1
    print("OK: every cited run's regime is recorded and disclosed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
