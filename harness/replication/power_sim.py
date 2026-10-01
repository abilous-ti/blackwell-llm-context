r"""Sample size for the replication, by simulation of the planned design and its analysis.

Each scenario fixes the true pass rates of the two compared conditions; every collection window
shifts both on the logit scale by a common random drift N(0, sigma_w^2), and, in the 'divergent'
setting, each condition by an extra independent N(0, sigma_c^2), so the effect itself moves between
windows. The 'one window lost' setting adds the operational failure the protocol allows for: one of
the planned windows yields no data (the primary analysis then averages the windows it has, with the
weighted bound). Blocks are simulated window by window and analysed with the rule of analyze.py: the
window-averaged block difference with the one-sided weighted Hoeffding bound at the per-statement
level of design.json (0.05 / 24), and the 0.30 margin for harm. Reported: the probability of
verifying the claim, for designs that fit the call budget with its retry headroom and for two larger
reference designs that do not. Scenarios come from the published record, including its weakest cells.

Usage:  python harness/replication/power_sim.py [reps]
"""
import io
import json
import math
import os
import random
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stats  # noqa: E402

SCENARIOS = [
    # label, kind, p_a, p_b (effect = p_a - p_b)
    ("harm, stark (1.00 -> 0.00)", "harm", 0.0, 1.0),
    ("harm, DeepSeek api_post_ok (0.75 -> 0.00)", "harm", 0.0, 0.75),
    ("harm, DeepSeek api_argorder (0.675 -> 0.05)", "harm", 0.05, 0.675),
    ("harm, weaker (0.60 -> 0.10)", "harm", 0.10, 0.60),
    ("advantage, stark (1.00 vs 0.00)", "adv", 1.0, 0.0),
    ("advantage, Haiku encoding (0.55 vs 0.00)", "adv", 0.55, 0.0),
    ("advantage, weaker (0.40 vs 0.05)", "adv", 0.40, 0.05),
]
SETTINGS = [("stable", 0.0, 0.0, 0), ("common drift", 0.5, 0.0, 0), ("divergent drift", 0.5, 0.3, 0),
            ("divergent, one window lost", 0.5, 0.3, 1)]


def shifted(p, u):
    if p <= 0.0 or p >= 1.0:
        return p
    z = math.log(p / (1 - p)) + u
    return 1 / (1 + math.exp(-z))


def power(p_a, p_b, kind, n_windows, bpw, alpha, margin, sigma_w, sigma_c, lost, reps, rng):
    hits = 0
    kept = n_windows - lost
    h = stats.weighted_hoeffding_halfwidth([bpw] * kept, alpha)
    for _ in range(reps):
        tot = 0.0
        for _w in range(kept):
            u = rng.gauss(0, sigma_w)
            pa = shifted(p_a, u + rng.gauss(0, sigma_c))
            pb = shifted(p_b, u + rng.gauss(0, sigma_c))
            s = 0
            for _b in range(bpw):
                s += (rng.random() < pa) - (rng.random() < pb)
            tot += s / bpw
        est = tot / kept
        if kind == "adv":
            hits += est - h > 0
        else:
            hits += est + h <= -margin
    return hits / reps


def main(reps=2000):
    design = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
    alpha = design["analysis"]["per_statement_alpha"]
    margin = design["analysis"]["harm_margin"]
    W, M = len(design["windows"]), len(design["models"])
    cap = design["budget"]["max_api_calls"]
    room = cap * (1 - design["budget"]["min_retry_headroom_fraction"])
    conds = sum(len(v) for v in design["cells"].values())
    grid = [24, 27, 30, 32, 40]
    rng = random.Random(7)
    print("Power of the primary rule (weighted Hoeffding, one-sided alpha = %.5f; harm margin %.2f; "
          "%d windows; %d reps)" % (alpha, margin, W, reps))
    print("Call budget %d; a schedule must leave %.0f%% for retries, i.e. at most %d requests." % (
        cap, 100 * design["budget"]["min_retry_headroom_fraction"], int(room)))
    designs = []
    for b in grid:
        for k in (conds, conds - 1):
            req = W * M * k * b
            designs.append({"blocks_per_window": b, "conditions": k, "n_per_condition": W * b,
                            "requests": req, "fits_budget": req <= room})
            print("  %2d blocks/window, %d conditions: n = %d per condition, %d requests%s" % (
                b, k, W * b, req, "" if req <= room else "  (exceeds the budget)"))
    print("\n  %-46s %-27s %s" % ("scenario", "setting", "  ".join("b=%-3d" % b for b in grid)))
    table = []
    for label, kind, pa, pb in SCENARIOS:
        for sname, sw, sc, lost in SETTINGS:
            row = [power(pa, pb, kind, W, b, alpha, margin, sw, sc, lost, reps, rng) for b in grid]
            table.append({"scenario": label, "setting": sname, "power": dict(zip(grid, row))})
            print("  %-46s %-27s %s" % (label, sname, "  ".join("%.2f " % p for p in row)))
    out = os.path.join(os.path.dirname(os.path.dirname(HERE)), "results", "replication", "power_sim.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"alpha": alpha, "margin": margin, "windows": W, "reps": reps, "blocks_per_window": grid,
               "call_budget": cap, "max_requests": int(room), "designs": designs, "rows": table},
              open(out, "w", encoding="utf-8"), indent=1)
    return table


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2000)
