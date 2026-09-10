"""Recompute every published per-model number from the raw run files, using the harness's
own certify_harm / clopper_pearson rather than a reimplementation.

Run it first in --mode cli to check it reproduces the numbers currently in the manuscript.
Only once that check passes is it trustworthy for --mode api, which is the transport swap.

Usage:  python recompute.py cli|api
"""
import sys, io, json, os
# Only rebind stdout when run as a script. Doing it at import time wraps the same buffer
# twice in any importer that also wraps it, and the first wrapper closes the buffer when
# it is collected -- a bug this cost three separate debugging rounds.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "harness"))
from measure_blackwell import clopper_pearson, certify_harm  # noqa: E402

RES = os.path.join(ROOT, "results")
TASKS = ["api_post_ok", "api_argorder", "enc_amount", "trap_store_wire"]
ARMS = ["none", "W1", "W2", "W1plus"]
ETA, TAU = 0.10, 0.30

# base file per model, plus arm-only re-measurements that override single cells.
# The overrides are how the published Opus/Haiku rows are actually built; ignoring them
# would silently compare against numbers the paper does not print.
CLI = {
    "Haiku-4.5":       ("blackwell_haiku_ss_n40",  {("W1", "enc_amount"): "blackwell_haiku_ss_W1_enc_v2"}),
    "Sonnet-4.6":      ("blackwell_sonnet_ss_n40", {}),
    # the Opus W1plus re-run covers ALL FOUR cells, not just the two API ones
    "Opus-4.8":        ("blackwell_opus_ss_n40",   dict([(("W1plus", t), "blackwell_opus_ss_W1plus_v2")
                                                         for t in TASKS] +
                                                        [(("W2", "trap_store_wire"), "blackwell_opus_ss_W2_trap_v2")])),
    # The base GPT run logged an HTTP 500 on W2/trap_store_wire, so both arms of that cell
    # are read from the retained re-measurement, which has zero transport errors. Same counts.
    "GPT-5.5":         ("blackwell_gpt55_n40",
                        {("W1", "trap_store_wire"): "audit/audit_gpt55_trap_store_wire_summary",
                         ("W2", "trap_store_wire"): "audit/audit_gpt55_trap_store_wire_summary"}),
    "DeepSeek-V4-Pro": ("blackwell_deepseek_n40",  {}),
    "Kimi-K2.6":       ("blackwell_kimi_n40",      {}),
}
API = dict(CLI)
for m, f in (("Haiku-4.5", "blackwell_haiku_api_n40"),
             ("Sonnet-4.6", "blackwell_sonnet_api_n40"),
             ("Opus-4.8", "blackwell_opus_api_n40")):
    API[m] = (f, {})


