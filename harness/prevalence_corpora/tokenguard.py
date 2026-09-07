# Corpus 2: the private `tokenguard` package (stdlib-only, importable). Natural docstrings of
# canonmatch / router / idiosyncrasy / compress / plancache; six usage tasks whose verifiers call
# the REAL functions, so ground truth is never authored.
ROOT = r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard"
MODULES = ["tokenguard/canonmatch.py", "tokenguard/router.py", "tokenguard/idiosyncrasy.py",
           "tokenguard/compress.py", "tokenguard/plancache.py"]
NL = chr(10)
HP = ROOT.replace(chr(92), "/")
PRE = "import sys; sys.path.insert(0, '" + HP + "')" + NL
PRE_SOL = PRE.strip()

PAIRS = [("add a retry to the http client", "add retries to the http client"),
         ("delete the cache dir", "add a retry to the http client"),
         ("fix the login bug", "fix the login bug"),
         ("write tests for parser", "write tests for the tokenizer"),
         ("x", "y")]
IDIO_IN = ["call fooBarBaz(42, 1337) with the kx7- prefix and the MAGIC_7 constant",
           "rewrite computeTotalCents to use ledger.post(acct, cents, *, memo) and return the entry id 0x1F",
           "print hello world"]
LONG = " ".join("token%d" % i for i in range(6000))
CHEAP = [(0.9, 1.0, 10.0), (0.05, 1.0, 10.0), (0.5, 3.0, 4.0), (0.5, 0.0, 0.0)]

TASKS = [
    {"id": "t_cheap", "key": "tokenguard.router.should_try_cheap_first",
     "prompt": "Package `tokenguard` (importable) has, in `tokenguard.router`, a decision helper: given a "
               "calibrated success probability of the cheap tier and the per-call costs of the cheap and "
               "the expensive tier, it says whether to try the cheap tier first. In solution.py write "
               "go_cheap(p, cheap_cost, expensive_cost) that returns that module's boolean decision by "
               "calling it. solution.py only.",
     "verify": PRE + "from tokenguard import router as R" + NL + "from solution import go_cheap" + NL +
               "for s0,c0,c1 in " + repr(CHEAP) + ":" + NL +
               "    assert go_cheap(s0,c0,c1)==R.should_try_cheap_first(s0,c0,c1), (s0,c0,c1)" + NL},
    {"id": "t_match", "key": "tokenguard.canonmatch.match",
     "prompt": "Package `tokenguard` (importable) has, in `tokenguard.canonmatch`, a conservative test of "
               "whether two task descriptions canonicalize to the same (operation, target) key. In "
               "solution.py write same_task(a, b) that returns that module's boolean by calling it. "
               "solution.py only.",
     "verify": PRE + "from tokenguard import canonmatch as C" + NL + "from solution import same_task" + NL +
               "for a,b in " + repr(PAIRS) + ":" + NL +
               "    assert same_task(a,b)==C.match(a,b), (a,b)" + NL},
    {"id": "t_score", "key": "tokenguard.canonmatch.match_score",
     "prompt": "Package `tokenguard` (importable) has, in `tokenguard.canonmatch`, a graded task-similarity "
               "score: 1.0 for an exact key match, 0.5 for the same operation with a different target "
               "(or vice-versa), 0.0 otherwise. In solution.py write task_sim(a, b) that returns that "
               "module's score by calling it. solution.py only.",
     "verify": PRE + "from tokenguard import canonmatch as C" + NL + "from solution import task_sim" + NL +
               "for a,b in " + repr(PAIRS) + ":" + NL +
               "    assert abs(task_sim(a,b)-C.match_score(a,b))<1e-9, (a,b)" + NL},
    {"id": "t_idio", "key": "tokenguard.idiosyncrasy.is_idiosyncratic",
     "prompt": "Package `tokenguard` (importable) has, in `tokenguard.idiosyncrasy`, a gate that decides "
               "whether a task is idiosyncratic enough to warrant supplying private context; it returns a "
               "triple of (flag, score, features). In solution.py write idio_score(task) that returns "
               "that module's SCORE (the float) for a task string, calling the gate with its default "
               "arguments. solution.py only.",
     "verify": PRE + "from tokenguard import idiosyncrasy as I" + NL + "from solution import idio_score" + NL +
               "for t in " + repr(IDIO_IN) + ":" + NL +
               "    assert abs(idio_score(t)-I.is_idiosyncratic(t)[1])<1e-9, t" + NL},
    {"id": "t_feats", "key": "tokenguard.idiosyncrasy.extract_features",
     "prompt": "Package `tokenguard` (importable) has, in `tokenguard.idiosyncrasy`, a pre-hoc feature "
               "extractor for a task string (camel-case density, convention hints, magic numbers, and a "
               "perplexity slot that stays None unless a perplexity function is supplied). In solution.py "
               "write feats(task) that returns that module's feature dict for a task, default arguments. "
               "solution.py only.",
     "verify": PRE + "from tokenguard import idiosyncrasy as I" + NL + "from solution import feats" + NL +
               "for t in " + repr(IDIO_IN) + ":" + NL +
               "    assert feats(t)==I.extract_features(t), t" + NL},
    {"id": "t_compress", "key": "tokenguard.compress.compress_output",
     "prompt": "Package `tokenguard` (importable) has, in `tokenguard.compress`, a compactor for long model "
               "outputs that returns (compressed_text, original_tokens, saved_tokens); small outputs come "
               "back unchanged with saved 0, and it never raises. In solution.py write shrink(text) that "
               "returns that module's triple for the default thresholds. solution.py only.",
     "verify": PRE + "from tokenguard import compress as K" + NL + "from solution import shrink" + NL +
               "LONG=" + repr(LONG) + NL +
               "for t in [LONG, 'ok done']:" + NL +
               "    assert tuple(shrink(t))==tuple(K.compress_output(t)), len(t)" + NL},
]

REF = {
    "t_cheap":    "from tokenguard import router as R" + NL + "def go_cheap(p,a,b): return R.should_try_cheap_first(p,a,b)",
    "t_match":    "from tokenguard import canonmatch as C" + NL + "def same_task(a,b): return C.match(a,b)",
    "t_score":    "from tokenguard import canonmatch as C" + NL + "def task_sim(a,b): return C.match_score(a,b)",
    "t_idio":     "from tokenguard import idiosyncrasy as I" + NL + "def idio_score(t): return I.is_idiosyncratic(t)[1]",
    "t_feats":    "from tokenguard import idiosyncrasy as I" + NL + "def feats(t): return I.extract_features(t)",
    "t_compress": "from tokenguard import compress as K" + NL + "def shrink(t): return K.compress_output(t)",
}
WRONG = ("def go_cheap(p,a,b): return True" + NL + "def same_task(a,b): return False" + NL +
         "def task_sim(a,b): return 0.0" + NL + "def idio_score(t): return 0.0" + NL +
         "def feats(t): return {}" + NL + "def shrink(t): return (t, 0, 0)")
