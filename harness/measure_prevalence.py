"""
NATURALISTIC PREVALENCE PROBE (pilot 1).

Question: when a retriever hands a model its top-k candidate sources for a query, how often are
those candidates Blackwell-INCOMPARABLE (each decisive somewhere the other fails), as opposed to
nested (one dominates)?  The main paper answers this only for two hand-built pairs; this probe
measures it on a NATURAL corpus with retrieval-selected candidates.

Corpus  : unedited docstrings of a PRIVATE codebase (this harness). Real text, zero hand-writing,
          and the model cannot know these signatures (unlike stdlib, where none-baseline ~ 100%).
Tasks   : 6 usage tasks; each verifier calls the REAL function, so ground truth is never authored.
Retrieval: mini-BM25 (no deps) over chunks, top-3 per task -> candidate pool K.
Arms    : none + one arm per candidate chunk.  Cells = (K+1) x |D|.
Verdicts: per candidate PAIR, the paper's certify_incomparable / certify_dominance over D
          (same Clopper-Pearson + union-bound rule, eta=0.10). Leaky-baseline protocol applied.

  python harness/measure_prevalence.py --selftest      # verifiers: correct passes, wrong fails
  python harness/measure_prevalence.py --mock          # plumbing + analysis on planted outcomes
  python harness/measure_prevalence.py --runs 16 --workers 3 --out results/prevalence_haiku_n16.json
"""
import argparse, ast, json, math, random, re, sys, tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure_blackwell as mb          # reuse run_one / verify_in / certify_* unchanged

REPO = HERE.parent
ETA = 0.10
NL = chr(10)
HP = str(HERE).replace(chr(92), "/")     # forward-slash path for verifier snippets
PRE = "import sys; sys.path.insert(0, '" + HP + "')" + NL + "import measure_blackwell as mb" + NL
TQ = chr(34) * 3


# ----------------------------------------------------------------------------- corpus
def natural_chunks():
    """Every public function/class docstring (>= 20 words) in the private modules, verbatim."""
    out = []
    for fn in ("measure_blackwell.py", "probe_select.py"):
        src = (HERE / fn).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                if not doc or len(doc.split()) < 20:
                    continue
                sig = ast.unparse(node.args) if isinstance(node, ast.FunctionDef) else ""
                head = ("def %s(%s):" % (node.name, sig)) if sig else ("class %s:" % node.name)
                text = ("# from module " + fn[:-3] + NL + head + NL + "    " + TQ + doc + TQ)
                out.append({"id": fn[:-3] + "." + node.name, "name": node.name, "text": text})
    return out


# ----------------------------------------------------------------------------- mini-BM25
def _tok(s):
    return re.findall(r"[a-z_][a-z0-9_]+", s.lower())


def bm25_topk(query, docs, k=3, k1=1.5, b=0.75):
    toks = [_tok(d["text"]) for d in docs]
    N = len(docs); avg = sum(map(len, toks)) / N
    df = Counter(t for ts in toks for t in set(ts))
    q = _tok(query)
    scores = []
    for i, ts in enumerate(toks):
        tf = Counter(ts); L = len(ts); s = 0.0
        for t in q:
            if t not in tf:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * L / avg))
        scores.append((s, i))
    scores.sort(reverse=True)
    return [docs[i]["id"] for s, i in scores[:k] if s > 0]


