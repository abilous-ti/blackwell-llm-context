"""BigCodeBench pilot for the context partial order.

Two designs for making a private convention DECISIVE on a natural task, because
BigCodeBench's own tests check the behaviour of task_func and not which API produced
it -- so renaming alone changes nothing.

  sandbox   the real library is blocked while the solution module is imported, so the
            renamed shim qx7 is the only route. The task's own test runs UNCHANGED.
  contract  task and test untouched; the solution must additionally register a private
            token through qx7, and one appended assertion checks it.

Four arms per task: none, W_PD, W_SC, W_PD+W_SC. A pandas-side task needs W_PD; a
scipy-side task needs W_SC; neither document reveals the other's names or token.

  python bcb_pilot.py --design sandbox --model DeepSeek-V4-Pro --out ../../results/bcb
"""
import json, os, re, sys, subprocess, tempfile, shutil, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

HARNESS = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, HARNESS)
import measure_blackwell as mb  # noqa: E402

TOKEN_PD = "qx7-tbl-4417"
TOKEN_SC = "qx7-stat-9052"

SANDBOX_RULE = (" You may NOT import pandas or scipy directly; the only sanctioned access path is"
                " the module `qx7`, whose names are given in the team context.")
CONTRACT_RULE = (" Before returning, your function must call `qx7.register(TOKEN)` exactly once,"
                 " with the private team token given in the team context.")


def build_prompt(task, arm, design, side, sources):
    ctx = ""
    if arm == "W_PD":
        ctx = sources["W_PD"]
    elif arm == "W_SC":
        ctx = sources["W_SC"]
    elif arm == "W_BOTH":
        ctx = sources["W_SC"] + "\n\n" + sources["W_PD"]
    rule = SANDBOX_RULE if design == "sandbox" else CONTRACT_RULE
    body = task.get("instruct_prompt") or task.get("code_prompt") or ""
    head = (ctx + "\n\n") if ctx else ""
    return (head + body + rule +
            " Return ONLY the raw Python file content, no markdown fences, no prose.")


BLOCKER = '''
import sys, importlib.abc, importlib.machinery
class _Blocked(importlib.abc.MetaPathFinder):
    def __init__(self, names): self.names = set(names)
    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".")[0]
        if root in self.names:
            raise ImportError("module %r is not available in this sandbox" % fullname)
        return None
'''


def runner_source(design, side, test_src):
    """The script executed in the temp dir: import shim, (block), import solution, run test."""
    reg = TOKEN_PD if side == "pd" else TOKEN_SC
    parts = ["import sys; sys.path.insert(0, '.')", "import qx7"]
    if design == "sandbox":
        parts += [BLOCKER,
                  "sys.meta_path.insert(0, _Blocked(['pandas', 'scipy']))",
                  "import solution",
                  "sys.meta_path.pop(0)"]
    else:
        parts += ["import solution"]
    parts += ["from solution import *", test_src, "import unittest",
              "_r = unittest.TextTestRunner(verbosity=0).run(",
              "    unittest.TestLoader().loadTestsFromTestCase(TestCases))",
              "assert _r.wasSuccessful(), 'task test failed'"]
    if design == "contract":
        # the task's own test calls task_func several times, so the contract is
        # "registered, and only ever with this token", not "registered exactly once".
        parts += ["assert qx7._REGISTERED and set(qx7._REGISTERED) == {%r}, "
                  "('contract', qx7._REGISTERED)" % reg]
    parts += ["print('ok')"]
    return "\n".join(parts)


def one(model, task, arm, design, side, sources, i):
    wd = Path(tempfile.mkdtemp(prefix="bcb_"))
    rec = {"task_id": task["task_id"], "arm": arm, "design": design, "side": side, "i": i}
    try:
        prompt = build_prompt(task, arm, design, side, sources)
        last = None
        for attempt in range(3):
            try:
                text, toks = mb._azure_complete(" ".join(prompt.split()), model)
                code = mb._extract_code(text)
                (wd / "qx7.py").write_text(sources["SHIM"], encoding="utf-8")
                (wd / "solution.py").write_text(code, encoding="utf-8")
                (wd / "_run.py").write_text(runner_source(design, side, task["test"]),
                                            encoding="utf-8")
                v = subprocess.run([sys.executable, str(wd / "_run.py")], cwd=str(wd),
                                   capture_output=True, text=True, timeout=120)
                # sandbox is enforced statically: a meta_path blocker only sees
                # module-level imports, and a function-body import evades it.
                banned = bool(re.search(r"(?m)^\s*(import|from)\s+(pandas|scipy)\b", code)) \
                         or bool(re.search(r"(?m)^\s+(import|from)\s+(pandas|scipy)\b", code))
                rec["banned_import"] = banned
                rec["pass"] = (v.returncode == 0) and not (design == "sandbox" and banned)
                rec["stderr_tail"] = (v.stderr or "")[-350:]
                rec["uses_qx7"] = "qx7" in code
                rec["direct_import"] = bool(re.search(r"^\s*(import|from)\s+(pandas|scipy)", code, re.M))
                rec["out_tokens"] = toks
                rec["code"] = code
                return rec
            except Exception as e:
                last = e
                import time
                time.sleep(3 * (attempt + 1))
        rec["error"] = "%s: %s" % (type(last).__name__, str(last)[:110])
        rec["pass"] = False
        return rec
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True, choices=["sandbox", "contract"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--pilot", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--keep", default=None,
                    help="bcb_screen.json: restrict to tasks whose no-context base rate is high")
    a = ap.parse_args()

    src = json.load(open(a.pilot, encoding="utf-8"))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    keep = None
    if a.keep:
        keep = json.load(open(a.keep, encoding="utf-8"))["keep"]
    jobs = []
    for side, key in (("pd", "pd_tasks"), ("sc", "sc_tasks")):
        for t in src[key]:
            if keep is not None and t["task_id"] not in keep[side]:
                continue
            for arm in ("none", "W_PD", "W_SC", "W_BOTH"):
                jobs.append((t, arm, side))

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        rows = list(ex.map(lambda j: one(a.model, j[0], j[1], a.design, j[2], src, 0), jobs))

    json.dump(rows, open(out / ("bcb_%s_%s.json" % (a.design, re.sub(r'[^A-Za-z0-9]', '', a.model))),
                         "w", encoding="utf-8"), indent=1)

    print("design=%s model=%s" % (a.design, a.model))
    print("%-6s %-8s %-8s %-8s %-8s" % ("side", "none", "W_PD", "W_SC", "W_BOTH"))
    for side in ("pd", "sc"):
        cells = []
        for arm in ("none", "W_PD", "W_SC", "W_BOTH"):
            sel = [r for r in rows if r["side"] == side and r["arm"] == arm]
            cells.append("%d/%d" % (sum(bool(r.get("pass")) for r in sel), len(sel)))
        print("%-6s %-8s %-8s %-8s %-8s" % (side, *cells))
    err = sum(1 for r in rows if r.get("error"))
    print("transport errors: %d / %d" % (err, len(rows)))


if __name__ == "__main__":
    main()
