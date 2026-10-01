r"""Both graders, applied to every retained reply.

Primary: the grader that produced the published record (harness commit 5a5dbcc), whose pass signal
is the exit status of the verification script. Its code is reproduced below unchanged except for one
deliberate deviation: the child process receives the current harness's credential-stripped
environment (measure_blackwell._child_env) instead of the parent's, so that model-generated code
never runs with the provider keys this driver authenticates with. The checks are the task strings in
measure_blackwell.TASKS, identical at 5a5dbcc and at HEAD.

Secondary: the current grader, measure_blackwell.verify_in, which requires a parent-generated token
and treats an early SystemExit as a failure. The two can disagree only on a reply that exits early.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import measure_blackwell as mb  # noqa: E402


def verify_published(wd: Path, snippet: str) -> bool:
    (wd / "_v.py").write_text("import sys;sys.path.insert(0,'.')\n" + snippet +
                              "\nprint('ok')", encoding="utf-8")
    try:
        return subprocess.run([sys.executable, str(wd / "_v.py")], cwd=str(wd),
                              capture_output=True, timeout=30,
                              env=mb._child_env()).returncode == 0
    except Exception:
        return False


def grade(task, code):
    """Grade one extracted solution with both graders, each in a fresh directory. A reply holding a
    lone surrogate is written as it is (surrogatepass), so it fails to import instead of stopping
    the run."""
    out = {}
    for name, fn in (("published", verify_published), ("current", mb.verify_in)):
        wd = Path(tempfile.mkdtemp(prefix="bwrep_"))
        try:
            (wd / "solution.py").write_text(code, encoding="utf-8", errors="surrogatepass")
            out[name] = bool(fn(wd, task["verify"]))
        finally:
            shutil.rmtree(wd, ignore_errors=True)
    return out
