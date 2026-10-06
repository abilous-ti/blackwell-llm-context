r"""Channel-matrix certificate of Blackwell incomparability for the declared pair families.

For each pair (cache, inventory, audit) the state space is the product of the declared families,
and each source is the deterministic channel from a state to its rendered text (pairs.py). For each
direction a linear program computes the exact Le Cam deficiency
    delta(W, W') = min over stochastic G  max over states s  TV(G kappa_W(s), kappa_W'(s)),
with TV the supremum over events (half the L1 distance). delta(W, W') = 0 would mean W' is a
garbling of W; a positive optimum in both directions certifies incomparability for the generator.
For deterministic injective renderings on a product space the optimum is 1 - 1/N, N the number of
states of the other source's coordinate; the program confirms it numerically.

  python harness/package2/channel_certificate.py      (writes results/package2/channel_certificate.json)
"""
import io
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import pairs as P  # noqa: E402

OUT = ROOT / "results" / "package2" / "channel_certificate.json"


def channels(pid):
    p = P.PAIRS[pid]
    a_states, b_states = P.states(p["A_space"]), P.states(p["B_space"])
    states = [(a, b) for a in a_states for b in b_states]
    ta = [p["render_a"](a) for a, _ in states]
    tb = [p["render_b"](b) for _, b in states]
    ia = {t: i for i, t in enumerate(sorted(set(ta)))}
    ib = {t: i for i, t in enumerate(sorted(set(tb)))}
    return [ia[t] for t in ta], [ib[t] for t in tb], len(ia), len(ib), len(states)


def deficiency(src, dst, n_src, n_dst):
    """Exact delta(W_src, W_dst) for deterministic channels: states map to text indices src[s], dst[s].
    Variables: G (n_src x n_dst, row-stochastic), u_{s,j} >= |G[src[s], j] - 1[j == dst[s]]|, t."""
    S = len(src)
    nG, nU = n_src * n_dst, S * n_dst
    nv = nG + nU + 1
    c = np.zeros(nv)
    c[-1] = 1.0
    A_ub, b_ub = [], []
    for s in range(S):
        for j in range(n_dst):
            g = src[s] * n_dst + j
            u = nG + s * n_dst + j
            e = 1.0 if j == dst[s] else 0.0
            row = np.zeros(nv); row[g] = 1.0; row[u] = -1.0; A_ub.append(row); b_ub.append(e)      # G - e <= u
            row = np.zeros(nv); row[g] = -1.0; row[u] = -1.0; A_ub.append(row); b_ub.append(-e)    # e - G <= u
        row = np.zeros(nv)
        row[nG + s * n_dst: nG + (s + 1) * n_dst] = 0.5
        row[-1] = -1.0
        A_ub.append(row); b_ub.append(0.0)                                                          # TV_s <= t
    A_eq, b_eq = [], []
    for i in range(n_src):
        row = np.zeros(nv); row[i * n_dst:(i + 1) * n_dst] = 1.0; A_eq.append(row); b_eq.append(1.0)
    bounds = [(0, 1)] * nG + [(0, None)] * nU + [(0, None)]
    r = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), A_eq=np.array(A_eq), b_eq=np.array(b_eq),
                bounds=bounds, method="highs")
    assert r.status == 0, r.message
    return float(r.fun)


def main():
    res = {}
    for pid in ("cache", "inventory", "audit"):
        a, b, na, nb, S = channels(pid)
        d_ab = deficiency(a, b, na, nb)     # can B be obtained from A?
        d_ba = deficiency(b, a, nb, na)     # can A be obtained from B?
        res[pid] = {"states": S, "A_texts": na, "B_texts": nb,
                    "delta(W_A,W_B)": round(d_ab, 6), "closed_form_1_minus_1_over_NB": round(1 - 1 / nb, 6),
                    "delta(W_B,W_A)": round(d_ba, 6), "closed_form_1_minus_1_over_NA": round(1 - 1 / na, 6),
                    "incomparable": d_ab > 1e-9 and d_ba > 1e-9}
        print("%-10s states %3d | delta(A,B) = %.4f (1-1/%d) | delta(B,A) = %.4f (1-1/%d) | incomparable: %s" % (
            pid, S, d_ab, nb, d_ba, na, res[pid]["incomparable"]))
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
