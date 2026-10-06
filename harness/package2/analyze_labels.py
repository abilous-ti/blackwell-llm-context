r"""Analysis of the declarative label experiment, as fixed in PROTOCOL_LABELS.md (Section 4).

Primary (24 one-sided statements: 2 pairs x 2 label tasks x 6 models, alpha = 0.05/24 each): the
one-sided Clopper-Pearson lower bound L on the own-source accuracy; verified when L > cap (cap =
1/N, proved by enumeration in labels.certify()). On the coverage event, the directional deficiency
of the other source relative to the own source is at least max(0, L - cap). A pair is certified
incomparable for a model when both of its statements are verified (simultaneous over all 24).

Diagnostics (own error budget, 0.05/48, one-sided): other-source and no-context accuracy whose CP
lower bound exceeds the cap is flagged as evidence against the combined assumptions.
Secondary: own minus other-source accuracy per task (fixed-model comparison over the hidden
states; block-difference Hoeffding bound, alpha = 0.05/24, complete blocks).
Sensitivity: the primary with every missing own-source outcome counted as incorrect.
Descriptive: per-state own-source accuracy (no simultaneous coverage), choices without the source,
invalid replies.

  python harness/package2/analyze_labels.py [record_dir]     (default results/package2/confirm_labels)
"""
import io
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import labels as L  # noqa: E402
import measure_blackwell as mb  # noqa: E402

MODELS = ["Haiku-4.5", "Sonnet-4.6", "Opus-4.8", "GPT-5.5", "DeepSeek-V4-Pro", "Kimi-K2.6"]
ALPHA = 0.05 / 24
ALPHA_DIAG = 0.05 / 48


def cp_lower(k, n, alpha):
    """One-sided lower confidence bound at level alpha (mb.clopper_pearson is two-sided)."""
    return mb.clopper_pearson(k, n, 2 * alpha)[0] if n else None


