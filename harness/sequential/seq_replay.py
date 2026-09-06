"""
Retrospective cost analysis: how much cheaper would the incomparability
verification have been under ANYTIME-VALID sequential testing instead of the
fixed-n=40 Clopper-Pearson batch?

Decision rule replicated exactly from harness/measure_blackwell.py:
    alpha_pair = eta / (2|D|);  L_T = lo(p_B(T)) - hi(p_A(T));  L_D = max_T L_T
    verified iff L_D(A,B) > 0 and L_D(B,A) > 0

Fixed-n intervals : exact Clopper-Pearson (scipy.stats.beta).
Sequential intervals: anytime-valid confidence sequence from the beta-mixture
    (uniform-prior) martingale, valid under optional stopping via Ville:
        log M_n(p) = logB(S+1, n-S+1) - [S log p + (n-S) log(1-p)]
        CS_n(a)    = { p : log M_n(p) < log(1/a) }
"""
import json, math, os, random
from scipy.stats import beta as sbeta
from scipy.special import betaln

RES = r'C:\Users\AndriyBilous\Documents\GitHub\blackwell-llm-context\results'
MODELS = [
    ("Haiku-4.5",       "blackwell_haiku_ss_n40.json"),
    ("Sonnet-4.6",      "blackwell_sonnet_ss_n40.json"),
    ("Opus-4.8",        "blackwell_opus_ss_n40.json"),
    ("GPT-5.5",         "blackwell_gpt55_n40.json"),
    ("DeepSeek-V4-Pro", "blackwell_deepseek_n40.json"),
    ("Kimi-K2.6",       "blackwell_kimi_n40.json"),
]
ETA = 0.10


def cp_interval(S, n, alpha):
    """Exact two-sided Clopper-Pearson at level alpha."""
    lo = 0.0 if S == 0 else sbeta.ppf(alpha / 2, S, n - S + 1)
    hi = 1.0 if S == n else sbeta.ppf(1 - alpha / 2, S + 1, n - S)
    return float(lo), float(hi)


def _logM(p, S, n):
    if p <= 0.0:
        return math.inf if S > 0 else betaln(S + 1, n - S + 1)
    if p >= 1.0:
        return math.inf if S < n else betaln(S + 1, n - S + 1)
    return betaln(S + 1, n - S + 1) - (S * math.log(p) + (n - S) * math.log1p(-p))


def av_interval(S, n, alpha, tol=1e-6):
    """Anytime-valid CS: {p : logM(p) < log(1/alpha)}. Interval by bisection."""
    thr = -math.log(alpha)
    centre = S / n if n else 0.5
    if _logM(centre, S, n) >= thr:          # cannot exclude anything yet
        return 0.0, 1.0
    lo = 0.0
    if _logM(0.0, S, n) >= thr:
        a, b = 0.0, centre
        while b - a > tol:
            m = (a + b) / 2
            if _logM(m, S, n) >= thr: a = m
            else: b = m
        lo = b
    hi = 1.0
    if _logM(1.0, S, n) >= thr:
        a, b = centre, 1.0
        while b - a > tol:
            m = (a + b) / 2
            if _logM(m, S, n) < thr: a = m
            else: b = m
        hi = a
    return lo, hi


def L_D(intervals, A, B, tasks):
    """max_T [ lo(p_B(T)) - hi(p_A(T)) ]  -- simultaneously valid lower bound."""
    return max(intervals[(B, t)][0] - intervals[(A, t)][1] for t in tasks)


def load(fn):
    with open(os.path.join(RES, fn)) as f:
        d = json.load(f)
    counts = {}
    for key, (S, n) in d["counts"].items():
        arm, task = key.split("|", 1)
        counts[(arm, task)] = (S, n)
    return counts


def draws(S, n, rng):
    """A draw sequence consistent with S successes in n trials.
    Stark cells (S=0 or S=n) are order-invariant -> EXACT, not simulated."""
    seq = [1] * S + [0] * (n - S)
    if 0 < S < n:
        rng.shuffle(seq)
    return seq


def stopping_time(counts, tasks, alpha, rng, nmax):
    seqs = {k: draws(*counts[k], rng) for k in counts}
    S = {k: 0 for k in counts}
    for n in range(1, nmax + 1):
        for k in seqs:
            S[k] += seqs[k][n - 1]
        iv = {k: av_interval(S[k], n, alpha) for k in counts}
        if L_D(iv, "W1", "W2", tasks) > 0 and L_D(iv, "W2", "W1", tasks) > 0:
            return n
    return None


def main():
    print(f"{'Model':<17} {'fixed n=40':<24} {'sequential (anytime-valid)':<30} {'saving'}")
    print("-" * 92)
    tot_fixed = tot_seq = 0
    for name, fn in MODELS:
        c = load(fn)
        tasks = sorted({t for (a, t) in c if a == "W1"})
        arms_needed = {(a, t) for a in ("W1", "W2") for t in tasks}
        c = {k: v for k, v in c.items() if k in arms_needed}
        nmax = min(n for _, n in c.values())
        alpha = ETA / (2 * len(tasks))

        ivf = {k: cp_interval(c[k][0], nmax, alpha) for k in c}
        ab, ba = L_D(ivf, "W1", "W2", tasks), L_D(ivf, "W2", "W1", tasks)
        fixed_ok = ab > 0 and ba > 0

        stark = all(S == 0 or S == n for S, n in c.values())
        rng = random.Random(0)
        reps = 1 if stark else 400
        ts = [stopping_time(c, tasks, alpha, rng, nmax) for _ in range(reps)]
        ok = [t for t in ts if t is not None]
        if ok:
            med = sorted(ok)[len(ok) // 2]
            worst = max(ok)
            kind = "exact" if stark else f"median of {reps} perms"
            seq_txt = f"n={med} ({kind})" + ("" if stark else f", max {worst}")
        else:
            med = nmax
            seq_txt = f"not reached by n={nmax}"

        cost_fixed = nmax * 2 * len(tasks)
        cost_seq = med * 2 * len(tasks)
        tot_fixed += cost_fixed
        tot_seq += cost_seq
        print(f"{name:<17} L_D=+{ab:.2f}/+{ba:.2f} {'OK' if fixed_ok else 'NO':<4} "
              f"{seq_txt:<30} {cost_fixed}->{cost_seq} calls "
              f"({cost_fixed/max(cost_seq,1):.1f}x)")
    print("-" * 92)
    print(f"{'TOTAL':<17} {tot_fixed} -> {tot_seq} model calls   "
          f"reduction {tot_fixed/max(tot_seq,1):.1f}x "
          f"({100*(1-tot_seq/tot_fixed):.0f}% fewer)")


if __name__ == "__main__":
    main()
