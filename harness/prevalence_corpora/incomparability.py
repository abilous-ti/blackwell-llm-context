# Corpus 3: `tokenbench/measure_incomparability.py` -- an earlier, private sibling of the paper's
# harness (same author) with DIFFERENT signatures and conventions (e.g. hat_delta(PASS, b, a) with
# a PASS table keyed by (task_id, source)). Five usage tasks; verifiers call the REAL functions.
ROOT = r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard"
MODULES = ["tokenbench/measure_incomparability.py"]
NL = chr(10)
HP = ROOT.replace(chr(92), "/")
PRE = "import sys; sys.path.insert(0, '" + HP + "')" + NL + "from tokenbench import measure_incomparability as M" + NL
PRE_SOL = PRE.split(NL)[0]

REPLY = ("Here is my answer." + NL + "```python" + NL + "x = 1" + NL + "```" + NL + "and the real one:" + NL +
         "```python" + NL + "def f():" + NL + "    return 2" + NL + "```")
NINC = [(0.95, 0.05, 4, 0.1, 8), (0.8, 0.2, 4, 0.1, 8), (1.0, 0.0, 6, 0.1, 12)]
NDOM = [(0.95, 0.95, 4, 0.1, 0.15, 8), (1.0, 0.9, 6, 0.1, 0.15, 12)]
# PASS table over the module's own task list: source 'B' beats 'A' most on the third task.
PASS_SETUP = ("PASS={(t['id'],'A'):0.1 for t in M.TASKS}; PASS.update({(t['id'],'B'):0.2 for t in M.TASKS}); "
              "PASS[(M.TASKS[2]['id'],'B')]=0.9; PASS[(M.TASKS[0]['id'],'A')]=0.7")

TASKS = [
    {"id": "t_cpx", "key": "tokenbench.measure_incomparability.clopper_pearson",
     "prompt": "Module `tokenbench.measure_incomparability` (importable) has an exact two-sided "
               "Clopper-Pearson interval for a binomial proportion, solved by bisection on the binomial "
               "CDF. In solution.py write ci(k, n, alpha) that returns that module's (lo, hi) tuple by "
               "calling it. solution.py only.",
     "verify": PRE + "from solution import ci" + NL +
               "for k,n,a in [(8,10,0.05),(7,20,0.05),(0,40,0.0125)]:" + NL +
               "    g=ci(k,n,a); e=M.clopper_pearson(k,n,a)" + NL +
               "    assert abs(g[0]-e[0])<1e-9 and abs(g[1]-e[1])<1e-9, (k,n,a,g,e)" + NL},
    {"id": "t_hd", "key": "tokenbench.measure_incomparability.hat_delta",
     "prompt": "Module `tokenbench.measure_incomparability` (importable) has a function computing the "
               "empirical deficiency: how much a source b beats a source a at its best task, given a PASS "
               "table keyed by (task_id, source) -> pass rate over the module's own task list; it returns "
               "(value, best_task_id, per_task_gaps). In solution.py write best_task(PASS, a, b) that "
               "returns the task id at which b most beats a, using the module's function. solution.py only.",
     "verify": PRE + "from solution import best_task" + NL + PASS_SETUP + NL +
               "assert best_task(PASS,'A','B')==M.hat_delta(PASS,'B','A')[1]" + NL +
               "assert best_task(PASS,'B','A')==M.hat_delta(PASS,'A','B')[1]" + NL},
    {"id": "t_ninc", "key": "tokenbench.measure_incomparability.required_n_incomparability",
     "prompt": "Module `tokenbench.measure_incomparability` (importable) has a power calculation: the "
               "smallest per-cell n such that a clean crossover between a winning pass rate and a losing "
               "pass rate certifies a positive gap at the Bonferroni per-proportion level eta / m_cert, "
               "over a family of D tasks. In solution.py write n_cross(p_win, p_lose, D, eta, m_cert) "
               "that returns that number by calling the module's function. solution.py only.",
     "verify": PRE + "from solution import n_cross" + NL +
               "for args in " + repr(NINC) + ":" + NL +
               "    assert n_cross(*args)==M.required_n_incomparability(*args), args" + NL},
    {"id": "t_ndom", "key": "tokenbench.measure_incomparability.required_n_dominance",
     "prompt": "Module `tokenbench.measure_incomparability` (importable) has a second power calculation "
               "for the dominance leg: the smallest per-cell n such that the largest upper bound on the "
               "sub-source's advantage over the dominant source is at most a tolerance tol, at the "
               "per-proportion level eta / m_cert over D tasks. In solution.py write "
               "n_dom(p_dom, p_sub, D, eta, tol, m_cert) that returns it by calling the module's "
               "function. solution.py only.",
     "verify": PRE + "from solution import n_dom" + NL +
               "for args in " + repr(NDOM) + ":" + NL +
               "    assert n_dom(*args)==M.required_n_dominance(*args), args" + NL},
    {"id": "t_code", "key": "tokenbench.measure_incomparability.extract_code",
     "prompt": "Module `tokenbench.measure_incomparability` (importable) has a helper that pulls the "
               "solution code out of a model reply: it prefers the largest fenced code block and falls "
               "back to the raw text. In solution.py write get_code(reply) that returns that module's "
               "extraction by calling it. solution.py only.",
     "verify": PRE + "from solution import get_code" + NL + "REPLY=" + repr(REPLY) + NL +
               "for r in [REPLY, 'just words']:" + NL +
               "    assert get_code(r)==M.extract_code(r), r[:20]" + NL},
]

REF = {
    "t_cpx":  "from tokenbench import measure_incomparability as M" + NL + "def ci(k,n,a): return M.clopper_pearson(k,n,a)",
    "t_hd":   "from tokenbench import measure_incomparability as M" + NL + "def best_task(P,a,b): return M.hat_delta(P,b,a)[1]",
    "t_ninc": "from tokenbench import measure_incomparability as M" + NL + "def n_cross(*a): return M.required_n_incomparability(*a)",
    "t_ndom": "from tokenbench import measure_incomparability as M" + NL + "def n_dom(*a): return M.required_n_dominance(*a)",
    "t_code": "from tokenbench import measure_incomparability as M" + NL + "def get_code(r): return M.extract_code(r)",
}
WRONG = ("def ci(k,n,a): return (0.0,1.0)" + NL + "def best_task(P,a,b): return 'x'" + NL +
         "def n_cross(*a): return 40" + NL + "def n_dom(*a): return 40" + NL + "def get_code(r): return ''")