def load(stem):
    p = os.path.join(RES, stem + ".json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def counts_for(model, spec):
    """Return {arm: {task: (k,n)}} or None if the base run is missing."""
    base, over = spec
    d = load(base)
    if d is None:
        return None, base
    c = {a: {} for a in ARMS}
    for a in ARMS:
        for t in TASKS:
            kn = d["counts"].get("%s|%s" % (a, t))
            if kn:
                c[a][t] = tuple(kn)
    for (a, t), stem in over.items():
        od = load(stem)
        if od is None:
            # Silently keeping the base counts here would substitute a different record
            # for the one the declaration names, with no warning anywhere.
            raise SystemExit(
                "declared override missing: %s for %s|%s (model %s). Refusing to "
                "recompute from the base file." % (stem, a, t, model))
        kn = od["counts"].get("%s|%s" % (a, t)) if "counts" in od else None
        if kn is None and "arms" in od:
            # retained-audit summary: {arms: {W1: {n, pass_original, ...}, ...}}
            arm = (od["arms"] or {}).get(a)
            if arm and "pass_original" in arm and "n" in arm:
                kn = [arm["pass_original"], arm["n"]]
        if kn is None:
            # An arm-only re-measurement stores a single cell, but matching on the task suffix
            # alone ignored the arm: a file holding only W1|trap_store_wire satisfied a request
            # for W2|trap_store_wire and returned W1's counts as W2's. The arm must match too, so
            # the only thing this branch now tolerates is a file that stores exactly one cell and
            # stores it for the arm we asked about.
            for k2, v2 in (od.get("counts") or {}).items():
                if k2 == "%s|%s" % (a, t):
                    kn = v2
        # An override that exists but does not carry the declared cell is the same failure as a
        # missing file: the base value stays and nothing says so. Require the entry, and require
        # it to be a usable pair.
        if kn is None:
            raise SystemExit(
                "declared override %s has no entry for %s|%s (model %s). Refusing to fall back "
                "to the base file." % (stem, a, t, model))
        if not (isinstance(kn, (list, tuple)) and len(kn) == 2):
            raise SystemExit("override %s: %s|%s is not a [k, n] pair: %r" % (stem, a, t, kn))
        k_, n_ = kn
        if not (isinstance(k_, int) and isinstance(n_, int) and n_ > 0 and 0 <= k_ <= n_):
            raise SystemExit("override %s: %s|%s has invalid counts %r" % (stem, a, t, kn))
        c[a][t] = (k_, n_)
    return c, None


def pct(kn):
    k, n = kn
    return 100.0 * k / n if n else float("nan")


def main(mode):
    table = CLI if mode == "cli" else API
    print("MODE: %s\n" % mode)
    missing = []
    rows = {}
    for m, spec in table.items():
        c, miss = counts_for(m, spec)
        if c is None:
            missing.append((m, miss))
            continue
        rows[m] = c

    if missing:
        print("MISSING run files (model, stem):")
        for m, s in missing:
            print("   %-18s %s" % (m, s))
        print()

    # ---- per-cell PASS ------------------------------------------------------
    print("PER-CELL PASS %  (arm x task)")
    print("%-17s %-8s %s" % ("model", "arm", "  ".join("%-16s" % t for t in TASKS)))
    for m in table:
        if m not in rows:
            continue
        for a in ARMS:
            cells = "  ".join("%-16s" % ("%d/%d=%.0f%%" % (rows[m][a][t][0], rows[m][a][t][1], pct(rows[m][a][t]))
                                         if t in rows[m][a] else "-") for t in TASKS)
            print("%-17s %-8s %s" % (m if a == ARMS[0] else "", a, cells))
    print()

    # ---- harm table (tab:interference / fig:forest) -------------------------
    print("HARM CONTRAST  Delta_T = PASS(W1plus)-PASS(W1);  tau=%.2f" % TAU)
    print("%-17s %-16s %10s %9s %10s %10s %s" %
          ("model", "cell", "W1->W1plus", "Delta", "upper@eta", "upper@eta/12", "verified"))
    n_marg = n_joint = 0
    per_model_any_joint = {}
    for m in table:
        if m not in rows:
            continue
        by = [t for t in ("api_post_ok", "api_argorder") if t in rows[m]["W1"] and t in rows[m]["W1plus"]]
        marg = certify_harm(rows[m], by, eta=ETA, tau=TAU)
        for t in by:
            k1, n1 = rows[m]["W1"][t]
            kp, np_ = rows[m]["W1plus"][t]
            # joint budget: one eta spread over all 12 contrasts -> per-interval eta/12
            hi_j = clopper_pearson(kp, np_, ETA / 12.0)[1]
            lo_j = clopper_pearson(k1, n1, ETA / 12.0)[0]
            dj = hi_j - lo_j
            dm = marg[t]["delta_hi"]
            okm, okj = dm <= -TAU, dj <= -TAU
            n_marg += okm
            n_joint += okj
            per_model_any_joint[m] = per_model_any_joint.get(m, False) or okj
            print("%-17s %-16s %10s %9.3f %10.4f %10.4f  %s" %
                  (m, t, "%.0f%%->%.0f%%" % (pct((k1, n1)), pct((kp, np_))),
                   marg[t]["delta"], dm, dj, "yes" if okm else "NO"))
    print()
    print("marginal verifications clearing -tau : %d" % n_marg)
    print("joint (eta/12) verifications clearing: %d" % n_joint)
    print("every model keeps >=1 under joint    : %s" %
          all(per_model_any_joint.get(m, False) for m in rows))
    print()

    # ---- guessability (none arm) -------------------------------------------
    # the manuscript's value spectrum is the none arm on api_argorder specifically,
    # not the four-cell pool -- pooling understates it and would silently restate the claim.
    print("GUESSABILITY (none arm; the published spectrum is the api_argorder column)")
    print("   %-18s %10s %10s %10s %10s   %s" % ("model", *TASKS, "PUBLISHED"))
    for m in table:
        if m not in rows:
            continue
        cells = tuple("%d/%d" % rows[m]["none"][t] if t in rows[m]["none"] else "-" for t in TASKS)
        ag = rows[m]["none"].get("api_argorder")
        print("   %-18s %10s %10s %10s %10s   %s" % (m, cells[0], cells[1], cells[2], cells[3],
              ("%.0f%%" % (100.0*ag[0]/ag[1])) if ag else "-"))
    print()

    # ---- policies (tab:policies) -------------------------------------------
    print("POLICIES, mean PASS %% over the four cells")
    print("%-18s %9s %9s %9s %9s" % ("model", "fixed", "topical", "concat", "oracle"))
    TOPICAL = {"api_post_ok": "W1", "api_argorder": "W1", "enc_amount": "W2", "trap_store_wire": "W2"}
    for m in table:
        if m not in rows:
            continue
        c = rows[m]
        if not all(t in c[a] for a in ("W1", "W2", "W1plus") for t in TASKS):
            print("%-18s  (incomplete)" % m)
            continue
        fixed = sum(pct(c["W1"][t]) for t in TASKS) / 4
        top = sum(pct(c[TOPICAL[t]][t]) for t in TASKS) / 4
        con = sum(pct(c["W1plus"][t]) for t in TASKS) / 4
        orc = sum(max(pct(c["W1"][t]), pct(c["W2"][t])) for t in TASKS) / 4
        print("%-18s %9.1f %9.1f %9.1f %9.1f" % (m, fixed, top, con, orc))
    print()

    # ---- Haiku front numbers (fig:hasse), joint over 3x4 at eta/12 ----------
    if "Haiku-4.5" in rows:
        c = rows["Haiku-4.5"]
        a = ETA / 12.0

        def LD(X, Y):   # lower bound on sup_T [PASS(Y,T) - PASS(X,T)]
            best = -9
            for t in TASKS:
                if t not in c[X] or t not in c[Y]:
                    continue
                lo = clopper_pearson(c[Y][t][0], c[Y][t][1], a)[0]
                hi = clopper_pearson(c[X][t][0], c[X][t][1], a)[1]
                best = max(best, lo - hi)
            return best

        def UD(X, Y):   # upper bound on that sup
            best = -9
            for t in TASKS:
                if t not in c[X] or t not in c[Y]:
                    continue
                hi = clopper_pearson(c[Y][t][0], c[Y][t][1], a)[1]
                lo = clopper_pearson(c[X][t][0], c[X][t][1], a)[0]
                best = max(best, hi - lo)
            return max(0.0, best)

        print("HAIKU FRONT (fig:hasse), all 3x4 intervals at per-interval level eta/12")
        print("   L_D(W1,W2)     = %+.4f" % LD("W1", "W2"))
        print("   L_D(W2,W1)     = %+.4f" % LD("W2", "W1"))
        print("   L_D(W1plus,W1) = %+.4f   (non-dominance witness)" % LD("W1plus", "W1"))
        print("   L_D(W1,W1plus) = %+.4f" % LD("W1", "W1plus"))
        print("   U_D(W1plus,W2) = %.4f    (epsilon-dominance margin)" % UD("W1plus", "W2"))


if __name__ == "__main__":
    # Default to the record the paper publishes. The historical command-line grid is
    # still reachable with an explicit "cli" argument.
    main(sys.argv[1] if len(sys.argv) > 1 else "api")
