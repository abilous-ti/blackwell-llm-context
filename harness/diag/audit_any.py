"""Packaging / import / content audit for ANY model in the paper-1 roster.

Re-runs a (task, arm) cell keeping every raw completion, then scores each draw under
BOTH verifiers:
  * original  -- the published verifier (import hygiene counts against the model)
  * neutral   -- binds `ledger` into the solution namespace when the reply omitted the
                 import, so the cell measures the private contract, not import hygiene

and records the packaging signals a reviewer would ask about: was the reply fenced, did
it start with prose, did the extractor come back empty, is the decisive call present.

Backends: claude CLI (Anthropic), Azure OpenAI-style chat completions, Codex CLI (GPT).
Credentials are read from the environment only and are never written to disk.

  python audit_any.py --kind azure --model DeepSeek-V4-Pro --task api_post_ok \
                      --arms W1,W1plus --n 40 --out ../../results/audit
"""
import sys, os, json, re, subprocess, tempfile, shutil, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

HARNESS = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, HARNESS)
import measure_blackwell as mb  # noqa: E402


def build_neutral(task):
    """Verifier that does not punish a missing `import ledger`.

    Cells whose verifier does not stub the ledger (enc_amount) have no import to
    neutralize; the published verifier is returned unchanged, so pass_neutral equals
    pass_original there rather than silently meaning something else."""
    if not task["verify"].startswith(mb._LEDGER_STUB):
        return task["verify"]
    return (mb._LEDGER_STUB
            + "import solution as _s\n"
            + "_s.__dict__.setdefault('ledger',led)\n"
            + "_s.__dict__.setdefault('post',led.post)\n"
            + task["verify"][len(mb._LEDGER_STUB):])


# The published harness sends DIFFERENT suffixes per backend. Reproduce them exactly,
# or the audit measures a different prompt than the run it is auditing.
SUFFIX = {
    # measure_blackwell.run_one, non-Anthropic branch
    "azure": " Return ONLY the raw Python file content, no markdown fences, no prose.",
    # measure_blackwell.run_one, singleshot branch
    "cli": (" Return ONLY the raw Python file content, no markdown fences, no prose, "
            "and do NOT use any tools or write any files."),
    # NOT a paper-1 regime: paper 1 ran GPT-5.5 as a single-shot Azure completion
    "codex": " Return ONLY the raw Python file content, no markdown fences, no prose.",
}


IMPORT_CLAUSE = (" Write a standalone module that begins with an absolute `import ledger`"
                 " statement; do not assume the module is already in scope.")


def complete(kind, model, prompt, wd):
    """Return (raw_text, out_tokens). Raises on a transport failure."""
    if kind == "cli":
        cmd = mb.claude_cmd(["-p", " ".join(prompt.split()), "--model", model,
                             "--output-format", "json", "--max-turns", "1",
                             "--dangerously-skip-permissions"])
        r = subprocess.run(cmd, cwd=str(wd), capture_output=True, text=True,
                           encoding="utf-8", timeout=240)
        lines = (r.stdout or "").strip().splitlines()
        if not lines:
            raise RuntimeError("empty cli stdout")
        out = json.loads(lines[-1])
        toks = (out.get("usage", {}) or {}).get("output_tokens", 0)
        if out.get("is_error") or (not out.get("result") and toks == 0):
            raise RuntimeError("cli error/empty result")
        served = ",".join((out.get("modelUsage") or {}).keys()) or model
        return out.get("result", "") or "", toks, served
    if kind == "azure":
        text, toks = mb._azure_complete(prompt, model)
        return text, toks, model      # Azure echoes the deployment name we asked for
    if kind == "codex":
        exe = shutil.which("codex") or "codex"
        argv = [exe, "exec", "--skip-git-repo-check"]
        if model and model != "default":
            argv += ["--model", model]        # never rely on the CLI default
        argv += [" ".join(prompt.split())]
        if os.name == "nt" and exe.lower().endswith((".cmd", ".bat")):
            argv = [os.environ.get("COMSPEC", "cmd.exe"), "/c"] + argv
        # Popen + tree kill: a plain subprocess.run timeout only reaps cmd.exe and
        # leaves codex/node holding the pipe, which wedges the worker indefinitely.
        pr = subprocess.Popen(argv, cwd=str(wd), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, encoding="utf-8")
        try:
            txt, err = pr.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pr.pid), "/T", "/F"],
                               capture_output=True)
            else:
                pr.kill()
            try:
                pr.communicate(timeout=15)
            except Exception:
                pass
            raise RuntimeError("codex timed out after 300s; process tree killed")
        if not (txt or "").strip():
            raise RuntimeError("empty codex stdout: " + (err or "")[:120])
        return txt, 0, model
    raise ValueError("unknown kind " + kind)


