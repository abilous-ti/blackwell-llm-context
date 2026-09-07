"""
SEQUENTIAL prevalence probe: the C1 machinery (paper 3) applied to the prevalence measurement.

Same object as measure_prevalence.py (pairwise Blackwell verdicts among retrieval-selected
candidates over a task family), but cells are drawn in ROUNDS with the two-stage alpha/2 rule:

  stage 1  after each round, every candidate pair is re-tested with the anytime-valid beta-mixture
           CS at alpha/2 (alpha = eta / (2|D_clean|)); a pair verified INCOMPARABLE is done.
           A candidate cell stops when every pair it belongs to is done, or on FUTILITY: a cell
           still at 0 passes after `--futility` draws stops (it cannot supply L>0 in its direction;
           stopping it never creates a false verification, it can only cost power).
  stage 2  at n_max, remaining pairs are tested with fixed-n Clopper-Pearson at alpha/2.
  Per-interval error <= alpha/2 + alpha/2 = alpha, so the union bound of the paper is unchanged.

`none` cells are measured in full first (they decide leaky tasks, which decides |D_clean|).

Corpus interface: a module exposing  ROOT (sys.path root for verifiers), MODULES (list of
module paths relative to ROOT), TASKS (id/key/prompt/verify), REF (id -> correct solution).

  python harness/prevalence_seq.py --corpus harness --mock
  python harness/prevalence_seq.py --corpus tokenguard --selftest
  python harness/prevalence_seq.py --corpus tokenguard --nmax 16 --round 4 --workers 2 --out results/prev_seq_tokenguard.json
"""
import argparse, ast, importlib, json, math, random, sys, tempfile, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "sequential"))
import measure_blackwell as mb
from seq_replay import av_interval, cp_interval          # pure functions
from measure_prevalence import bm25_topk                 # mini-BM25

REPO = HERE.parent
ETA = 0.10
NL = chr(10)


# ----------------------------------------------------------------------------- corpus loading
def load_corpus(name):
    return importlib.import_module("prevalence_corpora." + name)


def natural_chunks(corpus):
    """Verbatim public function/class docstrings (>= 20 words) of the corpus modules, presented
    as `def name(sig):` + indented body, with NO quote delimiters (cmd.exe quote-toggling)."""
    out = []
    for rel in corpus.MODULES:
        p = Path(corpus.ROOT) / rel
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        modname = rel[:-3].replace("/", ".").replace(chr(92), ".")
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                if not doc or len(doc.split()) < 20:
                    continue
                sig = ast.unparse(node.args) if isinstance(node, ast.FunctionDef) else ""
                head = ("def %s(%s):" % (node.name, sig)) if sig else ("class %s:" % node.name)
                body = NL.join("    " + ln if ln.strip() else ln for ln in doc.split(NL))
                text = "# from module " + modname + NL + head + NL + body
                if chr(34) in text:
                    text = text.replace(chr(34), "'")   # never ship a double quote through cmd.exe
                out.append({"id": modname + "." + node.name, "name": node.name, "text": text})
    return out


# ----------------------------------------------------------------------------- verdict helpers
def L_D(iv, A, B, tasks):
    return max(iv[(B, t)][0] - iv[(A, t)][1] for t in tasks)


def pair_status(iv, a, b, tasks):
    lab, lba = L_D(iv, a, b, tasks), L_D(iv, b, a, tasks)
    if lab > 0 and lba > 0:
        return "INCOMPARABLE", lab, lba
    return "open", lab, lba