# ----------------------------------------------------------------------------- tasks
# Each task's decisive fact lives in exactly ONE chunk ("key"); verifiers call the REAL function.
CW1 = {"a": (40, 40), "b": (0, 40), "c": (39, 40)}
CW2 = {"a": (0, 40), "b": (40, 40), "c": (2, 40)}
BT = ["a", "b", "c"]
TASKS = [
    {"id": "t_cp", "key": "measure_blackwell.clopper_pearson",
     "prompt": "Module `measure_blackwell` (importable) has a function that computes the exact "
               "two-sided Clopper-Pearson binomial confidence interval. In solution.py write "
               "ci95(k, n) that returns that module's 95% interval for k successes in n trials "
               "as a (lo, hi) tuple, by calling the module's function. solution.py only.",
     "verify": PRE + "from solution import ci95" + NL +
               "for k,n in [(7,20),(0,40),(40,40)]:" + NL +
               "    got=ci95(k,n); exp=mb.clopper_pearson(k,n,0.05)" + NL +
               "    assert abs(got[0]-exp[0])<1e-9 and abs(got[1]-exp[1])<1e-9, (k,n,got,exp)" + NL},
    {"id": "t_nstark", "key": "measure_blackwell.required_n_stark",
     "prompt": "Module `measure_blackwell` (importable) has a function giving the smallest per-cell "
               "sample size that certifies a STARK crossover (0/n vs n/n) at joint confidence 1-eta "
               "over a task family of size D. In solution.py write n_stark(eta, D) that returns "
               "that number by calling the module's function. solution.py only.",
     "verify": PRE + "from solution import n_stark" + NL +
               "for e,D in [(0.1,4),(0.05,6),(0.2,2)]:" + NL +
               "    assert n_stark(e,D)==mb.required_n_stark(eta=e,D=D), (e,D)" + NL},
    {"id": "t_suptask", "key": "measure_blackwell.hat_delta_D",
     "prompt": "Module `measure_blackwell` (importable) has a function computing the empirical "
               "deficiency of source W1 relative to W2 over a task family, given per-task counts "
               "dicts mapping task id -> (k, n). In solution.py write sup_task(cW1, cW2, tasks) "
               "that returns the TASK ID at which W2 most beats W1, using the module's function. "
               "solution.py only.",
     "verify": PRE + "from solution import sup_task" + NL +
               "cW1=" + repr(CW1) + "; cW2=" + repr(CW2) + "; bt=" + repr(BT) + NL +
               "assert sup_task(cW1,cW2,bt)==mb.hat_delta_D(cW1,cW2,bt)[1]" + NL +
               "assert sup_task(cW2,cW1,bt)==mb.hat_delta_D(cW2,cW1,bt)[1]" + NL},
    {"id": "t_lab", "key": "measure_blackwell.certify_incomparable",
     "prompt": "Module `measure_blackwell` (importable) has a function that certifies empirical "
               "Blackwell-incomparability of two sources A, B from per-task count dicts "
               "(task id -> (k, n)) at joint confidence 1-eta. In solution.py write lab(cA, cB, "
               "tasks) that returns the certified LOWER bound on the A->B deficiency at eta=0.1, "
               "using the module's function. solution.py only.",
     "verify": PRE + "from solution import lab" + NL +
               "cA=" + repr(CW1) + "; cB=" + repr(CW2) + "; bt=" + repr(BT) + NL +
               "assert abs(lab(cA,cB,bt)-mb.certify_incomparable(cA,cB,bt,eta=0.1)['L_AB'])<1e-9" + NL},
    {"id": "t_ud", "key": "measure_blackwell.certify_dominance",
     "prompt": "Module `measure_blackwell` (importable) has a function that certifies that a "
               "dominant source has zero deficiency relative to a sub-source over a task family, "
               "from per-task count dicts (task id -> (k, n)), at confidence 1-eta. In solution.py "
               "write u_d(cdom, csub, tasks) that returns the certified UPPER bound it computes "
               "at eta=0.1, using the module's function. solution.py only.",
     "verify": PRE + "from solution import u_d" + NL +
               "cd=" + repr(CW1) + "; cs=" + repr(CW2) + "; bt=" + repr(BT) + NL +
               "assert abs(u_d(cd,cs,bt)-mb.certify_dominance(cd,cs,bt,eta=0.1)['U_D'])<1e-9" + NL},
    {"id": "t_lex", "key": "measure_blackwell.lexical_relevance",
     "prompt": "Module `measure_blackwell` (importable) has a model-free, query-conditioned "
               "relevance score: bag-of-words cosine between a context text and a task prompt. "
               "In solution.py write rel(ctx, prompt) that returns that score by calling the "
               "module's function. solution.py only.",
     "verify": PRE + "from solution import rel" + NL +
               "for c,p in [('ledger post memo keyword','post to ledger with memo'),('a b c','x y z')]:" + NL +
               "    assert abs(rel(c,p)-mb.lexical_relevance(c,p))<1e-9, (c,p)" + NL},
]
for t in TASKS:
    t["fam"] = "prev"

# Correct reference solutions (used ONLY by --selftest to prove the verifiers are sound).
REF = {
    "t_cp":      "import measure_blackwell as mb" + NL + "def ci95(k,n): return mb.clopper_pearson(k,n,0.05)",
    "t_nstark":  "import measure_blackwell as mb" + NL + "def n_stark(eta,D): return mb.required_n_stark(eta=eta,D=D)",
    "t_suptask": "import measure_blackwell as mb" + NL + "def sup_task(a,b,t): return mb.hat_delta_D(a,b,t)[1]",
    "t_lab":     "import measure_blackwell as mb" + NL + "def lab(a,b,t): return mb.certify_incomparable(a,b,t,eta=0.1)['L_AB']",
    "t_ud":      "import measure_blackwell as mb" + NL + "def u_d(a,b,t): return mb.certify_dominance(a,b,t,eta=0.1)['U_D']",
    "t_lex":     "import measure_blackwell as mb" + NL + "def rel(c,p): return mb.lexical_relevance(c,p)",
}
WRONG = ("def ci95(k,n): return (0.0,1.0)" + NL + "def n_stark(eta,D): return 40" + NL +
         "def sup_task(a,b,t): return t[0]" + NL + "def lab(a,b,t): return 0.0" + NL +
         "def u_d(a,b,t): return 0.0" + NL + "def rel(c,p): return 0.5")