def load(d):
    d = Path(d)
    sched = [json.loads(l) for l in open(d / "schedule.jsonl", encoding="utf-8") if l.strip()]
    rec, grd = {}, {}
    for line in open(d / "records.jsonl", encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("type") == "receipt":
            rec[r["id"]] = r
        elif r.get("type") == "grade":
            grd[r["id"]] = r
    return sched, rec, grd


def analyze(d):
    sched, rec, grd = load(d)
    caps = L.caps()
    tasks = [(pid, x, L.TASKS[(pid, x)]["id"]) for pid in L.PAIR_IDS for x in ("A", "B")]
    cell = defaultdict(list)         # (model, task, arm) -> [(block, correct)]
    sched_n = Counter()
    per_state = defaultdict(lambda: [0, 0])
    choices = defaultdict(Counter)
    invalid = Counter()
    for s in sched:
        sched_n[(s["model"], s["task"], s["arm"])] += 1
        g = grd.get(s["id"])
        if g is None or rec.get(s["id"], {}).get("transport_failed"):
            continue
        cell[(s["model"], s["task"], s["arm"])].append((s["block"], bool(g["correct"])))
        if g.get("choice") is None:
            invalid[(s["model"], s["arm"] == s["source"])] += 1
        if s["arm"] == s["source"]:
            key = s["a_key"] if s["source"] == "A" else s["b_key"]
            per_state[(s["model"], s["task"], key)][0] += bool(g["correct"])
            per_state[(s["model"], s["task"], key)][1] += 1
        if s["arm"] == "none":
            choices[(s["model"], s["task"])][g.get("choice")] += 1
    res = {"n": {"scheduled": len(sched), "received": len(rec), "graded": len(grd),
                 "transport_failed": sum(1 for r in rec.values() if r.get("transport_failed"))},
           "caps": caps, "primary": [], "certified_pairs": [], "diagnostics": [], "secondary": [],
           "per_state": [], "none_choices": [], "invalid": []}
    verified = {}
    for m in MODELS:
        for pid, x, tid in tasks:
            own = cell.get((m, tid, x), [])
            k, n = sum(c for _, c in own), len(own)
            lo = cp_lower(k, n, ALPHA)
            n_wc = sched_n[(m, tid, x)]
            lo_wc = cp_lower(k, n_wc, ALPHA)
            v = lo is not None and lo > caps[tid]
            verified[(m, pid, x)] = v
            res["primary"].append({
                "model": m, "pair": pid, "task": tid, "own": x, "other": "B" if x == "A" else "A",
                "k": k, "n": n, "accuracy": k / n if n else None, "cp_lower": lo, "cap": caps[tid],
                "verified": v, "deficiency_lower_bound": max(0.0, lo - caps[tid]) if lo is not None else None,
                "bound_direction": "delta(E_%s, E_%s)" % ("B" if x == "A" else "A", x),
                "worst_case": {"k": k, "n": n_wc, "cp_lower": lo_wc,
                               "verified": lo_wc is not None and lo_wc > caps[tid]}})
            for arm in ("none", "B" if x == "A" else "A"):
                c = cell.get((m, tid, arm), [])
                kk, nn = sum(v2 for _, v2 in c), len(c)
                lo2 = cp_lower(kk, nn, ALPHA_DIAG)
                res["diagnostics"].append({"model": m, "task": tid, "arm": arm, "k": kk, "n": nn,
                                           "cp_lower": lo2, "cap": caps[tid],
                                           "flag": lo2 is not None and lo2 > caps[tid]})
            other = "B" if x == "A" else "A"
            ob = dict(cell.get((m, tid, x), []))
            oo = dict(cell.get((m, tid, other), []))
            diffs = [int(ob[b]) - int(oo[b]) for b in sorted(set(ob) & set(oo))]
            if diffs:
                est = sum(diffs) / len(diffs)
                h = math.sqrt(2 * math.log(1 / ALPHA) / len(diffs))
                res["secondary"].append({"model": m, "task": tid, "blocks": len(diffs), "estimate": est,
                                         "bound": est - h, "verified": est - h > 0})
        for pid in L.PAIR_IDS:
            res["certified_pairs"].append({"model": m, "pair": pid,
                                           "certified_incomparable": bool(verified[(m, pid, "A")] and verified[(m, pid, "B")])})
    for (m, t, key), (k, n) in sorted(per_state.items()):
        res["per_state"].append({"model": m, "task": t, "state": key, "k": k, "n": n})
    for (m, t), c in sorted(choices.items()):
        res["none_choices"].append({"model": m, "task": t, "choices": {str(a): b for a, b in sorted(c.items(), key=lambda z: str(z[0]))}})
    for (m, own), k in sorted(invalid.items()):
        res["invalid"].append({"model": m, "own_source_arm": own, "count": k})
    return res


def fmt(x, nd=3):
    return "-" if x is None else "%.*f" % (nd, x)


def report(res):
    Ln = ["requests: scheduled %(scheduled)d, received %(received)d, graded %(graded)d, transport failures %(transport_failed)d" % res["n"], ""]
    Ln.append("PRIMARY: own-source accuracy vs proved cap (one-sided CP, alpha = 0.05/24 each)")
    Ln.append("%-16s %-18s %-4s %-8s %-7s %-6s %-9s %s" % ("model", "task", "own", "k/n", "L", "cap", "verified", "deficiency lower bound"))
    for r in res["primary"]:
        Ln.append("%-16s %-18s %-4s %3d/%-4d %-7s %-6s %-9s %s %s" % (
            r["model"], r["task"], r["own"], r["k"], r["n"], fmt(r["cp_lower"]), fmt(r["cap"]),
            "yes" if r["verified"] else "no", r["bound_direction"], fmt(r["deficiency_lower_bound"])))
    nv = sum(r["verified"] for r in res["primary"])
    nwc = sum(r["worst_case"]["verified"] == r["verified"] for r in res["primary"])
    Ln.append("statements verified: %d of %d; unchanged with missing outcomes counted as incorrect: %d of %d" % (
        nv, len(res["primary"]), nwc, len(res["primary"])))
    cps = [c for c in res["certified_pairs"] if c["certified_incomparable"]]
    Ln.append("pair-model combinations certified incomparable: %d of %d" % (len(cps), len(res["certified_pairs"])))
    Ln.append("")
    Ln.append("DIAGNOSTICS (one-sided CP at 0.05/48; FLAG = lower bound above the cap)")
    for r in res["diagnostics"]:
        Ln.append("  %-16s %-18s %-4s %3d/%-4d L=%s cap=%s %s" % (r["model"], r["task"], r["arm"], r["k"], r["n"],
                                                             fmt(r["cp_lower"]), fmt(r["cap"]), "FLAG" if r["flag"] else ""))
    Ln.append("flags: %d" % sum(r["flag"] for r in res["diagnostics"]))
    Ln.append("")
    Ln.append("SECONDARY: own minus other-source accuracy (block differences, Hoeffding, alpha = 0.05/24)")
    for r in res["secondary"]:
        Ln.append("  %-16s %-18s B=%3d %+.2f bound %+.2f %s" % (r["model"], r["task"], r["blocks"], r["estimate"],
                                                           r["bound"], "verified" if r["verified"] else ""))
    Ln.append("")
    Ln.append("DESCRIPTIVE: own-source accuracy per hidden state (no simultaneous coverage)")
    for r in res["per_state"]:
        Ln.append("  %-16s %-18s %-40s %d/%d" % (r["model"], r["task"], r["state"], r["k"], r["n"]))
    Ln.append("DESCRIPTIVE: choices without context")
    for r in res["none_choices"]:
        Ln.append("  %-16s %-18s %s" % (r["model"], r["task"], r["choices"]))
    Ln.append("invalid replies: " + "; ".join("%s %s %d" % (r["model"], "own" if r["own_source_arm"] else "other/none", r["count"])
                                              for r in res["invalid"]))
    return "\n".join(Ln)


def main():
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results" / "package2" / "confirm_labels"
    res = analyze(d)
    res["certificate"] = L.certify()
    text = report(res)
    (d / "analysis_labels.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (d / "analysis_labels.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