# ----------------------------------------------------------------------------- driver
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--nmax", type=int, default=16)
    ap.add_argument("--round", type=int, default=4)
    ap.add_argument("--futility", type=int, default=8)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--out", default="")
    ap.add_argument("--only-cells", default="", help="arm|task,... re-run in ISOLATION to nmax (outage protocol)")
    a = ap.parse_args()
    corpus = load_corpus(a.corpus)
    TASKS = corpus.TASKS
    for t in TASKS:
        t.setdefault("fam", "prev")

    if a.selftest:
        ok = True
        for t in TASKS:
            for label, code, want in (("correct", corpus.REF[t["id"]], True), ("wrong", corpus.WRONG, False)):
                wd = Path(tempfile.mkdtemp(prefix="pseq_"))
                (wd / "solution.py").write_text(corpus.PRE_SOL + NL + code, encoding="utf-8")
                got = mb.verify_in(wd, t["verify"])
                ok &= (got == want)
                print(f"  {'OK ' if got == want else 'BAD'} {t['id']:<12} {label:<8} verify={got} (expected {want})")
        print("SELFTEST", "PASSED" if ok else "FAILED")
        sys.exit(0 if ok else 1)

    docs = natural_chunks(corpus)
    topk = {t["id"]: bm25_topk(t["prompt"], docs, k=a.topk) for t in TASKS}
    pool = sorted({d for ids in topk.values() for d in ids})
    by_task = [t["id"] for t in TASKS]
    print(f"corpus={a.corpus}: {len(docs)} natural chunks | tasks {len(TASKS)} | pool K={len(pool)} | "
          f"nmax={a.nmax} round={a.round} futility={a.futility}")
    for t in TASKS:
        print(f"  {t['id']:<12} top{a.topk}={topk[t['id']]}  decisive {'HIT' if t['key'] in topk[t['id']] else 'miss'}")
    mb.ARMS = {"none": None, **{d["id"]: d["text"] for d in docs if d["id"] in pool}}
    tmap = {t["id"]: t for t in TASKS}

    if a.mock:
        keys = {t["id"]: t["key"] for t in TASKS}
        rng = random.Random(0)
        def fake(task, arm, mock, i, model=None, singleshot=False):
            p = 0.95 if arm == keys[task["id"]] else 0.03
            return {"solved": rng.random() < p, "cost": 0.0, "out_tokens": 0}
        mb.run_one = fake

    draws = {(x, t): [] for x in ["none"] + pool for t in by_task}
    errs = {k: [] for k in draws}
    dropped, residual = {}, {}                          # outage draws redrawn / left unscored
    cost = 0.0
    calls = 0

    def draw_cells(cells, k):
        nonlocal cost, calls
        jobs = [(x, t, i) for (x, t) in cells for i in range(k)]
        def one(job):
            x, t, i = job
            return (x, t), mb.run_one(tmap[t], x, False, len(draws[(x, t)]) + i, a.model, singleshot=True)
        pending = jobs
        for attempt in range(4):                       # redraw transport errors, up to 3 extra passes
            failed = []
            with ThreadPoolExecutor(max_workers=1 if a.mock else a.workers) as ex:
                for job, (key, r) in zip(pending, ex.map(one, pending)):
                    cost += r.get("cost", 0.0); calls += 1
                    if r.get("error"):
                        failed.append(job); dropped[key] = dropped.get(key, 0) + 1
                        continue
                    draws[key].append(1 if r["solved"] else 0)
                    errs[key].append(0)
            if not failed:
                break
            if attempt < 3:
                print(f"    redrawing {len(failed)} outage draw(s), pass {attempt + 1}")
                time.sleep(20 * (attempt + 1))
            pending = failed
        for job in pending if failed else []:          # residual: recorded, NOT scored
            residual[job[0] + "|" + job[1]] = residual.get(job[0] + "|" + job[1], 0) + 1

    if a.only_cells:
        cells = [tuple(c.strip().split("|", 1)) for c in a.only_cells.split(",") if c.strip()]
        for x, t in cells:
            draw_cells([(x, t)], a.nmax)
        out = {"isolated": True, "corpus": a.corpus, "model": a.model, "nmax": a.nmax,
               "counts": {f"{x}|{t}": [sum(draws[(x, t)]), len(draws[(x, t)])] for x, t in cells},
               "draws": {f"{x}|{t}": draws[(x, t)] for x, t in cells},
               "errs": {f"{x}|{t}": errs[(x, t)] for x, t in cells}, "total_cost_usd": cost}
        (REPO / a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
        print("isolated re-run of", list(out["counts"]), "->", REPO / a.out, f"  spend ${cost:.2f}")
        return

    # 1) none arm in full -> leaky tasks -> D_clean and alpha
    draw_cells([("none", t) for t in by_task], a.nmax)
    none_p = {t: sum(draws[("none", t)]) / a.nmax for t in by_task}
    leaky = [t for t in by_task if none_p[t] >= 0.5]
    clean = [t for t in by_task if t not in leaky]
    alpha = ETA / (2 * len(clean)); a1 = a2 = alpha / 2
    print(f"[{time.strftime('%H:%M:%S')}] none-baseline:", {t: f"{v:.0%}" for t, v in none_p.items()}, "| leaky:", leaky, f"| alpha={alpha:.4f}")

    # 2) candidates in rounds with the two-stage rule
    pairs = [(pool[i], pool[j]) for i in range(len(pool)) for j in range(i + 1, len(pool))]
    done = {}                      # pair -> (status, lab, lba, n_at_stop)
    active = {(x, t) for x in pool for t in clean}
    stop_n = {}
    n_drawn = 0
    while n_drawn < a.nmax and active:
        k = min(a.round, a.nmax - n_drawn)
        draw_cells(sorted(active), k)
        n_drawn += k
        iv = {(x, t): av_interval(sum(draws[(x, t)]), len(draws[(x, t)]), a1) for x in pool for t in clean}
        for pr in pairs:
            if pr in done:
                continue
            st, lab, lba = pair_status(iv, pr[0], pr[1], clean)
            if st == "INCOMPARABLE":
                done[pr] = ("INCOMPARABLE", lab, lba, n_drawn)
        # cell stopping: all its pairs done, or futility (still 0 after >= futility draws)
        tot = {x: sum(sum(draws[(x, t)]) for t in clean) for x in pool}
        for cell in sorted(active):
            x, t = cell
            mine = [pr for pr in pairs if x in pr]
            open_partners = [pr[0] if pr[1] == x else pr[1] for pr in mine if pr not in done]
            hopeless = n_drawn >= a.futility and tot[x] == 0 and all(tot[p] == 0 for p in open_partners)
            if all(pr in done for pr in mine) or hopeless:
                active.discard(cell); stop_n[cell] = n_drawn
        print(f"  [{time.strftime('%H:%M:%S')}] round n={n_drawn:<3} verified pairs {sum(1 for v in done.values() if v[0]=='INCOMPARABLE'):>2}/{len(pairs)}"
              f"  active cells {len(active):>3}  calls so far {calls}")
    for cell in active:
        stop_n[cell] = n_drawn

    # 3) stage 2: fixed-n CP at alpha/2 on the cells' final counts for the open pairs
    ivf = {(x, t): cp_interval(sum(draws[(x, t)]), len(draws[(x, t)]), a2) for x in pool for t in clean}
    rows = []
    for pr in pairs:
        if pr in done:
            st, lab, lba, nstop = done[pr]
        else:
            st, lab, lba = pair_status(ivf, pr[0], pr[1], clean); nstop = a.nmax
            st = st if st == "INCOMPARABLE" else "unresolved"
        sa, sb = lab > 0, lba > 0
        pat = "incomparable" if (sa and sb) else ("one-way evidence" if (sa or sb) else "no evidence")
        co = any(pr[0] in ids and pr[1] in ids for ids in topk.values())
        rows.append({"pair": list(pr), "verdict": st, "pattern": pat, "L_AB": round(lab, 3),
                     "L_BA": round(lba, 3), "co_retrieved": co, "n_at_verdict": nstop})
    tally = Counter(r["verdict"] for r in rows); pat_all = Counter(r["pattern"] for r in rows)
    pat_co = Counter(r["pattern"] for r in rows if r["co_retrieved"])
    fixed_calls = (len(pool) + 1) * len(by_task) * a.nmax
    print(f"verdicts: {dict(tally)}  | patterns ALL {dict(pat_all)}  CO-RETRIEVED {dict(pat_co)}")
    print(f"calls: {calls} vs fixed-n {fixed_calls}  -> {fixed_calls/max(calls,1):.2f}x  ({100*(1-calls/fixed_calls):.0f}% fewer)   spend ${cost:.2f}")
    print(f"outage draws redrawn: {sum(dropped.values())}   left unscored: {sum(residual.values())}")
    out = {"corpus": a.corpus, "sequential": True, "mock": a.mock, "model": a.model, "eta": ETA,
           "nmax": a.nmax, "round": a.round, "futility": a.futility, "topk": topk, "pool": pool,
           "none_pass": none_p, "leaky_tasks": leaky, "clean_tasks": clean,
           "counts": {f"{x}|{t}": [sum(v), len(v)] for (x, t), v in draws.items()},
           "draws": {f"{x}|{t}": v for (x, t), v in draws.items()},
           "errs": {f"{x}|{t}": v for (x, t), v in errs.items()},
           "stop_n": {f"{x}|{t}": n for (x, t), n in stop_n.items()},
           "pairs": rows, "tally": dict(tally), "pattern_all": dict(pat_all), "pattern_co": dict(pat_co),
           "calls": calls, "fixed_calls": fixed_calls, "total_cost_usd": cost,
           "outage_redrawn": dropped, "outage_unscored": residual}
    if a.out:
        (REPO / a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
        print("wrote", REPO / a.out)


if __name__ == "__main__":
    main()
