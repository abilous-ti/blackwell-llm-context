r"""Check every confidence bound printed in the manuscript's tables against the computed one.

The rule the paper states is that a bound is rounded AWAY from the claim it supports: a lower
bound down, an upper bound up. Stated that way it holds for bounds of either sign, which the
previous wording ("an upper bound toward zero") did not -- it is only correct while the upper
bound is negative.

A printed bound is sound iff it is implied by the computed one:
    printed lower <= computed lower        (weaker, so safe)
    printed upper >= computed upper        (weaker, so safe)
Anything else asserts more than the data support.

Usage:  python harness/diag/check_printed_bounds.py
"""
import json, os, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "harness"))
from measure_blackwell import clopper_pearson as cp                  # noqa: E402

RES = os.path.join(ROOT, "results")
TEX = os.path.join(ROOT, "paper", "blackwell-paper.tex")
ETA, TAU = 0.10, 0.30
TASKS = ["api_post_ok", "api_argorder", "enc_amount", "trap_store_wire"]
FILES = [("Haiku-4.5", "blackwell_haiku_api_n40"), ("Sonnet-4.6", "blackwell_sonnet_api_n40"),
         ("Opus-4.8", "blackwell_opus_api_n40"), ("GPT-5.5", "blackwell_gpt55_n40"),
         ("DeepSeek-V4-Pro", "blackwell_deepseek_n40"), ("Kimi-K2.6", "blackwell_kimi_n40")]
GPT_TRAP = os.path.join(RES, "audit", "audit_gpt55_trap_store_wire_summary.json")

counts = {}
for lab, f in FILES:
    c = json.load(open(os.path.join(RES, f + ".json"), encoding="utf-8"))["counts"]
    counts[lab] = {k: tuple(v) for k, v in c.items()}
if os.path.exists(GPT_TRAP):
    arms = json.load(open(GPT_TRAP, encoding="utf-8"))["arms"]
    for a, v in arms.items():
        counts["GPT-5.5"]["%s|trap_store_wire" % a] = (v["pass_original"], v["n"])

src = open(TEX, encoding="utf-8").read()
bad, checked = [], 0

# --- interference table: "Model & \texttt{cell} & $A\% \to B\%$ & $D$ & $U$ & \checkmark" ----
row = re.compile(r"^([\w.\-]+(?:-[\w.]+)*)\s*&\s*\\texttt\{(api\\_post\\_ok|api\\_argorder)\}"
                 r".*?&\s*\$([-+]?\d*\.?\d+)\$\s*&\s*\$([-+]?\d*\.?\d+)\$", re.M)
for m in row.finditer(src):
    lab, cell = m.group(1), m.group(2).replace("\\_", "_")
    printed_d, printed_u = float(m.group(3)), float(m.group(4))
    if lab not in counts:
        continue
    kA, nA = counts[lab]["W1plus|" + cell]
    kB, nB = counts[lab]["W1|" + cell]
    d = kA / nA - kB / nB
    u = cp(kA, nA, ETA)[1] - cp(kB, nB, ETA)[0]
    checked += 2
    # Delta is a point estimate, not a bound: any correct 2-decimal rounding is within half a
    # unit, and an exact half (-0.625 -> -0.62) is correct either way. Bounds are the strict case.
    if abs(printed_d - d) > 5e-3 + 1e-9:
        bad.append("%s/%s Delta printed %+.3f, computed %+.4f" % (lab, cell, printed_d, d))
    if printed_u < u - 1e-9:                      # printed upper must be >= computed upper
        bad.append("%s/%s upper printed %+.3f is STRONGER than computed %+.6f"
                   % (lab, cell, printed_u, u))

# --- consolidated table: L_D rows are LOWER bounds, printed must be <= computed --------------
for direction, (X, Y) in (("W_1,W_2", ("W1", "W2")), ("W_2,W_1", ("W2", "W1"))):
    m = re.search(r"\$L_\{\\Dcal\}\(%s\)\$((?:\s*&\s*\$[-+]?\d*\.?\d+\$)+)" % re.escape(direction), src)
    if not m:
        continue
    vals = [float(x) for x in re.findall(r"\$([-+]?\d*\.?\d+)\$", m.group(1))]
    for (lab, _f), printed in zip(FILES, vals):
        best = max(cp(*counts[lab]["%s|%s" % (Y, t)], ETA / 8)[0]
                   - cp(*counts[lab]["%s|%s" % (X, t)], ETA / 8)[1] for t in TASKS)
        checked += 1
        if printed > best + 1e-9:                 # printed lower must be <= computed lower
            bad.append("L_D(%s) %s printed %+.3f is STRONGER than computed %+.6f"
                       % (direction, lab, printed, best))

print("checked %d printed bounds against the released counts" % checked)
if bad:
    print("UNSOUND (printed bound not implied by the computed one):")
    for b in bad:
        print("   " + b)
    sys.exit(1)
print("every printed bound is implied by the computed one")
