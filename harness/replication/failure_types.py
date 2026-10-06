r"""Failure types of the replication's failing replies, by model, task and condition (R4.6).

Every graded observation that FAILS under the primary grader gets exactly one type, checked in
this order:
  truncated      the reply stopped at the output limit (stop reason length / max_tokens /
                 incomplete), whatever text it kept
  empty          no final text at all
  refusal        prose outside code fences matches the paper's refusal pattern (Appendix B.2)
  no code        the extracted text contains neither a function definition nor an import
  syntax         the extracted code does not parse
and otherwise the code is executed against the task's checks (the current grader's verifier, in
the credential-stripped environment) and typed by the exception that ended it:
  import/name    ImportError, ModuleNotFoundError, NameError (e.g. a missing `import ledger`)
  wrong call     TypeError (e.g. the memo passed positionally; Python's own signature check)
  contract       ledger.PostError (e.g. account and amount swapped)
  wrong result   AssertionError (a call or a return value that the checks reject)
  other runtime  any other exception; timeout if the checks did not finish
A failing reply whose code passes when re-executed is reported as 'passes on re-execution'
(the published and current graders differ on one observation).

Reads the records only; makes no model call.   python harness/replication/failure_types.py
"""
import ast
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import records  # noqa: E402
import measure_blackwell as mb  # noqa: E402

LIMIT = ("length", "max_tokens", "max_output_tokens", "incomplete")
REFUSAL = re.compile(r"\bI can(?:no|')t\b|\bI won't\b|\bI'm (?:not able|unable)\b"
                     r"|\bunable to (?:help|assist|comply)\b|\bI must decline\b", re.I)
FENCE = re.compile(r"```.*?```", re.S)
ORDER = ["truncated", "empty", "refusal", "no code", "syntax", "import/name", "wrong call", "contract",
         "wrong result", "other runtime", "timeout", "passes on re-execution"]


def exec_type(code, snippet):
    """Run the checks on the code and return the name of the exception that ended them."""
    wd = Path(tempfile.mkdtemp(prefix="ft_"))
    try:
        (wd / "solution.py").write_text(code, encoding="utf-8")
        indented = "\n".join("    " + ln for ln in snippet.split("\n"))
        src = ("import sys, json\nsys.path.insert(0, '.')\n_r = 'ok'\ntry:\n" + indented +
               "\nexcept BaseException as e:\n    _r = type(e).__name__\n"
               "print('@@RESULT@@' + _r)\n")
        (wd / "_ft.py").write_text(src, encoding="utf-8")
        try:
            out = subprocess.run([sys.executable, str(wd / "_ft.py")], cwd=str(wd), capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", timeout=30, env=mb._child_env())
        except subprocess.TimeoutExpired:
            return "timeout"
        m = re.findall(r"@@RESULT@@(\w+)", out.stdout or "")
        return m[-1] if m else "no result"
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def classify(rc, code):
    text = rc.get("raw_text") or ""
    if (rc.get("stop_reason") or "") in LIMIT:
        return "truncated"
    if not text.strip():
        return "empty"
    if REFUSAL.search(FENCE.sub(" ", text)):
        return "refusal"
    if not re.search(r"^\s*(def |import |from \S+ import )", code, re.M):
        return "no code"
    try:
        ast.parse(code)
    except SyntaxError:
        return "syntax"
    return None


def main():
    st = records.read_dir(str(ROOT / "results" / "replication" / "records"))
    R, G = st["receipts"], st["grades"]
    verify = {t["id"]: t["verify"] for t in mb.TASKS}
    failing = [s for s in G if s in R and not R[s]["transport_failed"] and not G[s]["pass_published"]]
    pre, need_exec = {}, []
    for s in failing:
        code = mb._extract_code(R[s].get("raw_text") or "")
        c = classify(R[s], code)
        if c:
            pre[s] = c
        else:
            need_exec.append((s, code))
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda sc: (sc[0], exec_type(sc[1], verify[R[sc[0]]["task"]])), need_exec))
    MAP = {"ImportError": "import/name", "ModuleNotFoundError": "import/name", "NameError": "import/name",
           "TypeError": "wrong call", "PostError": "contract", "AssertionError": "wrong result",
           "timeout": "timeout", "ok": "passes on re-execution"}
    types = dict(pre)
    raw_exc = Counter()
    for s, exc in results:
        raw_exc[exc] += 1
        types[s] = MAP.get(exc, "other runtime")
    table = defaultdict(Counter)
    for s, t in types.items():
        r = R[s]
        table[(r["model"], r["task"], r["condition"])][t] += 1
    out = {"n_failing": len(failing), "overall": dict(Counter(types.values())),
           "exceptions_on_execution": dict(raw_exc),
           "by_cell": {"|".join(k): dict(v) for k, v in sorted(table.items())}}
    json.dump(out, open(ROOT / "results" / "replication" / "failure_types.json", "w", encoding="utf-8"), indent=1)
    print("failing graded observations: %d" % len(failing))
    print("overall: " + ", ".join("%s %d" % (t, out["overall"].get(t, 0)) for t in ORDER if out["overall"].get(t)))
    print("exceptions on execution: %s" % dict(raw_exc))
    cols = [t for t in ORDER if out["overall"].get(t)]
    print("\n%-34s" % "model | task | condition" + "".join("%9s" % c[:8] for c in cols))
    for k, v in sorted(table.items()):
        print("%-34s" % " | ".join(k) + "".join("%9s" % (v.get(c, "") or ".") for c in cols))


if __name__ == "__main__":
    main()
