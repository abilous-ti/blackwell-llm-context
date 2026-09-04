"""Diagnostic: re-run Haiku single-shot on one cell, KEEPING raw completions and
verifier stderr, then classify every failure (extraction / import / contract / other).
Reuses the harness's own prompt, arm text, extractor and verifier so the regime is identical."""
import sys, json, subprocess, tempfile, shutil, re, collections
from pathlib import Path
sys.path.insert(0, r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard\tokenbench")
import measure_blackwell as mb

MODEL = "claude-haiku-4-5-20251001"
TASK_ID, ARM, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
OUT = Path(sys.argv[4]); OUT.mkdir(parents=True, exist_ok=True)
task = next(t for t in mb.TASKS if t["id"] == TASK_ID)
ctx = mb.ARMS[ARM]
prompt = ((ctx + "\n\n") if ctx else "") + task["prompt"]
sp = (prompt + " Return ONLY the raw Python file content, no markdown fences, no prose, "
      "and do NOT use any tools or write any files.")
cmd = mb.claude_cmd(["-p", " ".join(sp.split()), "--model", MODEL, "--output-format", "json",
                     "--max-turns", "1", "--dangerously-skip-permissions"])

def classify(code, stderr):
    if "SyntaxError" in stderr or "IndentationError" in stderr: return "EXTRACTION/prose->SyntaxError"
    if "ModuleNotFoundError" in stderr or "ImportError" in stderr: return "IMPORT"
    if "cannot import name" in stderr: return "IMPORT(name)"
    if "wrong call" in stderr: return "CONTRACT(_CALLS mismatch)"
    if "bad id" in stderr: return "RETURN(bad id)"
    if "PostError" in stderr: return "PostError raised"
    if "TypeError" in stderr: return "TypeError(argorder/kw)"
    if "AssertionError" in stderr: return "ASSERT(other)"
    return "OTHER"

rows = []
for i in range(N):
    wd = Path(tempfile.mkdtemp(prefix="bwdiag_"))
    rec = {"i": i}
    try:
        r = subprocess.run(cmd, cwd=str(wd), capture_output=True, text=True, encoding="utf-8", timeout=200)
        lines = (r.stdout or "").strip().splitlines()
        out = json.loads(lines[-1]) if lines else {}
        raw = out.get("result", "") or ""
        rec["out_tokens"] = (out.get("usage", {}) or {}).get("output_tokens", 0)
        rec["cost"] = out.get("total_cost_usd", 0.0)
        rec["is_error"] = bool(out.get("is_error"))
        code = mb._extract_code(raw)
        (wd / "solution.py").write_text(code, encoding="utf-8")
        (wd / "_v.py").write_text("import sys;sys.path.insert(0,'.')\n" + task["verify"] + "\nprint('ok')", encoding="utf-8")
        v = subprocess.run([sys.executable, str(wd / "_v.py")], cwd=str(wd), capture_output=True, text=True, timeout=30)
        rec["pass"] = v.returncode == 0
        rec["stderr_tail"] = (v.stderr or "")[-600:]
        rec["fenced"] = bool(re.search(r"```", raw))
        rec["starts_with_prose"] = not raw.lstrip().startswith(("import", "from", "def", "#", '"""', "'''"))
        rec["raw"] = raw; rec["code"] = code
        rec["class"] = "PASS" if rec["pass"] else classify(code, rec["stderr_tail"])
    except Exception as e:
        rec["pass"] = False; rec["class"] = f"HARNESS:{type(e).__name__}:{str(e)[:80]}"
    finally:
        shutil.rmtree(wd, ignore_errors=True)
    rows.append(rec)
    print(f"[{i:02d}] {'PASS' if rec.get('pass') else 'FAIL'}  {rec['class']}  fenced={rec.get('fenced')} prose={rec.get('starts_with_prose')} toks={rec.get('out_tokens')}", flush=True)

(OUT / f"{TASK_ID}_{ARM}_diag.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
k = sum(r.get("pass", False) for r in rows)
print(f"\nPASS {k}/{N} = {k/N:.0%}   spend ${sum(r.get('cost',0) for r in rows):.3f}")
print("failure classes:", dict(collections.Counter(r["class"] for r in rows if not r.get("pass"))))
