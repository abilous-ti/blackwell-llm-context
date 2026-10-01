r"""Analyse the replication within its collection structure, reconciled against the frozen schedule.

Every scheduled request gets exactly one status:
  graded         a response was saved and graded;
  ungraded       a response was saved but not yet graded (the runner grades it on resumption);
  failed         every transport attempt failed: a missing observation;
  interrupted    issued, but the run stopped before its response was saved: missing, never re-requested;
  not collected  its window closed (end time or call budget) before it was issued: missing;
  pending        its window is still open.
A window is closed by a window_end or window_closed record. The analysis is FINAL only if every
planned window is closed, no request is pending or ungraded, every record matches the schedule and
the design, and, for live data, the freeze holds (freeze.verify). Otherwise it is PROVISIONAL, and so
is every decision in it.

For each model and contrast (d = Y_a - Y_b per block, primary grader):
  primary     complete blocks; the window-averaged estimate over the windows that hold complete
              blocks, with the weighted Hoeffding bound for their sizes (stats.contrast_summary);
              planned windows without a complete block are listed;
  worst case  every scheduled block of every planned window, each missing outcome imputed against the
              claim (FAIL for the favoured condition, PASS for the other), so a window that was never
              collected contributes all of its blocks at the least favourable value.
Also reported: the estimate in every window, a descriptive heterogeneity test, the secondary
stratified normal bound, the pooled Clopper-Pearson comparability value, the current-grader
sensitivity, request statuses by model, window, task and condition, and calls used against the budget.

Usage:  python harness/replication/analyze.py [--mock]
Writes results/replication/analysis{_mock}.json, .md, and replication_table{_mock}.tex /
replication_windows{_mock}.tex (TikZ) for the manuscript; every output states its status.
"""
import argparse
import hashlib
import io
import json
import math
import os
import sys
from collections import Counter, defaultdict

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import freeze as frz  # noqa: E402
import records  # noqa: E402
import stats  # noqa: E402

STATUSES = ("graded", "ungraded", "failed", "interrupted", "not collected", "pending")


def load_schedule(design, base):
    tag = "" if design.get("status") == "frozen" else ".DRAFT"
    man = json.load(open(os.path.join(base, "schedule%s_manifest.json" % tag), encoding="utf-8"))
    p = os.path.join(base, man["schedule_file"])
    if hashlib.sha256(open(p, "rb").read()).hexdigest() != man["schedule_sha256"]:
        raise SystemExit("schedule hash does not match its manifest")
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def reconcile(rows, st):
    """Status of every scheduled request, and the records that do not belong to the schedule."""
    closed = records.closed_windows(st)
    status = {}
    for r in rows:
        sid = r["schedule_id"]
        rc = st["receipts"].get(sid)
        if rc is not None:
            status[sid] = "failed" if rc["transport_failed"] else (
                "graded" if sid in st["grades"] else "ungraded")
        elif sid in st["issued"]:
            status[sid] = "interrupted"
        elif r["window"] in closed:
            status[sid] = "not collected"
        else:
            status[sid] = "pending"
    stray = sorted((set(st["receipts"]) | set(st["issued"]) | set(st["grades"])) - set(status))
    return status, closed, stray


