# Two-stage alpha-spending rule (valid under the union bound, no double-dipping):
#   stage 1: anytime-valid beta-mixture CS at alpha/2 per interval, stop as soon as verified;
#   stage 2: if not stopped by n_max, fixed-n exact Clopper-Pearson at alpha/2 at n_max.
# Each interval's total error <= alpha/2 + alpha/2 = alpha, so the paper's union bound is unchanged.
# Goal: keep the early stop on stark cells AND recover marginal verdicts that pure sequential loses.
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seq_replay import av_interval, cp_interval, load, draws, L_D, RES, MODELS, ETA

ARMS = ["none", "W1", "W2", "W1plus"]


def two_stage_incomp(counts, tasks, alpha, rng, nmax):
    a1 = a2 = alpha / 2
    seqs = {k: draws(*counts[k], rng) for k in counts}
    S = {k: 0 for k in counts}
    for n in range(1, nmax + 1):
        for k in seqs:
            S[k] += seqs[k][n - 1]
        iv = {k: av_interval(S[k], n, a1) for k in counts}
        if L_D(iv, "W1", "W2", tasks) > 0 and L_D(iv, "W2", "W1", tasks) > 0:
            return n, "stage1"
    ivf = {k: cp_interval(S[k], nmax, a2) for k in counts}
    ok = L_D(ivf, "W1", "W2", tasks) > 0 and L_D(ivf, "W2", "W1", tasks) > 0
    return nmax, ("stage2-verified" if ok else "stage2-NOT")


def two_stage_interf(counts, alpha, tau, rng, nmax):
    a1 = a2 = alpha / 2
    seqs = {a: draws(*counts[a], rng) for a in ARMS}
    S = {a: 0 for a in ARMS}
    for n in range(1, nmax + 1):
        for a in ARMS:
            S[a] += seqs[a][n - 1]
        iv = {a: av_interval(S[a], n, a1) for a in ARMS}
        if iv["W1plus"][1] - iv["W1"][0] - iv["W2"][0] + iv["none"][1] <= -tau:
            return n, "stage1"
    ivf = {a: cp_interval(S[a], nmax, a2) for a in ARMS}
    up = ivf["W1plus"][1] - ivf["W1"][0] - ivf["W2"][0] + ivf["none"][1]
    return nmax, ("stage2-verified" if up <= -tau else "stage2-NOT")


def summ(res):
    ns = [n for n, _ in res]
    kinds = {}
    for _, k in res:
        kinds[k] = kinds.get(k, 0) + 1
    med = sorted(ns)[len(ns) // 2]
    return med, max(ns), kinds


print("=== INCOMPARABILITY: two-stage (alpha/2 sequential, alpha/2 fixed at n=40) ===")
print(f"{'Model':<17}{'median stop':>12}{'max':>5}   outcomes")
tot = 0
for name, fn in MODELS:
    c = load(fn); tasks = sorted({t for (a, t) in c if a == "W1"})
    c = {k: v for k, v in c.items() if k[0] in ("W1", "W2")}
    nmax = min(n for _, n in c.values()); alpha = ETA / (2 * len(tasks))
    stark = all(S in (0, n) for S, n in c.values()); reps = 1 if stark else 400
    rng = random.Random(0)
    med, mx, kinds = summ([two_stage_incomp(c, tasks, alpha, rng, nmax) for _ in range(reps)])
    tot += med * 2 * len(tasks)
    print(f"{name:<17}{med:>12}{mx:>5}   {kinds}")
print(f"total calls 1920 -> {tot}  ({1920/tot:.1f}x)")

print()
print("=== INTERFERENCE: two-stage (tau=0.30) ===")
CELLS = [("Haiku-4.5","blackwell_haiku_ss_n40.json","api_argorder"),
         ("Sonnet-4.6","blackwell_sonnet_ss_n40.json","api_post_ok"),
         ("Sonnet-4.6","blackwell_sonnet_ss_n40.json","api_argorder"),
         ("GPT-5.5","blackwell_gpt55_n40.json","api_post_ok"),
         ("DeepSeek-V4-Pro","blackwell_deepseek_n40.json","api_post_ok"),
         ("Kimi-K2.6","blackwell_kimi_n40.json","api_post_ok"),
         ("Opus-4.8","blackwell_opus_ss_n40.json","api_post_ok")]
print(f"{'Model':<17}{'cell':<14}{'paper':>7}{'median stop':>12}   outcomes")
for name, fn, cell in CELLS:
    c = load(fn); counts = {a: c[(a, cell)] for a in ARMS}
    if fn == "blackwell_opus_ss_n40.json":
        rr = json.load(open(os.path.join(RES, "blackwell_opus_ss_W1plus.json")))
        counts["W1plus"] = (rr[cell]["pass"], rr[cell]["n"])
    nmax = min(n for _, n in counts.values()); alpha = ETA / 4
    ivf = {a: cp_interval(*counts[a], alpha) for a in ARMS}
    paper = "YES" if ivf["W1plus"][1] - ivf["W1"][0] - ivf["W2"][0] + ivf["none"][1] <= -0.30 else "no"
    stark = all(S in (0, n) for S, n in counts.values()); reps = 1 if stark else 400
    rng = random.Random(1)
    med, mx, kinds = summ([two_stage_interf(counts, alpha, 0.30, rng, nmax) for _ in range(reps)])
    print(f"{name:<17}{cell:<14}{paper:>7}{med:>12}   {kinds}")
