"""BigCodeBench pilot: pandas vs scipy, 10 tasks per side, two designs.

(a) SANDBOX  - the real library is blocked while the solution module is imported,
    so the renamed shim `qx7` is the only route. The task's own test runs unchanged.
(b) CONTRACT - the task and its test are untouched; a private call contract is
    appended (the solution must register a private token via qx7), and one extra
    assertion checks it. Task semantics do not move.
"""
import json, re, os, sys, io, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SP = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(SP, "bcb.json"), encoding="utf-8"))

STD = set("""os sys re json math random collections itertools datetime string csv io time glob shutil
hashlib base64 struct subprocess logging warnings functools operator pathlib textwrap unicodedata
heapq bisect codecs binascii zlib gzip pickle sqlite3 socket smtplib email urllib ssl secrets
statistics decimal fractions uuid threading queue traceback ast inspect types copy enum abc typing
tempfile stat errno signal platform getpass shlex difflib pprint cmath array mmap select ctypes
multiprocessing concurrent xml html http ftplib imaplib poplib mimetypes""".split())
HAVE = {"scipy", "numpy", "pandas", "matplotlib", "PIL", "requests", "bs4", "cv2", "werkzeug"}

def libs(r):
    v = r.get("libs")
    if isinstance(v, str):
        try:
            v = json.loads(v.replace("'", '"'))
        except Exception:
            v = [x.strip().strip("'\"") for x in v.strip("[]").split(",") if x.strip()]
    return set(v or [])

PD = {"DataFrame": "Grid", "Series": "Column", "read_csv": "load_table",
      "concat": "stack_frames", "merge": "join_on", "to_datetime": "as_instant"}
SC = {"norm": "bell", "zscore": "standard_score", "linregress": "line_fit",
      "ttest_ind": "two_sample", "curve_fit": "fit_curve", "pearsonr": "corr_pair"}
SC_SRC = {"norm": "scipy.stats", "zscore": "scipy.stats", "linregress": "scipy.stats",
          "ttest_ind": "scipy.stats", "curve_fit": "scipy.optimize", "pearsonr": "scipy.stats"}

def doc(mapping, title, srcmap=None, mod="pandas"):
    out = ["TEAM CONTEXT (private) -- %s." % title,
           "This team reaches these primitives only through the module `qx7`. The names below are",
           "internal: they appear in no public documentation and cannot be guessed from the task."]
    for real, fake in mapping.items():
        src = srcmap[real] if srcmap else mod
        out.append("  qx7.%-16s is the %s primitive of %s" % (fake, real, src))
    return "\n".join(out)

W_PD = doc(PD, "table primitives")
W_SC = doc(SC, "statistical primitives", SC_SRC)

shim = ["# qx7 -- private team shim. Renamed re-exports; these names are not public.",
        "import pandas as _pd", "from scipy import stats as _st", "from scipy import optimize as _opt"]
for real, fake in PD.items():
    shim.append("%s = _pd.%s" % (fake, real))
for real, fake in SC.items():
    src = "_opt" if SC_SRC[real] == "scipy.optimize" else "_st"
    shim.append("%s = %s.%s" % (fake, src, real))
shim += ["", "_REGISTERED = []", "", "def register(token):",
         '    """Private call contract: a solution must register its team token."""',
         "    _REGISTERED.append(token)", "    return True"]
SHIM = "\n".join(shim) + "\n"

def uses(r, names):
    p = (r.get("code_prompt") or "") + (r.get("canonical_solution") or "")
    return any(re.search(r"\b%s\b" % n, p) for n in names)

runnable = [r for r in rows if (libs(r) - STD) <= HAVE]
pd_tasks = [r for r in runnable if "pandas" in libs(r) and "scipy" not in libs(r) and uses(r, PD)]
sc_tasks = [r for r in runnable if "scipy" in libs(r) and "pandas" not in libs(r) and uses(r, SC)]
random.Random(20260908).shuffle(pd_tasks)
random.Random(20260908).shuffle(sc_tasks)
pd_tasks, sc_tasks = pd_tasks[:10], sc_tasks[:10]

print("pandas-side %d   scipy-side %d   (all deps installed)" % (len(pd_tasks), len(sc_tasks)))
for r in pd_tasks[:4]:
    print("   PD", r["task_id"], sorted(libs(r)))
for r in sc_tasks[:4]:
    print("   SC", r["task_id"], sorted(libs(r)))

keep = ("task_id", "code_prompt", "canonical_solution", "test", "entry_point", "instruct_prompt")
json.dump({"W_PD": W_PD, "W_SC": W_SC, "SHIM": SHIM,
           "pd_tasks": [{k: r.get(k) for k in keep} for r in pd_tasks],
           "sc_tasks": [{k: r.get(k) for k in keep} for r in sc_tasks]},
          open(os.path.join(SP, "bcb_pilot.json"), "w", encoding="utf-8"), indent=1)
print()
print(W_PD)
print()
print("written bcb_pilot.json")
