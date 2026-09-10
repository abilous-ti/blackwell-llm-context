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

# The manuscript is submitted to the journal rather than published here, so this check is
# available when the source is present locally and skips cleanly when it is not. It checks
# manuscript-to-data consistency; the research itself reproduces without it.
if not os.path.exists(TEX):
    print("manuscript not present at %s - skipping the printed-bound check." % TEX)
    print("(this verifies the paper against the data; the data recomputation is recompute.py)")
    sys.exit(0)
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

# --- prose bounds: every 4-decimal figure must be an OUTWARD rounding of a computed endpoint ---
# Two review rounds found endpoints rounded inward in prose, where no table structure makes the
# error visible. Build the set of endpoints the controls and the second pair can produce, each
# tagged with its role, and require every printed 4-decimal value to be a sound rounding of one.
def endpoints():
    out = []
    ctl = json.load(open(os.path.join(RES, "blackwell_controls_api_n40.json"),
                         encoding="utf-8"))["counts"]
    p2 = json.load(open(os.path.join(RES, "blackwell_pair2_api_n40.json"),
                        encoding="utf-8"))["counts"]
    pairs = []
    for t in ("api_post_ok", "api_argorder"):
        for a in ("W1plus", "W1pad", "W1plus_instr", "W1plus_xml", "W1plus_rev"):
            pairs.append((ctl["%s|%s" % (a, t)], ctl["W1|" + t]))
        pairs.append((ctl["W1plus|" + t], ctl["W1pad|" + t]))
    for t in ("cache_put_ok", "key_norm", "trap_cache"):
        pairs.append((p2["W1plus|" + t], p2["W1|" + t]))
    for (kA, nA), (kB, nB) in pairs:
        for lvl in (ETA, ETA / 2, ETA / 3):        # one-sided, two-sided-via-95%, 3-contrast budget
            out.append((cp(kA, nA, lvl)[0] - cp(kB, nB, lvl)[1], "lower"))
            out.append((cp(kA, nA, lvl)[1] - cp(kB, nB, lvl)[0], "upper"))
    return out


EPS = 1e-4
POOL = endpoints()
prose_checked = 0
for m in re.finditer(r"\$([-+]\d\.\d{4})\$", src):
    p = float(m.group(1))
    prose_checked += 1
    near = [(e, role) for e, role in POOL if abs(p - e) < EPS]
    if not near:
        bad.append("printed %+.4f matches no computed contrast endpoint" % p)
        continue
    if not any((p <= e + 1e-12) if role == "lower" else (p >= e - 1e-12) for e, role in near):
        e, role = min(near, key=lambda x: abs(p - x[0]))
        bad.append("printed %+.4f is an INWARD rounding of the computed %s bound %+.10f"
                   % (p, role, e))

print("checked %d table bounds and %d prose bounds against the released counts"
      % (checked, prose_checked))
if bad:
    print("UNSOUND (printed bound not implied by the computed one):")
    for b in bad:
        print("   " + b)
    sys.exit(1)
print("every printed bound is implied by the computed one")
