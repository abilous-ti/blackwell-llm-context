"""
Retrospective cost analysis for the INTERFERENCE verification (anti-monotonicity).
Rule from the paper: Psi_T = P(W1+) - P(W1) - P(W2) + P(none); verified iff
    upper(Psi_T) = up(W1+) - lo(W1) - lo(W2) + up(none) <= -tau,   tau=0.30, alpha=eta/4.
Sequential: anytime-valid beta-mixture CS on each of the 4 arms; stop at first n with
upper <= -tau.  Stark arms are order-invariant (exact); mixed arms are permutation-replayed.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from seq_replay import av_interval, cp_interval, load, draws, RES

ETA, TAU = 0.10, 0.30
ALPHA = ETA / 4
# (model, file, carrying cell) -- the cells the paper verifies (tab:interference)
CELLS = [
    ("Haiku-4.5",       "blackwell_haiku_ss_n40.json", "api_argorder"),
    ("Sonnet-4.6",      "blackwell_sonnet_ss_n40.json", "api_post_ok"),
    ("Sonnet-4.6",      "blackwell_sonnet_ss_n40.json", "api_argorder"),
    ("GPT-5.5",         "blackwell_gpt55_n40.json",     "api_post_ok"),
    ("DeepSeek-V4-Pro", "blackwell_deepseek_n40.json",  "api_post_ok"),
    ("Kimi-K2.6",       "blackwell_kimi_n40.json",      "api_post_ok"),
    ("Opus-4.8",        "blackwell_opus_ss_n40.json",   "api_post_ok"),   # paper: NOT verified
]
ARMS = ["none", "W1", "W2", "W1plus"]


def psi_upper(iv):
    return iv["W1plus"][1] - iv["W1"][0] - iv["W2"][0] + iv["none"][1]


def stop_time(counts, rng, nmax):
    seqs = {a: draws(*counts[a], rng) for a in ARMS}
    S = {a: 0 for a in ARMS}
    for n in range(1, nmax + 1):
        for a in ARMS:
            S[a] += seqs[a][n - 1]
        iv = {a: av_interval(S[a], n, ALPHA) for a in ARMS}
        if psi_upper(iv) <= -TAU:
            return n
    return None


print(f"{'Model':<16}{'cell':<14}{'Psi':>6}{'fixed upper':>13}{'verdict':>9}   sequential stop")
print("-" * 86)
tot_f = tot_s = 0
for name, fn, cell in CELLS:
    c = load(fn)
    counts = {a: c[(a, cell)] for a in ARMS}
    if fn == "blackwell_opus_ss_n40.json":
        # The Opus W1+ arm in the main file was hit by a transport outage; the paper
        # (and Table 5) use the isolated re-run blackwell_opus_ss_W1plus.json.
        rr = json.load(open(os.path.join(RES, "blackwell_opus_ss_W1plus.json")))
        counts["W1plus"] = (rr[cell]["pass"], rr[cell]["n"])
    nmax = min(n for _, n in counts.values())
    p = {a: S / n for a, (S, n) in counts.items()}
    psi = p["W1plus"] - p["W1"] - p["W2"] + p["none"]
    ivf = {a: cp_interval(*counts[a], ALPHA) for a in ARMS}
    up_f = psi_upper(ivf)
    verdict = "YES" if up_f <= -TAU else "no"

    stark = all(S in (0, n) for S, n in counts.values())
    rng = random.Random(1)
    reps = 1 if stark else 400
    ts = [stop_time(counts, rng, nmax) for _ in range(reps)]
    ok = [t for t in ts if t is not None]
    if ok and len(ok) == reps:
        med = sorted(ok)[len(ok) // 2]
        txt = f"n={med}" + (" (exact)" if stark else f" (median/{reps}, max {max(ok)})")
        cost_s = med * 4
    elif ok:
        txt = f"reached in {len(ok)}/{reps} perms only"
        cost_s = nmax * 4
    else:
        txt = f"not reached by n={nmax} (matches fixed verdict)"
        cost_s = nmax * 4
    cost_f = nmax * 4
    if verdict == "YES":
        tot_f += cost_f; tot_s += cost_s
    print(f"{name:<16}{cell:<14}{psi:>+6.2f}{up_f:>+13.2f}{verdict:>9}   {txt}")
print("-" * 86)
print(f"verified cells only: {tot_f} -> {tot_s} calls  ({tot_f/max(tot_s,1):.1f}x, "
      f"{100*(1-tot_s/tot_f):.0f}% fewer)")
