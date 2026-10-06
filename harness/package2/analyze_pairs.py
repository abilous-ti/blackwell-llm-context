r"""Analysis of the independent-pair experiment, as fixed in PROTOCOL.md (Section 1).

Primary (36 one-sided statements, alpha = 0.05/36 each): for each pair and model, the A-decisive
advantage A - B on the A-task and the B-decisive advantage B - A on the B-task, from complete blocks
under the hardened checks, with the Hoeffding bound of the replication for one window,
h = sqrt(2 log(1/alpha) / B). A pair is PASS-incomparable for a model when both are verified.

Secondary (each family at its own Bonferroni level, never part of the primary claim):
  augmentation  AB - A and BA - A on the A-task, AB - B and BA - B on the B-task (72; any harm);
  controls      W1plus - W1, W1plus_rev - W1, W1pad - W1 on the two ledger tasks (36; two-sided);
  pooled        Clopper-Pearson comparison of the pooled counts, for comparability with the paper;
  published     the primary statements graded with the published checks (cache and ledger);
  worst case    every scheduled block, missing outcomes imputed against the claim;
plus no-context baselines and the replies whose published and hardened grades differ.

  python harness/package2/analyze_pairs.py [record_dir]     (default results/package2/confirm_pairs)
"""
import io
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import pairs as P  # noqa: E402
import measure_blackwell as mb  # noqa: E402

MODELS = ["Haiku-4.5", "Sonnet-4.6", "Opus-4.8", "GPT-5.5", "DeepSeek-V4-Pro", "Kimi-K2.6"]
PAIR_IDS = ("cache", "inventory", "audit")


def task_ids(pid):
    ts = P.PAIRS[pid]["tasks"]
    return next(t["id"] for t in ts if t["decisive"] == "A"), next(t["id"] for t in ts if t["decisive"] == "B")


