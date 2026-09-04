"""PROBE-SELECT -- Algorithm 1 of the covering paper.

Builds the verified empirical dominance relation from a measured PASS table, prunes
verified-dominated sources, returns the non-dominated front (an antichain), and
coverage-diversifies over the front to a budget k.

Reuses the verification machinery (exact Clopper-Pearson + union bound) from
tokenbench.measure_blackwell; adds no new statistical assumptions.

The dominance relation follows the paper's definition: W_i >= W_j iff
  (a) delta_hat_D(W_i, W_j) <= alpha_tol   (no task where W_j beats W_i by more than the margin)
      -- certified by the upper bound U_D of certify_dominance; and
  (b) L_D(W_j, W_i) > 0                     (W_i strictly beats W_j on some task)
      -- certified by a verified lower bound on sup_T [p_i - p_j].

Usage:
  python tokenbench/probe_select.py results/blackwell_sonnet_ss_n40.json --k 2
  python tokenbench/probe_select.py results/*.json --k 2 --table
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tokenbench.measure_blackwell import clopper_pearson, certify_dominance  # noqa: E402


# ---------------------------------------------------------------------------
# data loading
# ---------------------------------------------------------------------------
def pr(kn):
    """Point pass rate from a (k, n) cell."""
    k, n = kn
    return 0.0 if n == 0 else k / n


def load_counts(path, merge=()):
    """Return (arms, tasks, n_per_cell) from a harness results JSON.

    arms[arm][task] = (k, n); tasks preserves first-seen order. Any files given in `merge`
    are applied on top, overriding cells of the same arm|task -- used where an arm was
    re-run in isolation after a transport outage.
    """
    with open(path, encoding="utf-8") as fh:
        blob = json.load(fh)
    raw = dict(blob.get("counts") or {})
    for extra in merge:
        arm = "W1plus"
        if ":" in extra:
            arm, extra = extra.split(":", 1)
        with open(extra, encoding="utf-8") as fh:
            eb = json.load(fh)
        if eb.get("counts"):
            raw.update(eb["counts"])
        else:
            # arm-only re-run: {task: {"pass": k, "n": n}}, arm implied
            for tid, cell in eb.items():
                if isinstance(cell, dict) and "pass" in cell and "n" in cell:
                    raw[f"{arm}|{tid}"] = [cell["pass"], cell["n"]]
    arms, tasks = {}, []
    for key, kn in raw.items():
        arm, task = key.split("|", 1)
        arms.setdefault(arm, {})[task] = tuple(kn)
        if task not in tasks:
            tasks.append(task)
    # keep only arms measured on every task (partial arm-only re-runs are skipped)
    full = {a: c for a, c in arms.items() if all(t in c for t in tasks)}
    return full, tasks, blob.get("n_per_cell")


# ---------------------------------------------------------------------------
# the verified dominance relation
# ---------------------------------------------------------------------------
def strict_win_lower(counts_a, counts_b, by_task, eta):
    """Verified lower bound on sup_T [p_a - p_b]. > 0 certifies A strictly beats B somewhere."""
    alpha = eta / max(1, len(by_task))
    best, arg = -1.0, None
    for tid in by_task:
        ka, na = counts_a[tid]
        kb, nb = counts_b[tid]
        a_lo, _ = clopper_pearson(ka, na, alpha)
        _, b_hi = clopper_pearson(kb, nb, alpha)
        gap = a_lo - b_hi
        if gap > best:
            best, arg = gap, tid
    return best, arg


def verified_dominates(a, b, arms, by_task, eta=0.10, alpha_tol=0.05):
    """Does A verifiably dominate B? Returns (bool, U_D, L_D, argmax task)."""
    up = certify_dominance(arms[a], arms[b], by_task, eta=eta)["U_D"]
    low, arg = strict_win_lower(arms[a], arms[b], by_task, eta)
    return (up <= alpha_tol and low > 0.0), up, low, arg


def build_relation(arms, by_task, eta=0.10, alpha_tol=0.05):
    """Pairwise verified dominance over candidate arms."""
    rel = {}
    names = list(arms)
    for a in names:
        for b in names:
            if a == b:
                continue
            ok, up, low, arg = verified_dominates(a, b, arms, by_task, eta, alpha_tol)
            rel[(a, b)] = {"dominates": ok, "U_D": up, "L_D": low, "arg": arg}
    return rel


def non_dominated(arms, rel):
    """The front: candidates not verifiably dominated by any other candidate."""
    front, pruned = [], {}
    for w in arms:
        killers = [v for v in arms if v != w and rel[(v, w)]["dominates"]]
        if killers:
            pruned[w] = killers
        else:
            front.append(w)
    return front, pruned


# ---------------------------------------------------------------------------
# coverage-diversified selection over the front
# ---------------------------------------------------------------------------
def routed_pass(selected, arms, by_task):
    """PASS of a selected SET under per-task routing: best member on each task."""
    if not selected:
        return {t: 0.0 for t in by_task}
    return {t: max(pr(arms[w][t]) for w in selected) for t in by_task}


def verified_pass_lower(kn, alpha):
    """Verified lower bound on a cell's PASS rate."""
    k, n = kn
    return clopper_pearson(k, n, alpha)[0]