def consistency(rows, st, design):
    """Receipts must repeat their schedule row, request the design's model and send the prompt the
    published harness builds for their task and condition."""
    import run_replication as rr
    by_id = {r["schedule_id"]: r for r in rows}
    ids = {m["label"]: m["id"] for m in design["models"]}
    bad = []
    for sid, rc in st["receipts"].items():
        r = by_id.get(sid)
        if r is None:
            continue
        if any(rc.get(k) != r[k] for k in ("window", "model", "task", "condition", "block")):
            bad.append("%s: fields differ from the schedule" % sid)
        if rc.get("requested_model") != ids.get(r["model"]):
            bad.append("%s: requested %s, design says %s" % (sid, rc.get("requested_model"), ids.get(r["model"])))
        text = rr.request_text(r["task"], r["condition"])[1]
        if rc.get("prompt_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
            bad.append("%s: prompt differs from the harness prompt" % sid)
    return bad


def outcomes(rows, st, status, grader):
    """(model, task, window, block) -> {condition: 1 or 0 if graded, None if missing}, for every
    scheduled block of every planned window."""
    out = defaultdict(dict)
    for r in rows:
        sid = r["schedule_id"]
        y = None
        if status[sid] == "graded":
            y = 1 if st["grades"][sid]["pass_%s" % grader] else 0
        out[(r["model"], r["task"], r["window"], r["block"])][r["condition"]] = y
    return out


def diffs(bl, model, c, worst_case=False):
    by_w = defaultdict(list)
    for (m, t, w, _b), ys in bl.items():
        if m != model or t != c["task"]:
            continue
        ya, yb = ys.get(c["a"]), ys.get(c["b"])
        if ya is None or yb is None:
            if not worst_case:
                continue
            if c["direction"] > 0:          # the imputation least favourable to the claim
                ya = 0 if ya is None else ya
                yb = 1 if yb is None else yb
            else:
                ya = 1 if ya is None else ya
                yb = 0 if yb is None else yb
        by_w[w].append(ya - yb)
    return dict(by_w)


def main(mock=False, design_path=None, records_dir=None, base=None, check_freeze=None, write=True):
    design_path = design_path or os.path.join(HERE, "design.json")
    design = json.load(open(design_path, encoding="utf-8"))
    base = base or os.path.join(ROOT, "results", "replication")
    check_freeze = (not mock) if check_freeze is None else check_freeze
    rows = load_schedule(design, base)
    st = records.read_dir(records_dir or os.path.join(base, "records_mock" if mock else "records"))
    status, closed, stray = reconcile(rows, st)
    planned = [w["id"] for w in design["windows"]]
    alpha = design["analysis"]["per_statement_alpha"]
    margin = design["analysis"]["harm_margin"]
    max_att = design.get("retry_policy", {}).get("max_attempts", 3)

    tally = Counter(status.values())
    problems = []
    if [w for w in planned if w not in closed]:
        problems.append("windows not closed: %s" % ", ".join(w for w in planned if w not in closed))
    if tally["ungraded"]:
        problems.append("%d saved responses not graded" % tally["ungraded"])
    if stray:
        problems.append("%d records not in the schedule" % len(stray))
    if st["truncated"]:
        problems.append("truncated last line in %s" % ", ".join(st["truncated"]))
    bad = consistency(rows, st, design)
    if bad:
        problems.append("%d receipts inconsistent with the schedule or the design (first: %s)" % (len(bad), bad[0]))
    if check_freeze:
        problems += ["freeze: " + p for p in frz.verify(design_path, base, ROOT)]
    state = "final" if not problems else "provisional"

    bl_pub, bl_cur = outcomes(rows, st, status, "published"), outcomes(rows, st, status, "current")
    results = []
    for m in [x["label"] for x in design["models"]]:
        for c in design["contrasts"]:
            mg = margin if c["direction"] < 0 else None
            s = stats.contrast_summary(diffs(bl_pub, m, c), alpha, c["direction"], mg, planned_windows=planned)
            if s["n_blocks"]:
                s["heterogeneity"] = stats.heterogeneity(diffs(bl_pub, m, c))
                s["current_grader"] = stats.contrast_summary(diffs(bl_cur, m, c), alpha, c["direction"], mg,
                                                             planned_windows=planned)
            s["worst_case"] = stats.contrast_summary(diffs(bl_pub, m, c, worst_case=True), alpha,
                                                     c["direction"], mg, planned_windows=planned)
            k = {x: [0, 0] for x in (c["a"], c["b"])}
            for r in rows:
                if (r["model"] == m and r["task"] == c["task"] and r["condition"] in k
                        and status[r["schedule_id"]] == "graded"):
                    k[r["condition"]][0] += bool(st["grades"][r["schedule_id"]]["pass_published"])
                    k[r["condition"]][1] += 1
            s["pooled_counts"] = {"a": k[c["a"]], "b": k[c["b"]]}
            s["pooled_cp_bound"] = stats.pooled_cp(k[c["a"]][0], k[c["a"]][1], k[c["b"]][0], k[c["b"]][1],
                                                   alpha, c["direction"])
            results.append(dict(model=m, contrast=c["id"], claim=c["claim"], status=state, **s))
    incomparable = {}
    for m in [x["label"] for x in design["models"]]:
        adv = [r for r in results if r["model"] == m and r["contrast"] in ("A1", "A2")]
        incomparable[m] = len(adv) == 2 and all(r.get("verified") for r in adv)

    by_cell = defaultdict(Counter)
    for r in rows:
        s = status[r["schedule_id"]]
        if s != "graded":
            by_cell["%s|%s|%s|%s" % (r["model"], r["window"], r["task"], r["condition"])][s] += 1
    graded = [sid for sid, s in status.items() if s == "graded"]
    agree = sum(1 for sid in graded if st["grades"][sid]["pass_published"] == st["grades"][sid]["pass_current"])
    windows = {w: ("closed" if w in closed else "open" if any(
        x["window"] == w for x in list(st["issued"].values()) + st["events"]) else "not started")
        for w in planned}
    doc = {"status": state, "problems": problems, "n_scheduled": len(rows),
           "request_status": {s: tally[s] for s in STATUSES}, "windows": windows,
           "calls_used": records.calls_used(st, max_att),
           "call_budget": design.get("budget", {}).get("max_api_calls"),
           "missing_by_cell": {k: dict(v) for k, v in sorted(by_cell.items())},
           "grader_agreement": [agree, len(graded)], "per_statement_alpha": alpha,
           "pass_incomparable": incomparable, "results": results}
    if not write:
        return doc
    tag = "_mock" if mock else ""
    json.dump(doc, open(os.path.join(base, "analysis%s.json" % tag), "w", encoding="utf-8"), indent=1)

    md = ["# Replication analysis%s: %s" % (" (MOCK DATA)" if mock else "", state.upper()), ""]
    if problems:
        md += ["Not final because:", ""] + ["- %s" % p for p in problems] + [""]
    md += ["%d scheduled requests: %s. Windows: %s. Calls used: %d of %s. Graders agree on %d of %d "
           "graded draws." % (len(rows), ", ".join("%d %s" % (tally[s], s) for s in STATUSES),
                              ", ".join("%s %s" % (w, v) for w, v in windows.items()), doc["calls_used"],
                              doc["call_budget"], agree, len(graded)), "",
           "| Model | Contrast | Blocks | Estimate | Primary bound | Verified | Worst case | Windows missing "
           "| Window range | Heterogeneity p |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        wc = r["worst_case"]
        if not r["n_blocks"]:
            md.append("| %s | %s | 0 | – | – | – | %s | %s | – | – |" % (
                r["model"], r["contrast"], _decision(wc), ", ".join(r.get("windows_missing", planned))))
            continue
        ws = [v["estimate"] for v in r["by_window"].values()]
        md.append("| %s | %s | %d | %+.3f | %+.3f | %s | %s (%+.3f) | %s | %+.2f to %+.2f | %.3f |" % (
            r["model"], r["contrast"], r["n_blocks"], r["estimate"], r["primary_bound"], _decision(r),
            _decision(wc), wc["primary_bound"], ", ".join(r["windows_missing"]) or "none", min(ws), max(ws),
            r["heterogeneity"]["p_value"]))
    md += ["", "PASS incomparability (A1 and A2 both verified): %s" % ", ".join(
        "%s %s" % (m, "yes" if v else "no") for m, v in incomparable.items())]
    open(os.path.join(base, "analysis%s.md" % tag), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    write_tex([r for r in results if r["n_blocks"]], state, problems,
              os.path.join(base, "replication_table%s.tex" % tag),
              os.path.join(base, "replication_windows%s.tex" % tag))
    print("\n".join(md))
    return doc


def _decision(r):
    if not r.get("n_blocks"):
        return "–"
    if "verified" in r:
        return "yes" if r["verified"] else "no"
    return "any %s, margin %s" % ("yes" if r["verified_any_harm"] else "no",
                                  "yes" if r["verified_margin"] else "no")


def write_tex(results, state, problems, table_path, plot_path):
    """Table rows, and a forest plot: one row per model and contrast; grey dots are the window
    estimates, the black diamond the window-averaged estimate, the bar its primary bound, dashed
    lines mark 0 and the -0.30 harm margin. Rounding is outward (lower bounds down, upper up).
    A provisional analysis is marked in both files."""
    head = "%% status: %s%s\n" % (state, "" if not problems else " (" + "; ".join(problems) + ")")
    rows = []
    for r in results:
        adv = "verified" in r
        b = math.floor(r["primary_bound"] * 100) / 100 if adv else math.ceil(r["primary_bound"] * 100) / 100
        dec = ("\\checkmark" if r["verified"] else "$\\times$") if adv else "%s / %s" % (
            "\\checkmark" if r["verified_any_harm"] else "$\\times$",
            "\\checkmark" if r["verified_margin"] else "$\\times$")
        rows.append("%s & %s & %d & $%+.2f$ & $%+.2f$ & %s \\\\" % (
            r["model"], r["contrast"], r["n_blocks"], r["estimate"], b, dec))
    open(table_path, "w", encoding="utf-8", newline="\n").write(head + "\n".join(rows) + "\n")
    X = lambda v: 4.0 * (v + 1.0)            # effect in [-1, 1] -> x in [0, 8] cm
    L = [head.rstrip("\n"), "\\begin{tikzpicture}[x=1cm,y=0.42cm,font=\\footnotesize]"]
    top = len(results)
    if state != "final":
        L.append("\\node[anchor=south east,font=\\bfseries] at (8,%.2f) {PROVISIONAL};" % (top + 0.6))
    for v in (-1.0, -0.5, 0.0, 0.5, 1.0):
        L.append("\\draw[black!15] (%.2f,0.4) -- (%.2f,%.2f);" % (X(v), X(v), top + 0.6))
        L.append("\\node[below] at (%.2f,0.4) {$%+.1f$};" % (X(v), v))
    L.append("\\draw[dashed] (%.2f,0.4) -- (%.2f,%.2f);" % (X(0), X(0), top + 0.6))
    L.append("\\draw[dashed,black!60] (%.2f,0.4) -- (%.2f,%.2f);" % (X(-0.3), X(-0.3), top + 0.6))
    for i, r in enumerate(results):
        y = top - i
        L.append("\\node[left] at (0,%d) {%s %s};" % (y, r["model"], r["contrast"]))
        for w in r["by_window"].values():
            e = w.get("estimate")
            if e is not None and e == e:
                L.append("\\fill[black!40] (%.3f,%d) circle (1.3pt);" % (X(e), y))
        L.append("\\draw[line width=1.4pt] (%.3f,%d) -- (%.3f,%d);" % (X(r["estimate"]), y,
                                                                      X(max(-1, min(1, r["primary_bound"]))), y))
        L.append("\\node[diamond,fill,inner sep=1.4pt] at (%.3f,%d) {};" % (X(r["estimate"]), y))
    L.append("\\end{tikzpicture}")
    open(plot_path, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    main(mock=ap.parse_args().mock)