def load(d):
    rec, grd = {}, {}
    for line in open(Path(d) / "records.jsonl", encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("type") == "receipt":
            rec[r["id"]] = r
        elif r.get("type") == "grade":
            grd[r["id"]] = r
    sched = [json.loads(l) for l in open(Path(d) / "schedule.jsonl", encoding="utf-8") if l.strip()]
    return rec, grd, sched


def outcomes(rec, grd, sched, key):
    """{(model, group, task, block): {arm: 0/1}} for graded requests; key = pass or pass_hardened."""
    out = defaultdict(dict)
    for s in sched:
        g = grd.get(s["id"])
        if g is None or rec.get(s["id"], {}).get("transport_failed"):
            continue
        out[(s["model"], s["group"], s["task"], s["block"])][s["arm"]] = int(bool(g.get(key, g["pass"])))
    return out


def scheduled_blocks(sched):
    b = defaultdict(set)
    for s in sched:
        b[(s["model"], s["group"], s["task"])].add(s["block"])
    return b


def contrast(Y, blocks_all, model, group, task, a, b, direction, alpha, worst_case=False, two_sided=False):
    diffs = []
    for blk in sorted(blocks_all[(model, group, task)]):
        ys = Y.get((model, group, task, blk), {})
        ya, yb = ys.get(a), ys.get(b)
        if ya is None or yb is None:
            if not worst_case:
                continue
            if direction > 0:
                ya, yb = (0 if ya is None else ya), (1 if yb is None else yb)
            else:
                ya, yb = (1 if ya is None else ya), (0 if yb is None else yb)
        diffs.append(ya - yb)
    B = len(diffs)
    if B == 0:
        return {"blocks": 0, "estimate": None, "bound": None, "verified": None}
    est = sum(diffs) / B
    h = math.sqrt(2 * math.log((2 if two_sided else 1) / alpha) / B)
    out = {"blocks": B, "estimate": est, "halfwidth": h}
    if two_sided:
        out.update(lower=est - h, upper=est + h, verified=(est - h > 0) or (est + h < 0))
    elif direction > 0:
        out.update(bound=est - h, verified=est - h > 0)
    else:
        out.update(bound=est + h, verified=est + h < 0)
    return out


def pooled_cp(Y, model, group, task, a, b, direction, alpha):
    k = {a: [0, 0], b: [0, 0]}
    for (m, g, t, _blk), ys in Y.items():
        if (m, g, t) != (model, group, task):
            continue
        for arm in (a, b):
            if arm in ys:
                k[arm][0] += ys[arm]
                k[arm][1] += 1
    if not k[a][1] or not k[b][1]:
        return None
    la, ua = mb.clopper_pearson(k[a][0], k[a][1], alpha)
    lb, ub = mb.clopper_pearson(k[b][0], k[b][1], alpha)
    return {"counts": {a: k[a], b: k[b]}, "bound": (la - ub) if direction > 0 else (ua - lb)}


def analyze(d):
    rec, grd, sched = load(d)
    blocks_all = scheduled_blocks(sched)
    Yh = outcomes(rec, grd, sched, "pass_hardened")
    Yp = outcomes(rec, grd, sched, "pass")
    a1 = 0.05 / 36
    res = {"primary": [], "augmentation": [], "controls": [], "baselines": [], "grading_differences": []}
    for pid in PAIR_IDS:
        ta, tb = task_ids(pid)
        for m in MODELS:
            row = {"pair": pid, "model": m}
            for name, task, a, b in (("A_adv", ta, "A", "B"), ("B_adv", tb, "B", "A")):
                c = contrast(Yh, blocks_all, m, pid, task, a, b, +1, a1)
                c["worst_case"] = contrast(Yh, blocks_all, m, pid, task, a, b, +1, a1, worst_case=True)
                c["published"] = contrast(Yp, blocks_all, m, pid, task, a, b, +1, a1)
                c["pooled_cp"] = pooled_cp(Yh, m, pid, task, a, b, +1, a1)
                row[name] = c
            row["pass_incomparable"] = bool(row["A_adv"]["verified"] and row["B_adv"]["verified"])
            res["primary"].append(row)
            for task, base in ((ta, "A"), (tb, "B")):
                for combo in ("AB", "BA"):
                    c = contrast(Yh, blocks_all, m, pid, task, combo, base, -1, 0.05 / 72)
                    res["augmentation"].append(dict(c, pair=pid, model=m, task=task, contrast="%s - %s" % (combo, base)))
                n = Counter()
                for (mm, g, t, _b), ys in Yh.items():
                    if (mm, g, t) == (m, pid, task) and "none" in ys:
                        n["k"] += ys["none"]
                        n["n"] += 1
                res["baselines"].append({"pair": pid, "model": m, "task": task, "none": [n["k"], n["n"]]})
    for task in ("api_post_ok", "api_argorder"):
        for m in MODELS:
            for arm in ("W1plus", "W1plus_rev", "W1pad"):
                c = contrast(Yh, blocks_all, m, "ledger_controls", task, arm, "W1", 0, 0.05 / 36, two_sided=True)
                c["published"] = contrast(Yp, blocks_all, m, "ledger_controls", task, arm, "W1", 0, 0.05 / 36, two_sided=True)
                res["controls"].append(dict(c, model=m, task=task, contrast="%s - W1" % arm))
    for i, g in grd.items():
        if "pass_hardened" in g and bool(g["pass"]) != bool(g["pass_hardened"]):
            r = rec[i]
            res["grading_differences"].append({"id": i, "published": g["pass"], "hardened": g["pass_hardened"]})
    res["n"] = {"scheduled": len(sched), "received": len(rec), "graded": len(grd),
                "transport_failed": sum(1 for r in rec.values() if r.get("transport_failed"))}
    return res


def fmt(x, nd=2):
    return "-" if x is None else ("%+.*f" % (nd, x))


def report(res):
    L = ["requests: scheduled %(scheduled)d, received %(received)d, graded %(graded)d, transport failures %(transport_failed)d" % res["n"], ""]
    L.append("PRIMARY: PASS incomparability (hardened checks; alpha = 0.05/36 per statement)")
    L.append("%-10s %-16s %-30s %-30s %s" % ("pair", "model", "A - B on A-task (B, est, bound)", "B - A on B-task (B, est, bound)", "incomparable"))
    for r in res["primary"]:
        cells = []
        for k in ("A_adv", "B_adv"):
            c = r[k]
            cells.append("%3s %s %s %s" % (c["blocks"], fmt(c["estimate"]), fmt(c.get("bound")), "yes" if c["verified"] else "no"))
        L.append("%-10s %-16s %-30s %-30s %s" % (r["pair"], r["model"], cells[0], cells[1], "YES" if r["pass_incomparable"] else "no"))
    n_inc = sum(r["pass_incomparable"] for r in res["primary"])
    L.append("pair-model combinations verified PASS-incomparable: %d of %d" % (n_inc, len(res["primary"])))
    wc = sum(1 for r in res["primary"] if all(r[k]["worst_case"]["verified"] == r[k]["verified"] for k in ("A_adv", "B_adv")))
    pub = sum(1 for r in res["primary"] if all(r[k]["published"]["verified"] == r[k]["verified"] for k in ("A_adv", "B_adv")))
    L.append("decisions unchanged under worst-case imputation: %d of %d; under the published checks: %d of %d" % (
        wc, len(res["primary"]), pub, len(res["primary"])))
    L.append("")
    L.append("SECONDARY: augmentation (estimate, upper bound at alpha = 0.05/72, harm verified?)")
    for r in res["augmentation"]:
        L.append("  %-10s %-16s %-14s %-8s B=%3s %s %s %s" % (r["pair"], r["model"], r["task"], r["contrast"], r["blocks"],
                                                        fmt(r["estimate"]), fmt(r.get("bound")), "HARM" if r["verified"] else ""))
    L.append("")
    L.append("SECONDARY: ledger controls (estimate, two-sided interval at alpha = 0.05/36)")
    for r in res["controls"]:
        L.append("  %-16s %-13s %-15s B=%3s %s [%s, %s] %s" % (r["model"], r["task"], r["contrast"], r["blocks"], fmt(r["estimate"]),
                                                          fmt(r.get("lower")), fmt(r.get("upper")), "verified" if r["verified"] else ""))
    L.append("")
    L.append("No-context baselines (passes / graded): " + "; ".join(
        "%s %s %s %d/%d" % (b["pair"], b["task"], b["model"], b["none"][0], b["none"][1]) for b in res["baselines"] if b["none"][0]))
    L.append("Replies graded differently by the published and hardened checks: %d" % len(res["grading_differences"]))
    return "\n".join(L)


def main():
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results" / "package2" / "confirm_pairs"
    res = analyze(d)
    text = report(res)
    (d / "analysis_pairs.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (d / "analysis_pairs.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
