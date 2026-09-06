"""
Tighter anytime-valid CS: Waudby-Smith & Ramdas (2023) hedged betting CS for [0,1]-valued
data. Compared against the beta-mixture CS on BOTH verifications. Motivation: the mixture
CS lost the DeepSeek interference verdict that fixed-n CP obtains; a tighter CS may recover it.

Hedged capital (theta=1/2, c=1/2):
  K+_t(m) = prod (1 + lam+_i (X_i - m)),  K-_t(m) = prod (1 - lam-_i (X_i - m))
  lam_t   = sqrt( 2 log(2/alpha) / (sig2_{t-1} t log(1+t)) ),  lam+ = min(lam, c/m), lam- = min(lam, c/(1-m))
  CS_t    = { m : max(K+/2, K-/2) < 1/alpha }      (Ville on each half -> level alpha)
"""
import json, math, os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from seq_replay import av_interval, cp_interval, load, draws, L_D, RES, MODELS, ETA

GRID = np.linspace(0.0, 1.0, 2001)


def betting_interval(prefix, alpha, c=0.5):
    """Hedged betting CS from the ordered 0/1 prefix. Returns (lo, hi)."""
    t = len(prefix)
    if t == 0:
        return 0.0, 1.0
    x = np.asarray(prefix, dtype=float)
    # predictable running mean/variance (shrunk to 1/2, 1/4)
    csum = np.cumsum(x)
    mu_prev = np.concatenate(([0.5], (0.5 + csum[:-1]) / (np.arange(1, t))))
    dev2 = (x - mu_prev) ** 2
    sig2_prev = np.concatenate(([0.25], (0.25 + np.cumsum(dev2)[:-1]) / (np.arange(1, t))))
    i = np.arange(1, t + 1)
    lam = np.sqrt(2 * math.log(2 / alpha) / (sig2_prev * i * np.log1p(i)))
    m = GRID[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        lam_p = np.minimum(lam[:, None], np.where(m > 0, c / np.where(m > 0, m, 1.0), np.inf))
        lam_m = np.minimum(lam[:, None], np.where(m < 1, c / np.where(m < 1, 1 - m, 1.0), np.inf))
    xm = x[:, None] - m
    logKp = np.sum(np.log1p(lam_p * xm), axis=0)
    logKm = np.sum(np.log1p(-lam_m * xm), axis=0)
    thr = math.log(2 / alpha)                       # K/2 < 1/alpha  <=>  log K < log(2/alpha)
    accept = (logKp < thr) & (logKm < thr)
    if not accept.any():
        return float(csum[-1] / t), float(csum[-1] / t)
    idx = np.where(accept)[0]
    return float(GRID[idx[0]]), float(GRID[idx[-1]])


def seq_stop_incomp(counts, tasks, alpha, rng, nmax, method):
    seqs = {k: draws(*counts[k], rng) for k in counts}
    S = {k: 0 for k in counts}
    for n in range(1, nmax + 1):
        for k in seqs:
            S[k] += seqs[k][n - 1]
        if method == "mixture":
            iv = {k: av_interval(S[k], n, alpha) for k in counts}
        else:
            iv = {k: betting_interval(seqs[k][:n], alpha) for k in counts}
        if L_D(iv, "W1", "W2", tasks) > 0 and L_D(iv, "W2", "W1", tasks) > 0:
            return n
    return None


def seq_stop_interf(counts, alpha, tau, rng, nmax, method):
    arms = ["none", "W1", "W2", "W1plus"]
    seqs = {a: draws(*counts[a], rng) for a in arms}
    S = {a: 0 for a in arms}
    for n in range(1, nmax + 1):
        for a in arms:
            S[a] += seqs[a][n - 1]
        if method == "mixture":
            iv = {a: av_interval(S[a], n, alpha) for a in arms}
        else:
            iv = {a: betting_interval(seqs[a][:n], alpha) for a in arms}
        up = iv["W1plus"][1] - iv["W1"][0] - iv["W2"][0] + iv["none"][1]
        if up <= -tau:
            return n
    return None


def summarize(ts, nmax):
    ok = [t for t in ts if t is not None]
    if len(ok) == len(ts):
        med = sorted(ok)[len(ok) // 2]
        return f"n={med:>2} (max {max(ok):>2})", med
    if ok:
        return f"{len(ok)}/{len(ts)} perms reach", nmax
    return "not by n=%d" % nmax, nmax


def main():
    print("=== INCOMPARABILITY: beta-mixture CS vs betting CS ===")
    print(f"{'Model':<17}{'mixture':<22}{'betting':<22}")
    tm = tb = 0
    for name, fn in MODELS:
        c = load(fn)
        tasks = sorted({t for (a, t) in c if a == "W1"})
        c = {k: v for k, v in c.items() if k[0] in ("W1", "W2")}
        nmax = min(n for _, n in c.values())
        alpha = ETA / (2 * len(tasks))
        stark = all(S in (0, n) for S, n in c.values())
        reps = 1 if stark else 200
        r1, r2 = random.Random(0), random.Random(0)
        s_mix, m1 = summarize([seq_stop_incomp(c, tasks, alpha, r1, nmax, "mixture") for _ in range(reps)], nmax)
        s_bet, m2 = summarize([seq_stop_incomp(c, tasks, alpha, r2, nmax, "betting") for _ in range(reps)], nmax)
        tm += m1; tb += m2
        print(f"{name:<17}{s_mix:<22}{s_bet:<22}")
    print(f"{'mean stop':<17}{tm/len(MODELS):<22.1f}{tb/len(MODELS):<22.1f}  (fixed n=40)")

    print("\n=== INTERFERENCE: beta-mixture CS vs betting CS  (tau=0.30, alpha=eta/4) ===")
    CELLS = [("Haiku-4.5","blackwell_haiku_ss_n40.json","api_argorder"),
             ("Sonnet-4.6","blackwell_sonnet_ss_n40.json","api_post_ok"),
             ("Sonnet-4.6","blackwell_sonnet_ss_n40.json","api_argorder"),
             ("GPT-5.5","blackwell_gpt55_n40.json","api_post_ok"),
             ("DeepSeek-V4-Pro","blackwell_deepseek_n40.json","api_post_ok"),
             ("Kimi-K2.6","blackwell_kimi_n40.json","api_post_ok"),
             ("Opus-4.8","blackwell_opus_ss_n40.json","api_post_ok")]
    print(f"{'Model':<17}{'cell':<14}{'fixed':<8}{'mixture':<22}{'betting':<22}")
    for name, fn, cell in CELLS:
        c = load(fn)
        counts = {a: c[(a, cell)] for a in ["none", "W1", "W2", "W1plus"]}
        if fn == "blackwell_opus_ss_n40.json":
            rr = json.load(open(os.path.join(RES, "blackwell_opus_ss_W1plus.json")))
            counts["W1plus"] = (rr[cell]["pass"], rr[cell]["n"])
        nmax = min(n for _, n in counts.values())
        alpha = ETA / 4
        ivf = {a: cp_interval(*counts[a], alpha) for a in counts}
        upf = ivf["W1plus"][1] - ivf["W1"][0] - ivf["W2"][0] + ivf["none"][1]
        stark = all(S in (0, n) for S, n in counts.values())
        reps = 1 if stark else 200
        r1, r2 = random.Random(1), random.Random(1)
        s_mix, _ = summarize([seq_stop_interf(counts, alpha, 0.30, r1, nmax, "mixture") for _ in range(reps)], nmax)
        s_bet, _ = summarize([seq_stop_interf(counts, alpha, 0.30, r2, nmax, "betting") for _ in range(reps)], nmax)
        print(f"{name:<17}{cell:<14}{'YES' if upf <= -0.30 else 'no':<8}{s_mix:<22}{s_bet:<22}")



if __name__ == "__main__":
    main()