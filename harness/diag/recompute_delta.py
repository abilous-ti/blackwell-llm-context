"""Recompute every reported harm bound under the corrected confidence allocation.

As implemented: clopper_pearson(k, n, eta/2) -- a TWO-SIDED interval with eta/4 in
each tail -- then only CP_hi of the superset arm and CP_lo of the W1 arm are used.
Two of the four endpoints are never touched, so the delivered guarantee is 1-eta/2,
not 1-eta, and the bound is needlessly wide.

Corrected: each one-sided bound should carry noncoverage eta/2, union-bounding to
eta. That is clopper_pearson(k, n, eta) two-sided, taking the single endpoint.
"""
import sys, io, json, os
sys.path.insert(0, r"C:\Users\AndriyBilous\Documents\GitHub\blackwell-llm-context\harness")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from measure_blackwell import clopper_pearson as cp
R = r"C:\Users\AndriyBilous\Documents\GitHub\blackwell-llm-context\results"
ETA, TAU = 0.10, 0.30

def old(k1, n1, kp, np_): return cp(kp, np_, ETA / 2)[1] - cp(k1, n1, ETA / 2)[0]
def new(k1, n1, kp, np_): return cp(kp, np_, ETA)[1] - cp(k1, n1, ETA)[0]
def bonf(k1, n1, kp, np_, m=2): return cp(kp, np_, ETA / m)[1] - cp(k1, n1, ETA / m)[0]

SPEC = {"Haiku-4.5": "blackwell_haiku_ss_n40.json", "Sonnet-4.6": "blackwell_sonnet_ss_n40.json",
        "Opus-4.8": "blackwell_opus_ss_n40.json", "GPT-5.5": "blackwell_gpt55_n40.json",
        "DeepSeek-V4-Pro": "blackwell_deepseek_n40.json", "Kimi-K2.6": "blackwell_kimi_n40.json"}
OPUS_W1P = {"api_post_ok": [15, 40], "api_argorder": [6, 40]}

print("=" * 74)
print("PUBLISHED CELLS (Table: anti-monotonicity)")
print("=" * 74)
print("%-16s %-13s  D       old      new      new-Bonf(2)" % ("model", "cell"))
nv_old = nv_new = nb_old = nb_new = tot = 0
for m, f in SPEC.items():
    c = json.load(open(os.path.join(R, f), encoding="utf-8"))["counts"]
    for t in ("api_post_ok", "api_argorder"):
        k1, n1 = c["W1|" + t]
        kp, np_ = OPUS_W1P[t] if m == "Opus-4.8" else c["W1plus|" + t]
        d = kp / np_ - k1 / n1
        o, nw, b_o, b_n = old(k1, n1, kp, np_), new(k1, n1, kp, np_), \
            cp(kp, np_, ETA / 4)[1] - cp(k1, n1, ETA / 4)[0], bonf(k1, n1, kp, np_)
        tot += 1
        nv_old += o <= -TAU; nv_new += nw <= -TAU
        nb_old += b_o <= -TAU; nb_new += b_n <= -TAU
        print("%-16s %-13s %+.2f   %+.3f   %+.3f   %+.3f  %s"
              % (m, t, d, o, nw, b_n, "" if nw <= -TAU else "<-- still short"))
print()
print("verified marginal : old %d/%d   new %d/%d" % (nv_old, tot, nv_new, tot))
print("verified Bonf(2)  : old %d/%d   new %d/%d" % (nb_old, tot, nb_new, tot))

print()
print("=" * 74)
print("CONTROLS")
print("=" * 74)
pad = json.load(open(os.path.join(R, "blackwell_pad_n40b.json"), encoding="utf-8"))["counts"]
k1, n1 = pad["W1|api_argorder"]; kp, np_ = pad["W1plus|api_argorder"]
print("padding, api_argorder      old %+.3f  new %+.3f" % (old(k1, n1, kp, np_), new(k1, n1, kp, np_)))
p8 = json.load(open(os.path.join(R, "blackwell_pair2_n80.json"), encoding="utf-8"))["counts"]
k1, n1 = p8["W1|cache_put_ok"]; kp, np_ = p8["W1plus|cache_put_ok"]
o, nw = old(k1, n1, kp, np_), new(k1, n1, kp, np_)
print("pair-2 n=80                old %+.3f  new %+.3f   %s"
      % (o, nw, "NOW CLEARS tau" if nw <= -TAU < o else ""))
print("import-neutralized Haiku   old %+.3f  new %+.3f" % (old(40, 40, 21, 40), new(40, 40, 21, 40)))
print("Haiku api_post_ok (orig)   old %+.3f  new %+.3f" % (old(21, 40, 6, 40), new(21, 40, 6, 40)))

print()
print("=" * 74)
print("RE-MEASUREMENT TABLE (fresh draws, results/audit)")
print("=" * 74)
LAB = {"haiku": "Haiku-4.5", "sonnet": "Sonnet-4.6", "opus": "Opus-4.8",
       "deepseek": "DeepSeek-V4-Pro", "kimi": "Kimi-K2.6", "gpt55": "GPT-5.5"}
for lab in LAB:
    for t in ("api_post_ok", "api_argorder"):
        fw = os.path.join(R, "audit", "audit_%s_%s_W1.json" % (lab, t))
        fp = os.path.join(R, "audit", "audit_%s_%s_W1plus.json" % (lab, t))
        if not (os.path.exists(fw) and os.path.exists(fp)):
            continue
        w, p = json.load(open(fw)), json.load(open(fp))
        k1 = sum(bool(r.get("pass_original")) for r in w)
        kp = sum(bool(r.get("pass_original")) for r in p)
        print("%-16s %-13s  %2d/%d -> %2d/%d   old %+.3f  new %+.3f"
              % (LAB[lab], t, k1, len(w), kp, len(p),
                 old(k1, len(w), kp, len(p)), new(k1, len(w), kp, len(p))))