def one(kind, model, task, neutral, arm, i, import_instruction=False):
    wd = Path(tempfile.mkdtemp(prefix="bwaudit_"))
    rec = {"arm": arm, "i": i}
    ctx = mb.ARMS[arm]
    prompt = ((ctx + "\n\n") if ctx else "") + task["prompt"]
    if import_instruction:
        prompt += IMPORT_CLAUSE
    prompt += SUFFIX[kind]
    last = None
    try:
        for attempt in range(3):
            try:
                raw, toks, served = complete(kind, model, prompt, wd)
                code = mb._extract_code(raw)
                (wd / "solution.py").write_text(code, encoding="utf-8")

                def run_verify(snippet):
                    (wd / "_v.py").write_text(
                        "import sys;sys.path.insert(0,'.')\n" + snippet + "\nprint('ok')",
                        encoding="utf-8")
                    v = subprocess.run([sys.executable, str(wd / "_v.py")], cwd=str(wd),
                                       capture_output=True, text=True, timeout=30)
                    return v.returncode == 0, (v.stderr or "")[-400:]

                rec["pass_original"], rec["stderr_original"] = run_verify(task["verify"])
                rec["pass_neutral"], rec["stderr_neutral"] = run_verify(neutral)
                rec["has_import"] = bool(re.search(r"^\s*(import ledger|from ledger import)",
                                                   code, re.M))
                rec["encoded_amount"] = bool(re.search(r"#\{|f\"\{sign\}|check\s*=|% 10", code))
                rec["fenced"] = "```" in raw
                rec["starts_with_prose"] = not raw.lstrip().startswith(
                    ("import", "from", "def", "#", '"""', "'''"))
                rec["code_empty"] = not code.strip()
                rec["call_present"] = ("ledger.post" in code) or ("post(" in code)
                rec["out_tokens"] = toks
                rec["model_requested"] = model
                rec["model_served"] = served
                rec["raw"] = raw
                rec["code"] = code
                return rec
            except Exception as e:                                   # transient: retry
                last = e
                import time
                time.sleep(4 * (attempt + 1) ** 2)
        rec["error"] = "%s: %s" % (type(last).__name__, str(last)[:120])
        rec["pass_original"] = rec["pass_neutral"] = False
        return rec
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=["cli", "azure", "codex"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", default=None, help="file-safe name for outputs")
    ap.add_argument("--task", required=True)
    ap.add_argument("--arms", default="W1,W1plus")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--import-instruction", action="store_true",
                    help="require an absolute `import ledger` in every condition")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    label = a.label or re.sub(r"[^A-Za-z0-9._-]", "_", a.model)
    task = next(t for t in mb.TASKS if t["id"] == a.task)
    neutral = build_neutral(task)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    summary = {}
    for arm in a.arms.split(","):
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            rows = list(ex.map(
                lambda i: one(a.kind, a.model, task, neutral, arm, i, a.import_instruction),
                range(a.n)))
        n = len(rows)
        ko = sum(bool(r.get("pass_original")) for r in rows)
        kn = sum(bool(r.get("pass_neutral")) for r in rows)
        errs = sum(1 for r in rows if r.get("error"))
        fails = [r for r in rows if not r.get("pass_original") and not r.get("error")]
        summary[arm] = {
            "n": n, "pass_original": ko, "pass_neutral": kn, "errs": errs,
            "fail_missing_import_only": sum(1 for r in fails
                                            if not r.get("has_import")
                                            and not r.get("encoded_amount")),
            "fail_encoded_amount": sum(1 for r in fails if r.get("encoded_amount")),
            "fail_code_empty": sum(1 for r in fails if r.get("code_empty")),
            "fail_prose_first": sum(1 for r in fails if r.get("starts_with_prose")),
            "fenced_pass": sum(1 for r in rows if r.get("pass_original") and r.get("fenced")),
            "fenced_fail": sum(1 for r in fails if r.get("fenced")),
        }
        print("  %-8s %-14s orig %2d/%d  neutral %2d/%d  errs %d  | fails: import-only %d, "
              "encoded %d, empty-extract %d, prose-first %d"
              % (label, arm, ko, n, kn, n, errs,
                 summary[arm]["fail_missing_import_only"], summary[arm]["fail_encoded_amount"],
                 summary[arm]["fail_code_empty"], summary[arm]["fail_prose_first"]), flush=True)
        json.dump(rows, open(out / ("audit_%s_%s_%s.json" % (label, a.task, arm)), "w",
                             encoding="utf-8"), indent=1)

    json.dump({"model": a.model, "label": label, "task": a.task, "kind": a.kind,
               "n": a.n, "arms": summary},
              open(out / ("audit_%s_%s_summary.json" % (label, a.task)), "w",
                   encoding="utf-8"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