def selftest():
    ok = True
    for t in TASKS:
        for label, code, want in (("correct", REF[t["id"]], True), ("wrong", WRONG, False)):
            wd = Path(tempfile.mkdtemp(prefix="prev_"))
            (wd / "solution.py").write_text(PRE.split(NL)[0] + NL + code, encoding="utf-8")
            got = mb.verify_in(wd, t["verify"])
            flag = "OK " if got == want else "BAD"
            ok &= (got == want)
            print(f"  {flag} {t['id']:<10} {label:<8} verify={got} (expected {want})")
    print("SELFTEST", "PASSED" if ok else "FAILED")
    return ok


# ----------------------------------------------------------------------------- analysis
def analyse(counts, by_task, pool, topk, eta=ETA):
    none_p = {t: mb.pass_rate(counts["none"][t]) for t in by_task}
    leaky = [t for t in by_task if none_p[t] >= 0.5]
    clean = [t for t in by_task if t not in leaky]
    co = set()
    for t, ids in topk.items():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                co.add(tuple(sorted((ids[i], ids[j]))))
    rows = []
    for i in range(len(pool)):
        for j in range(i + 1, len(pool)):
            a, b = pool[i], pool[j]
            ci = mb.certify_incomparable(counts[a], counts[b], clean, eta=eta)
            da = mb.certify_dominance(counts[a], counts[b], clean, eta=eta)["U_D"] <= 0
            db = mb.certify_dominance(counts[b], counts[a], clean, eta=eta)["U_D"] <= 0
            verdict = ("INCOMPARABLE" if ci["certified_incomparable"] else
                       "A>=B" if da and not db else "B>=A" if db and not da else
                       "equivalent" if (da and db) else "unresolved")
            rows.append({"pair": [a, b], "verdict": verdict, "L_AB": round(ci["L_AB"], 3),
                         "L_BA": round(ci["L_BA"], 3), "co_retrieved": tuple(sorted((a, b))) in co})
    tally = Counter(r["verdict"] for r in rows)
    tally_co = Counter(r["verdict"] for r in rows if r["co_retrieved"])
    return {"none_pass": none_p, "leaky_tasks": leaky, "clean_tasks": clean,
            "pairs": rows, "tally_all": dict(tally), "tally_co_retrieved": dict(tally_co),
            "n_pairs": len(rows), "n_co_retrieved": sum(r["co_retrieved"] for r in rows)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--runs", type=int, default=16)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--out", default="results/prevalence_pilot.json")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)

    docs = natural_chunks()
    topk = {t["id"]: bm25_topk(t["prompt"], docs, k=a.topk) for t in TASKS}
    pool = sorted({d for ids in topk.values() for d in ids})
    print(f"corpus: {len(docs)} natural chunks | tasks: {len(TASKS)} | candidate pool K={len(pool)}")
    for t in TASKS:
        hit = "HIT" if t["key"] in topk[t["id"]] else "miss"
        print(f"  {t['id']:<10} top{a.topk}={topk[t['id']]}  decisive-chunk {hit}")

    arms = ["none"] + pool
    mb.ARMS = {"none": None, **{d["id"]: d["text"] for d in docs if d["id"] in pool}}
    if a.mock:
        keys = {t["id"]: t["key"] for t in TASKS}
        def fake(task, arm, mock, i, model=None, singleshot=False):
            p = 0.95 if arm == keys[task["id"]] else 0.03
            return {"solved": random.random() < p, "cost": 0.0, "out_tokens": 0}
        mb.run_one = fake
    counts, cost, toks, draws = mb.measure(arms, False, a.runs, tasks=TASKS,
                                           workers=1 if a.mock else a.workers,
                                           model=a.model, singleshot=True)
    by_task = [t["id"] for t in TASKS]
    res = analyse(counts, by_task, pool, topk)
    out = {"mock": a.mock, "model": a.model, "n_per_cell": a.runs, "eta": ETA,
           "corpus_size": len(docs), "topk": topk, "pool": pool,
           "counts": {f"{x}|{t}": counts[x][t] for x in arms for t in by_task},
           "draws": {f"{x}|{t}": draws[x][t] for x in arms for t in by_task},
           "analysis": res,
           "total_cost_usd": sum(cost[x][t] for x in arms for t in by_task) * a.runs}
    (REPO / a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(NL + "none-baseline PASS:", {t: f"{v:.0%}" for t, v in res["none_pass"].items()},
          "| leaky (excluded):", res["leaky_tasks"])
    print(f"pairs: {res['n_pairs']} total, {res['n_co_retrieved']} co-retrieved")
    print("verdicts ALL          :", res["tally_all"])
    print("verdicts CO-RETRIEVED :", res["tally_co_retrieved"])
    print(f"spend ${out['total_cost_usd']:.2f}  -> wrote {REPO / a.out}")


if __name__ == "__main__":
    main()