def greedy_cover(front, arms, by_task, k, eta=0.10, verified=True):
    """Greedy max-coverage over the front (Proposition: (1-1/e), tight by Feige).

    With verified=True the marginal gain uses Clopper-Pearson LOWER bounds rather than point
    estimates, matching the paper's "largest verified marginal PASS gain". This matters: on
    point estimates a candidate can win the greedy step by a margin far inside its confidence
    interval, which is not a decision the data supports.
    """
    alpha = eta / max(1, len(by_task) * max(1, len(front)))
    score = {}
    for w in front:
        score[w] = {t: (verified_pass_lower(arms[w][t], alpha) if verified else pr(arms[w][t]))
                    for t in by_task}

    chosen, cur = [], {t: 0.0 for t in by_task}
    while len(chosen) < min(k, len(front)):
        best_w, best_gain = None, 0.0
        for w in front:
            if w in chosen:
                continue
            gain = sum(max(0.0, score[w][t] - cur[t]) for t in by_task)
            if gain > best_gain:
                best_gain, best_w = gain, w
        if best_w is None:
            break
        chosen.append(best_w)
        for t in by_task:
            cur[t] = max(cur[t], score[best_w][t])
    # report realized routed PASS (point estimates) for the chosen set
    return chosen, routed_pass(chosen, arms, by_task)


def probe_select(arms, by_task, k=2, eta=0.10, alpha_tol=0.05, verified=True):
    """Algorithm 1 end to end."""
    rel = build_relation(arms, by_task, eta, alpha_tol)
    front, pruned = non_dominated(arms, rel)
    chosen, cur = greedy_cover(front, arms, by_task, k, eta=eta, verified=verified)
    return {
        "relation": rel,
        "front": front,
        "pruned": pruned,
        "selected": chosen,
        "routed_pass": cur,
        "mean_pass": sum(cur.values()) / len(by_task) if by_task else 0.0,
    }


