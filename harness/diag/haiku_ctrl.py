"""Import-neutralized CONTROL for api_post_ok on Haiku: identical prompt, arms and contract
check, but the verifier binds `ledger` into the solution's namespace when the model omitted the
import line, so the cell measures the private contract (arg order / kw-only memo / return id)
and not import hygiene. Raw completions are retained. Usage: haiku_ctrl.py N OUT_DIR"""
import sys, json, subprocess, tempfile, shutil, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard\tokenbench")
import measure_blackwell as mb
MODEL = "claude-haiku-4-5-20251001"; N = int(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
task = next(t for t in mb.TASKS if t["id"] == "api_post_ok")
assert task["verify"].startswith(mb._LEDGER_STUB)
NEUTRAL = (mb._LEDGER_STUB
           + "import solution as _s\n_s.__dict__.setdefault('ledger',led)\n_s.__dict__.setdefault('post',led.post)\n"
           + task["verify"][len(mb._LEDGER_STUB):])
def one(arm, i):
    wd = Path(tempfile.mkdtemp(prefix="bwctrl_")); rec = {"arm": arm, "i": i}
    try:
        ctx = mb.ARMS[arm]; prompt = ((ctx + "\n\n") if ctx else "") + task["prompt"]
        sp = prompt + " Return ONLY the raw Python file content, no markdown fences, no prose, and do NOT use any tools or write any files."
        cmd = mb.claude_cmd(["-p", " ".join(sp.split()), "--model", MODEL, "--output-format", "json", "--max-turns", "1", "--dangerously-skip-permissions"])
        last = None
        for attempt in range(3):
            try:
                r = subprocess.run(cmd, cwd=str(wd), capture_output=True, text=True, encoding="utf-8", timeout=200)
                out = json.loads((r.stdout or "").strip().splitlines()[-1])
                toks = (out.get("usage", {}) or {}).get("output_tokens", 0)
                if out.get("is_error") or (not out.get("result") and toks == 0): raise RuntimeError("empty/error result")
                raw = out.get("result", "") or ""; code = mb._extract_code(raw)
                (wd / "solution.py").write_text(code, encoding="utf-8")
                def run_verify(snippet):
                    (wd / "_v.py").write_text("import sys;sys.path.insert(0,'.')\n" + snippet + "\nprint('ok')", encoding="utf-8")
                    v = subprocess.run([sys.executable, str(wd / "_v.py")], cwd=str(wd), capture_output=True, text=True, timeout=30)
                    return v.returncode == 0, (v.stderr or "")[-400:]
                rec["pass_original"], rec["stderr_original"] = run_verify(task["verify"])
                rec["pass_neutral"],  rec["stderr_neutral"]  = run_verify(NEUTRAL)
                rec["has_import"] = bool(re.search(r"^\s*(import ledger|from ledger import)", code, re.M))
                rec["encoded_amount"] = bool(re.search(r"#\{|f\"\{sign\}|check\s*=|% 10", code))
                rec["cost"] = out.get("total_cost_usd", 0.0); rec["out_tokens"] = toks; rec["raw"] = raw; rec["code"] = code
                return rec
            except Exception as e:
                last = e; import time; time.sleep(5 * (attempt + 1) ** 2)
        rec["error"] = str(last)[:100]; rec["pass_original"] = rec["pass_neutral"] = False; return rec
    finally: shutil.rmtree(wd, ignore_errors=True)
summary = {}
ARMS = sys.argv[3].split(",") if len(sys.argv) > 3 else ["none", "W1", "W2", "W1plus"]
for arm in ARMS:
    with ThreadPoolExecutor(max_workers=3) as ex: rows = list(ex.map(lambda i: one(arm, i), range(N)))
    ko = sum(r["pass_original"] for r in rows); kn = sum(r["pass_neutral"] for r in rows)
    imp = sum(r.get("has_import", False) for r in rows); errs = sum(1 for r in rows if r.get("error"))
    summary[arm] = {"pass_original": ko, "pass_neutral": kn, "n": N, "with_import": imp, "errs": errs,
                    "spend": round(sum(r.get("cost", 0) for r in rows), 3)}
    print(f"  arm={arm:<6} original-verifier {ko}/{N}={ko/N:.0%}   import-neutralized {kn}/{N}={kn/N:.0%}   import present {imp}/{N}   errs={errs}", flush=True)
    json.dump(rows, open(OUT / f"ctrl_api_post_ok_{arm}.json", "w", encoding="utf-8"), indent=1)
json.dump(summary, open(OUT / ("ctrl_api_post_ok_summary_" + "_".join(ARMS) + ".json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(summary, indent=1))
