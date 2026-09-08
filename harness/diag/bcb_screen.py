"""Screen BigCodeBench tasks for a usable ceiling.

The first pilot failed because the base solve rate was 20-50%: with everything near
the floor there is no headroom for a crossover to show. This screens a larger pool
with NO context and keeps only tasks the model already solves reliably, so that a
private convention has something to knock down.

  python bcb_screen.py --model DeepSeek-V4-Pro --n 3 --pool 60 --out ../../results/bcb
"""
import json, os, re, sys, subprocess, tempfile, shutil, argparse, random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

HARNESS = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, HARNESS)
import measure_blackwell as mb  # noqa: E402

STD = set("""os sys re json math random collections itertools datetime string csv io time glob shutil
hashlib base64 struct subprocess logging warnings functools operator pathlib textwrap unicodedata
heapq bisect codecs binascii zlib gzip pickle sqlite3 socket smtplib email urllib ssl secrets
statistics decimal fractions uuid threading queue traceback ast inspect types copy enum abc typing
tempfile stat errno signal platform getpass shlex difflib pprint cmath array mmap select ctypes
multiprocessing concurrent xml html http ftplib imaplib poplib mimetypes""".split())
HAVE = {"scipy", "numpy", "pandas", "matplotlib", "PIL", "requests", "bs4", "cv2", "werkzeug"}
PD = {"DataFrame", "Series", "read_csv", "concat", "merge", "to_datetime"}
SC = {"norm", "zscore", "linregress", "ttest_ind", "curve_fit", "pearsonr"}


def libs(r):
    v = r.get("libs")
    if isinstance(v, str):
        try:
            v = json.loads(v.replace("'", '"'))
        except Exception:
            v = [x.strip().strip("'\"") for x in v.strip("[]").split(",") if x.strip()]
    return set(v or [])


def solve_once(model, task):
    """One no-context attempt, scored by the task's own unchanged test."""
    wd = Path(tempfile.mkdtemp(prefix="scr_"))
    try:
        prompt = ((task.get("instruct_prompt") or task.get("code_prompt") or "") +
                  " Return ONLY the raw Python file content, no markdown fences, no prose.")
        text, _ = mb._azure_complete(" ".join(prompt.split()), model)
        (wd / "solution.py").write_text(mb._extract_code(text), encoding="utf-8")
        run = ["import sys; sys.path.insert(0,'.')", "import solution", "from solution import *",
               task["test"], "import unittest",
               "_r=unittest.TextTestRunner(verbosity=0).run(",
               "  unittest.TestLoader().loadTestsFromTestCase(TestCases))",
               "assert _r.wasSuccessful()", "print('ok')"]
        (wd / "_run.py").write_text("\n".join(run), encoding="utf-8")
        v = subprocess.run([sys.executable, str(wd / "_run.py")], cwd=str(wd),
                           capture_output=True, text=True, timeout=120)
        return v.returncode == 0
    except Exception:
        return False
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--bcb", required=True)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--pool", type=int, default=60)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = json.load(open(a.bcb, encoding="utf-8"))
    runnable = [r for r in rows if (libs(r) - STD) <= HAVE]

    def uses(r, names):
        p = (r.get("code_prompt") or "") + (r.get("canonical_solution") or "")
        return any(re.search(r"\b%s\b" % n, p) for n in names)

    pool = {}
    for side, want, other in (("pd", PD, "scipy"), ("sc", SC, "pandas")):
        lib = "pandas" if side == "pd" else "scipy"
        c = [r for r in runnable if lib in libs(r) and other not in libs(r) and uses(r, want)]
        random.Random(20260908).shuffle(c)
        pool[side] = c[:a.pool]
        print("%s pool: %d" % (side, len(pool[side])))

    jobs = [(side, t, i) for side in pool for t in pool[side] for i in range(a.n)]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(lambda j: (j[0], j[1]["task_id"], solve_once(a.model, j[1])), jobs))

    agg = {}
    for side, tid, ok in res:
        d = agg.setdefault((side, tid), [0, 0])
        d[0] += bool(ok); d[1] += 1

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    keep = {"pd": [], "sc": []}
    for (side, tid), (k, n) in sorted(agg.items()):
        if k / n >= 0.8:
            keep[side].append(tid)
    json.dump({"rates": {"%s|%s" % k: v for k, v in agg.items()}, "keep": keep},
              open(out / "bcb_screen.json", "w", encoding="utf-8"), indent=1)

    for side in ("pd", "sc"):
        rates = [k / n for (s, _), (k, n) in agg.items() if s == side]
        hi = sum(1 for r in rates if r >= 0.8)
        print("%s: %d tasks screened, mean base rate %.2f, >=80%%: %d"
              % (side, len(rates), sum(rates) / max(1, len(rates)), hi))
    print("kept:", {k: len(v) for k, v in keep.items()})


if __name__ == "__main__":
    main()
