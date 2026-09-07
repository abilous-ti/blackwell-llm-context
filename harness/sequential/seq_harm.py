# Interference under the TWO-ARM direct contrast (Psi is interaction, not harm): harm(T) = PASS(W1+) - PASS(W1).
# Verified harm iff hi(W1+) - lo(W1) <= -tau with two intervals at alpha = eta/2 each (union bound).
# Sequential: mixture CS in flight; two-stage = alpha/2 in flight + fixed CP alpha/2 at nmax.
import json, os, random, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seq_replay import av_interval, cp_interval, load, draws, RES, ETA
CELLS = [("Haiku-4.5","blackwell_haiku_ss_n40.json","api_argorder"),("Sonnet-4.6","blackwell_sonnet_ss_n40.json","api_post_ok"),
         ("Sonnet-4.6","blackwell_sonnet_ss_n40.json","api_argorder"),("GPT-5.5","blackwell_gpt55_n40.json","api_post_ok"),
         ("DeepSeek-V4-Pro","blackwell_deepseek_n40.json","api_post_ok"),("Kimi-K2.6","blackwell_kimi_n40.json","api_post_ok"),
         ("Opus-4.8","blackwell_opus_ss_n40.json","api_post_ok")]
TAU, alpha = 0.30, ETA / 2
def main():
    print(f"{'Model':<16}{'cell':<14}{'harm':>6}{'fixed-upper':>12}{'verdict':>9}   mixture stop   two-stage(a/2)")
    tf = ts = 0
    for name, fn, cell in CELLS:
        c = load(fn); w1, wp = c[("W1", cell)], c[("W1plus", cell)]
        if fn == "blackwell_opus_ss_n40.json":
            rr = json.load(open(os.path.join(RES, "blackwell_opus_ss_W1plus.json"))); wp = (rr[cell]["pass"], rr[cell]["n"])
        nmax = min(w1[1], wp[1]); harm = wp[0]/wp[1] - w1[0]/w1[1]
        up = cp_interval(*wp, alpha)[1] - cp_interval(*w1, alpha)[0]; ver = up <= -TAU
        stark = all(S in (0, n) for S, n in (w1, wp)); reps = 1 if stark else 400
        def stop(rng, a1, twostage):
            s1, sp = draws(*w1, rng), draws(*wp, rng); k1 = kp = 0
            for n in range(1, nmax + 1):
                k1 += s1[n-1]; kp += sp[n-1]
                if av_interval(kp, n, a1)[1] - av_interval(k1, n, a1)[0] <= -TAU: return n, "stage1"
            if twostage and cp_interval(kp, nmax, a1)[1] - cp_interval(k1, nmax, a1)[0] <= -TAU: return nmax, "stage2-verified"
            return nmax, "NOT"
        r1, r2 = random.Random(1), random.Random(1)
        m = sorted(stop(r1, alpha, False)[0] for _ in range(reps))[reps//2]
        res = [stop(r2, alpha/2, True) for _ in range(reps)]
        m2 = sorted(n for n, _ in res)[reps//2]; kinds = {k: sum(1 for _, kk in res if kk == k) for k in set(k for _, k in res)}
        if ver: tf += nmax * 2; ts += m2 * 2
        print(f"{name:<16}{cell:<14}{harm:>+6.2f}{up:>+12.2f}{'YES' if ver else 'no':>9}   n={m:<11} n={m2} {kinds}")
    print(f"verified cells: fixed {tf} -> two-stage {ts} calls ({tf/max(ts,1):.2f}x)   [four-term Psi bound gave only 1.2x]")
if __name__ == "__main__":
    main()