# ---------------------------------------------------------------------------
# baseline selection policies, for the comparison table
# ---------------------------------------------------------------------------
def policy_scores(arms, by_task, k=2, eta=0.10, alpha_tol=0.05, superset="W1plus"):
    """Mean PASS over tasks for each selection policy."""
    cands = [a for a in arms if a != "none"]
    sub = {a: arms[a] for a in cands}
    out = {}

    # best single fixed source (the oracle-best any query-independent scalar could pick)
    best_fixed, best_mean = None, -1.0
    for w in cands:
        m = sum(pr(arms[w][t]) for t in by_task) / len(by_task)
        if m > best_mean:
            best_mean, best_fixed = m, w
    out["best_fixed"] = {"value": best_mean, "pick": best_fixed}

    # concatenate everything (the "more signal is better" heuristic)
    if superset in arms:
        out["concatenate"] = {
            "value": sum(pr(arms[superset][t]) for t in by_task) / len(by_task),
            "pick": superset,
        }

    # Probe-Select: verified front + per-task routing
    res = probe_select(sub, by_task, k=k, eta=eta, alpha_tol=alpha_tol)
    out["probe_select"] = {
        "value": res["mean_pass"],
        "pick": res["selected"],
        "front": res["front"],
        "pruned": res["pruned"],
    }
    return out, res


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def run_one(path, k, eta, alpha_tol, verbose=True, merge=()):
    arms, tasks, n = load_counts(path, merge=merge)
    if not arms or not tasks:
        return None
    pol, res = policy_scores(arms, tasks, k=k, eta=eta, alpha_tol=alpha_tol)
    label = Path(path).stem
    if verbose:
        print(f"\n=== {label}  (n={n}, tasks={len(tasks)}, arms={sorted(arms)}) ===")
        print(f"  front      : {res['front']}")
        if res["pruned"]:
            for w, killers in res["pruned"].items():
                print(f"  pruned     : {w}  (dominated by {', '.join(killers)})")
        else:
            print("  pruned     : none")
        print(f"  selected   : {res['selected']}  (k={k})")
        print("  routed PASS per task:")
        for t in tasks:
            print(f"      {t:<18} {res['routed_pass'][t]*100:5.1f}%")
        print("  --- policy comparison (mean PASS over tasks) ---")
        for name in ("best_fixed", "concatenate", "probe_select"):
            if name in pol:
                v = pol[name]
                print(f"      {name:<14} {v['value']*100:5.1f}%   pick={v['pick']}")
    return {"label": label, "n": n, "tasks": tasks, "policies": pol, "result": res}


def main():
    ap = argparse.ArgumentParser(description="Probe-Select over measured PASS tables.")
    ap.add_argument("paths", nargs="+", help="harness results JSON file(s); globs allowed")
    ap.add_argument("--k", type=int, default=2, help="selection budget")
    ap.add_argument("--eta", type=float, default=0.10, help="confidence budget")
    ap.add_argument("--alpha-tol", type=float, default=0.05, help="equivalence margin")
    ap.add_argument("--table", action="store_true", help="print a summary table across files")
    ap.add_argument("--json-out", default=None, help="write full results to this path")
    ap.add_argument("--merge", nargs="*", default=[],
                    help="extra results files whose cells override (arm-only re-runs)")
    a = ap.parse_args()

    files = []
    for p in a.paths:
        files.extend(sorted(glob.glob(p)) or [p])

    rows = []
    for f in files:
        try:
            r = run_one(f, a.k, a.eta, a.alpha_tol, verbose=not a.table, merge=a.merge)
        except Exception as exc:  # a partial/arm-only file is expected to be skipped
            print(f"  [skip] {Path(f).name}: {exc}")
            continue
        if r:
            rows.append(r)

    if a.table and rows:
        print(f"\n{'run':<32} {'best fixed':>11} {'concat':>9} {'Probe-Select':>13}  selected")
        print("-" * 92)
        for r in rows:
            p = r["policies"]
            bf = p["best_fixed"]["value"] * 100
            cc = p.get("concatenate", {}).get("value")
            ps = p["probe_select"]["value"] * 100
            cc_s = f"{cc*100:8.1f}" if cc is not None else "       -"
            print(f"{r['label']:<32} {bf:10.1f} {cc_s} {ps:12.1f}  "
                  f"{'+'.join(p['probe_select']['pick'])}")

    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump(
                [{"label": r["label"], "n": r["n"], "tasks": r["tasks"],
                  "policies": {k2: {kk: vv for kk, vv in v.items() if kk != "front"}
                               for k2, v in r["policies"].items()},
                  "front": r["result"]["front"],
                  "pruned": r["result"]["pruned"],
                  "selected": r["result"]["selected"],
                  "routed_pass": r["result"]["routed_pass"]} for r in rows],
                fh, indent=1)
        print(f"\nwrote {a.json_out}")


if __name__ == "__main__":
    main()
