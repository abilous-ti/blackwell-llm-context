"""
PROSPECTIVE validation on the REAL draw order (no permutation).
Loads a harness JSON that carries "draws" and runs the exact sequential rules on the
observed sequence, for both CS constructions. Compares to the retrospective prediction.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from seq_replay import av_interval, cp_interval, L_D, ETA
from seq_betting import betting_interval

P = sys.argv[1] if len(sys.argv) > 1 else \
    r'C:\Users\AndriyBilous\Documents\GitHub\blackwell-llm-context\results\blackwell_haiku_seq_n40.json'
d = json.load(open(P))
draws = {tuple(k.split("|", 1)): v for k, v in d["draws"].items()}
tasks = sorted({t for (a, t) in draws})
nmax = min(len(v) for v in draws.values())
print(f"file: {os.path.basename(P)}   n={nmax}/cell   cells={len(draws)}")
print("per-cell PASS:", {f"{a}|{t}": f"{sum(v)}/{len(v)}" for (a, t), v in sorted(draws.items())})


def ivs(method, n, alpha, keys):
    out = {}
    for k in keys:
        seq = draws[k][:n]
        out[k] = av_interval(sum(seq), n, alpha) if method == "mixture" else betting_interval(seq, alpha)
    return out


# ---- incomparability (W1 vs W2 over the task family) ----
alpha_i = ETA / (2 * len(tasks))
keys_i = [(a, t) for a in ("W1", "W2") for t in tasks]
ivf = {k: cp_interval(sum(draws[k]), nmax, alpha_i) for k in keys_i}
print(f"\nINCOMPARABILITY  fixed n={nmax}: L_D = +{L_D(ivf,'W1','W2',tasks):.2f} / +{L_D(ivf,'W2','W1',tasks):.2f}"
      f"  -> {'VERIFIED' if min(L_D(ivf,'W1','W2',tasks), L_D(ivf,'W2','W1',tasks)) > 0 else 'not verified'}")
for method in ("mixture", "betting"):
    stop = None
    for n in range(1, nmax + 1):
        iv = ivs(method, n, alpha_i, keys_i)
        if L_D(iv, "W1", "W2", tasks) > 0 and L_D(iv, "W2", "W1", tasks) > 0:
            stop = n; break
    print(f"  sequential [{method:<7}] on REAL order: stop at n={stop}   "
          f"(retrospective prediction for Haiku: n=10)")

# two-stage alpha/2 rule (the rule the paper recommends), on the REAL order
a1 = a2 = alpha_i / 2
stop2 = None
for n in range(1, nmax + 1):
    iv = {k: av_interval(sum(draws[k][:n]), n, a1) for k in keys_i}
    if L_D(iv, "W1", "W2", tasks) > 0 and L_D(iv, "W2", "W1", tasks) > 0:
        stop2 = n; break
if stop2 is None:
    ivf2 = {k: cp_interval(sum(draws[k]), nmax, a2) for k in keys_i}
    ok2 = L_D(ivf2, "W1", "W2", tasks) > 0 and L_D(ivf2, "W2", "W1", tasks) > 0
    print(f"  two-stage  [alpha/2] on REAL order: no stage-1 stop; stage-2 at n={nmax}: "
          f"{'VERIFIED' if ok2 else 'NOT verified'}   (retrospective prediction: n=11)")
else:
    print(f"  two-stage  [alpha/2] on REAL order: stage-1 stop at n={stop2}   "
          f"(retrospective prediction: n=11)")

# ---- interference on each carrying cell ----
alpha_f = ETA / 4
arms = ["none", "W1", "W2", "W1plus"]
print(f"\nINTERFERENCE (tau=0.30):")
for t in tasks:
    keys_f = [(a, t) for a in arms]
    if not all(k in draws for k in keys_f):
        continue
    ivf = {k: cp_interval(sum(draws[k]), nmax, alpha_f) for k in keys_f}
    upf = ivf[("W1plus", t)][1] - ivf[("W1", t)][0] - ivf[("W2", t)][0] + ivf[("none", t)][1]
    p = {a: sum(draws[(a, t)]) / nmax for a in arms}
    psi = p["W1plus"] - p["W1"] - p["W2"] + p["none"]
    line = f"  {t:<16} Psi={psi:+.2f} fixed-upper={upf:+.2f} {'VERIFIED' if upf <= -0.30 else 'no':<9}"
    for method in ("mixture", "betting"):
        stop = None
        for n in range(1, nmax + 1):
            iv = ivs(method, n, alpha_f, keys_f)
            up = iv[("W1plus", t)][1] - iv[("W1", t)][0] - iv[("W2", t)][0] + iv[("none", t)][1]
            if up <= -0.30:
                stop = n; break
        line += f"  {method}:{'n=%d' % stop if stop else 'no':<6}"
    print(line)
