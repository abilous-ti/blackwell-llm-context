#!/usr/bin/env python3
"""BLACKWELL.md S6 empirical anchor: make Theorem C2 (incomparability) NON-VACUOUS on a
real LLM, with measured HTTP-API PASS rates and a CORRECT uniform certificate.

This is the ESTIMATOR + CERTIFICATE component. It extends tokenbench/measure_moat.py:
same verify_in / fresh-temp-dir / flattened-prompt
mechanics, stdlib only, cross-OS, utf-8 pinned.

It measures, for two fixed Blackwell-INCOMPARABLE context sources W1, W2 and a task set D:

  (A) INCOMPARABILITY  : delta_D(W1,W2) > 0 AND delta_D(W2,W1) > 0 (mutual positive
                          deficiency = neither dominates).
  (B) SCALAR MIS-RANK  : an aggregate scalar phi (mean PASS lift over D) ranks W1 > W2
                          GLOBALLY, yet on >=1 single task realized PASS ranks W2 > W1.
  (C) DOMINANCE control: W1plus = W2_text ++ W1_text. Expect delta_D(W1plus,W2) = 0 and
                          delta_D(W2,W1plus) > 0 (one-directional) -> for-all-tasks dominance.

THE ESTIMATOR
  Per-task PASS(W,T) = (1/n) * sum over n runs of 1[verifier passes].  k(W,T) = # passes.
  hat_delta_D(W1,W2) = max(0, sup_{T in D} [ PASS(W2,T) - PASS(W1,T) ]).
  Empirical incomparability test: hat_delta_D(W1,W2) > tau AND hat_delta_D(W2,W1) > tau.

THE CERTIFICATE (the part the synthesis flagged must be fixed)
  hat_delta_D involves a SUP over the |D| tasks. A pointwise DKW/Hoeffding bound on ONE
  task's PASS is NOT a valid certificate for the sup: selecting the max-gap task inflates
  the error by the multiplicity (Type-I error grows with |D|; see derivation in __doc__ of
  certify_incomparable). The correct tool is a UNIFORM bound: per-task Clopper-Pearson CIs
  at a Bonferroni-corrected level alpha_pair = eta / (2|D|) so all 2|D| per-task proportion
  intervals hold simultaneously at joint level >= 1 - eta. We then certify the sup from the
  simultaneously-valid per-task gap intervals.

Run (auth claude):  python tokenbench/measure_blackwell.py --runs 5
       pipeline:     python tokenbench/measure_blackwell.py --mock
"""
from __future__ import annotations
import argparse, json, math, os, shutil, statistics, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ============================================================================================
# FIXED context sources (do NOT redesign; from BLACKWELL.md S6 spec).
# ============================================================================================
W1 = ("TEAM CONTEXT (private), ledger module API contract: the canonical write call is "
      "`ledger.post(account: str, amount, *, memo: str)` -- note `account` is FIRST, `amount` "
      "is SECOND and positional, and `memo` is a REQUIRED keyword-only argument (calling "
      "without memo= is an error). On success post(...) returns the new integer entry id (>=1). "
      "On any failure (unknown account, malformed amount) it raises `ledger.PostError` (NOT "
      "ValueError, NOT KeyError). This signature is house-private and is not discoverable from "
      "the function name.")

W2 = ("TEAM CONTEXT (private), ledger amount wire-encoding invariant: every monetary amount is "
      "serialized as a STRING of the form `<sign><digits>#<check>` where <sign> is '+' or '-', "
      "<digits> is the amount in MINOR UNITS (integer cents, no decimal point -- $12.30 encodes "
      "its 1230 cents), and <check> is a single Luhn-style digit equal to (sum of the decimal "
      "digits in <digits>) mod 10. Example: -$0.07 -> \"-7#7\"; +$12.30 -> \"+1230#6\". Decoding "
      "rejects any string whose trailing check digit disagrees. This encoding is house-private "
      "and not inferable from the data alone.")

# Dominance positive control: literal superset of W2's signal (encoding ++ contract).
W1plus = W2 + "\n\n" + W1
# Order control (lead C): SAME content as W1plus, W1 FIRST. Note W1plus already puts W1 LAST
# (recency slot) and it still collapsed API PASS -> if W1plus_rev is indistinguishable, the
# anti-monotonicity harm is ORDER-INVARIANT (not lost-in-the-middle), which HARDENS the result.
W1plus_rev = W1 + "\n\n" + W2

# Length-matched PADDING control (2026-07-03): W1pad = FILLER ++ W1 mirrors W1plus's structure
# (added text FIRST, W1 last) with FILLER character-matched to W2 but carrying NO coordinate any
# verifier checks. Du et al. (2510.05381) show added length ALONE can hurt; if W1pad holds W1's
# ceiling on the collapse cells while W1plus craters, the anti-monotonicity harm is attributable
# to W2's signal content, not to token count. Same register as W2 ("TEAM CONTEXT (private)") so
# the only axes left differing vs W1plus are (a) signal content and (b) ledger-topicality.
# Routing-instruction ablation (2026-07-03, reviewer request): does a one-line routing note
# cure the superset collapse? NOTE the instruction itself presupposes knowing WHICH source is
# decisive for WHICH task family -- i.e. exactly the coordinate structure the partial order
# formalizes. Either outcome is informative: cure => the fix requires the diagnosis (selection-
# time knowledge of decisiveness), no cure => the collapse is robust to cheap prompting.
W1plus_instr = (W1plus + "\n\nROUTING NOTE: the two team conventions above serve different task "
                "families. For tasks that CALL the ledger API (posting, transferring, logging), "
                "use only the API call contract; the wire-encoding invariant applies only to "
                "tasks that encode or decode amount strings. Do not mix them.")

# Structured-context ablation (2026-07-04, reviewer mechanism-probe request): same two
# conventions, same order as W1plus (W2 first, W1 last), but wrapped in labeled XML sections.
# Tests whether STRUCTURE + section labels alone (no task-family routing statement) prevent the
# convention interference. Discriminates "model cannot segment the two conventions" from
# "model cannot route them to task families" (the latter is what W1plus_instr supplies).
W1plus_xml = ("<team_context>\n<wire_encoding_invariant>\n" + W2 +
              "\n</wire_encoding_invariant>\n<api_call_contract>\n" + W1 +
              "\n</api_call_contract>\n</team_context>")

W1PAD_FILLER = (
    "TEAM CONTEXT (private), office logistics note: the quarterly all-hands is held in the "
    "Maple room on the second Tuesday of the quarter at 10:00 local time; bring your own "
    "laptop, coffee is available from 09:30. Desk booking opens fourteen days ahead in the "
    "facilities portal and unclaimed desks are released again at 09:15 each morning. Guest "
    "badges must be requested from reception one business day in advance and must be returned "
    "before 18:00 on the same day. The bicycle cage code rotates monthly. Parcel lockers in "
    "the lobby are cleared by facilities every Friday afternoon.")
W1pad = W1PAD_FILLER + "\n\n" + W1

# ============================================================================================
# TASK SET D : 4 API-usage tasks (need W1) + 2 encode/decode tasks (need W2).
# W1's family is deliberately larger -> aggregate scalar phi ranks W1 > W2 globally (part B).
# Each verifier is a self-contained python snippet (returncode 0 = PASS) that stubs a fake
# `ledger` module enforcing ONLY the exact private contract.
# ============================================================================================
_LEDGER_STUB = (
    "import types,sys\n"
    "led=types.ModuleType('ledger')\n"
    "class PostError(Exception):pass\n"
    "led.PostError=PostError\n"
    "_ACCTS={'cash','ar','ap'}\n"
    "_CALLS=[]\n"
    "def post(account,amount,*,memo):\n"  # exact contract: account 1st, amount 2nd pos, memo kw-only required
    "    if not isinstance(account,str) or account not in _ACCTS: raise PostError('bad acct')\n"
    # amount may be int (cents) OR an already-wire-encoded string (trap task); the decisive W1
    # facts are arg-order / memo-kw / return-id, NOT amount type, so accepting str keeps the
    # trap W1-decisive while making it passable.
    "    if amount is None or not isinstance(amount,(int,str)): raise PostError('bad amount')\n"
    "    _CALLS.append((account,amount,memo)); return len(_CALLS)\n"
    "led.post=post; led._CALLS=_CALLS\n"
    "sys.modules['ledger']=led\n"
)

TASKS = [
    # ---- API-usage family (decisive fact = W1) ----
    {"id": "api_post_ok", "fam": "api",
     "prompt": "In a module `ledger` there is a write function `post`. Write "
               "record(acct, cents, note) in solution.py that posts `cents` to account "
               "`acct` with memo `note` using ledger.post, and RETURNS the new entry id. "
               "solution.py only.",
     "verify": _LEDGER_STUB +
               "from solution import record\n"
               "eid=record('cash',500,'lunch')\n"
               "assert isinstance(eid,int) and eid>=1, ('bad id',eid)\n"
               "assert led._CALLS[-1]==('cash',500,'lunch'), ('wrong call',led._CALLS)\n"},
    # HARDENED (2026-06-20): memo now comes from a PARAMETER (reason), mirroring api_post_ok, so a
    # model lacking W1 writes post(acct,cents,reason) positionally -> TypeError (memo is kw-only) ->
    # fail. This leans on the genuinely-unguessable kw-only-memo fact and drops the `none` baseline
    # toward 0 (the prior literal-memo version leaked ~40% because models guess memo='auto').
    {"id": "api_argorder", "fam": "api",
     "prompt": "Using module `ledger`'s write function `post`, write "
               "transfer(acct, cents, reason) in solution.py that posts `cents` to account "
               "`acct` using `reason` as the memo, and returns the entry id. solution.py only.",
     "verify": _LEDGER_STUB +
               "from solution import transfer\n"
               "eid=transfer('ar',1230,'rebalance')\n"
               "assert isinstance(eid,int) and eid>=1\n"
               "assert led._CALLS[-1]==('ar',1230,'rebalance'), ('wrong call/argorder',led._CALLS)\n"},
    {"id": "api_error_type", "fam": "api",
     "prompt": "Module `ledger` exposes a write function `post` that raises on a bad account. "
               "Write safe_post(acct, cents) in solution.py that calls ledger.post (memo='x') "
               "and returns the entry id on success, or returns the STRING 'failed' if posting "
               "raises ledger's own post-error type. Do not catch unrelated exceptions. "
               "solution.py only.",
     "verify": _LEDGER_STUB +
               "from solution import safe_post\n"
               "assert safe_post('cash',1)>=1\n"
               "assert safe_post('NOPE',1)=='failed', 'must catch ledger.PostError specifically'\n"},
    {"id": "api_memo_required", "fam": "api",
     "prompt": "Module `ledger`'s write function `post` is strict about how the memo is passed. "
               "Write log_fee(acct) in solution.py that posts 25 to `acct` with memo 'fee' and "
               "returns the entry id. solution.py only.",
     "verify": _LEDGER_STUB +
               "from solution import log_fee\n"
               "eid=log_fee('ap')\n"
               "assert isinstance(eid,int) and eid>=1\n"
               "assert led._CALLS[-1]==('ap',25,'fee'), ('memo not kw or wrong',led._CALLS)\n"},
    # ---- encode/decode family (decisive fact = W2) ----
    {"id": "enc_amount", "fam": "enc",
     "prompt": "Write encode_amount(dollars: str) -> str in solution.py that serializes a "
               "money amount (e.g. '12.30', '-0.07') to this team's private wire format. "
               "solution.py only.",
     "verify":
               "from solution import encode_amount as f\n"
               "assert f('12.30')=='+1230#6', ('12.30',f('12.30'))\n"
               "assert f('-0.07')=='-7#7', ('-0.07',f('-0.07'))\n"
               "assert f('0.00')=='+0#0', ('0.00',f('0.00'))\n"},
    {"id": "dec_amount", "fam": "enc",
     "prompt": "Write decode_amount(wire: str) -> str in solution.py that decodes this team's "
               "private money wire format back to a decimal-dollar string (2 dp), and raises "
               "ValueError if the wire string's trailing check digit is wrong. solution.py only.",
     "verify":
               "from solution import decode_amount as f\n"
               "assert f('+1230#6')=='12.30', f('+1230#6')\n"
               "assert f('-7#7')=='-0.07', f('-7#7')\n"
               "import builtins\n"
               "try:\n"
               "    f('+1230#5'); raise AssertionError('bad check digit not rejected')\n"
               "except ValueError: pass\n"},
    # ---- RELEVANCE-TRAP task (fam='trap'): lexically saturated with ENCODING vocabulary
    #      (so a query-conditioned relevance score scores W2 >> W1 for THIS task), yet the
    #      graded requirement is purely the W1 post() CONTRACT (the amount arrives already
    #      encoded and is passed through verbatim). Expect phi_lex(W2,T) > phi_lex(W1,T) but
    #      PASS(W1,T) > PASS(W2,T): defeats query-CONDITIONED relevance, the strong form of
    #      Thm 3 that kills the "just use relevance-of-W-to-T" confound.
    {"id": "trap_store_wire", "fam": "trap",
     "prompt": "Our monetary amounts arrive ALREADY wire-encoded as strings like '+1230#6' "
               "(sign, minor-unit cents digits, '#', check digit). The amount is ALREADY "
               "serialized -- do NOT re-encode or decode it. Write store(acct, wire) in "
               "solution.py that posts the wire-encoded amount string `wire` to account `acct` "
               "(memo 'wire') using the ledger module's write function and returns the new "
               "entry id. solution.py only.",
     "verify": _LEDGER_STUB +
               "from solution import store\n"
               "eid=store('cash','+1230#6')\n"
               "assert isinstance(eid,int) and eid>=1\n"
               "assert led._CALLS[-1]==('cash','+1230#6','wire'), ('needs W1 post contract',led._CALLS)\n"},
]

# Map an arm label -> the context text prepended to the prompt (None = no context).
ARMS = {"none": None, "W1": W1, "W2": W2, "W1plus": W1plus, "W1plus_rev": W1plus_rev,
        "W1pad": W1pad, "W1plus_instr": W1plus_instr, "W1plus_xml": W1plus_xml}


# ============================================================================================
# Harness mechanics (carried over from measure_moat.py).
# ============================================================================================
def _azure_complete(prompt, model):
    """Single-shot completion via an Azure OpenAI-style endpoint (stdlib urllib only; NO third-
    party deps). Reads AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_KEY from env -- the key is NEVER
    stored in this file. Auto-detects the API style from the endpoint URL:
      * '.../responses...'  -> Responses API   (input / output[]),     auth: api-key header
      * '.../v1/' or chat   -> Chat Completions (messages / choices[]), auth: Bearer + api-key
    Returns (assistant_text, output_tokens). Used for non-Anthropic, cross-vendor models. NB:
    single-shot completion, not an agentic loop -- a cleaner context-use probe."""
    import urllib.request
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    key = os.environ["AZURE_OPENAI_KEY"]
    if "anthropic" in endpoint:   # Anthropic Messages API (also served by Azure AI Foundry)
        url = endpoint
        headers = {"Content-Type": "application/json", "x-api-key": key, "api-key": key,
                   "anthropic-version": "2023-06-01"}
        body = {"model": model, "max_tokens": 8000,
                "messages": [{"role": "user", "content": prompt}]}
    elif "responses" in endpoint:
        url, headers = endpoint, {"Content-Type": "application/json", "api-key": key}
        body = {"model": model, "input": prompt, "max_output_tokens": 8000}
    else:  # OpenAI-compatible chat completions (e.g. Azure AI Foundry /openai/v1/)
        # Accept either a base URL or a full endpoint. Appending unconditionally turned a
        # full .../chat/completions into .../chat/completions/chat/completions, and the
        # resulting 404 was then scored as a failed draw.
        _e = endpoint.rstrip("/")
        url = _e if _e.endswith("/chat/completions") else _e + "/chat/completions"
        headers = {"Content-Type": "application/json",
                   "Authorization": "Bearer " + key, "api-key": key}
        body = {"model": model, "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 8000}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers=headers)
    out = None
    for attempt in range(3):                           # retry transient 429/500/timeout
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                out = json.loads(resp.read().decode("utf-8"))
            break
        except Exception:
            if attempt == 2:
                raise
            import time
            time.sleep(2 * (attempt + 1))
    if isinstance(out.get("content"), list):           # Anthropic Messages API
        text = "".join(c.get("text", "") for c in out["content"] if c.get("type") == "text")
        otoks = (out.get("usage", {}) or {}).get("output_tokens", 0)
    elif "output" in out:                              # Responses API
        text = ""
        for item in out.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") in ("output_text", "text"):
                        text += c.get("text", "")
        text = text or out.get("output_text", "") or ""
        otoks = (out.get("usage", {}) or {}).get("output_tokens", 0)
    else:                                              # Chat Completions
        msg = ((out.get("choices") or [{}])[0].get("message") or {})
        text = msg.get("content") or ""
        otoks = (out.get("usage", {}) or {}).get("completion_tokens", 0)
    return text, otoks


def _extract_code(text):
    """Pull raw Python from a model reply: strip a ```python ... ``` fence if present, else as-is."""
    import re
    m = re.search(r"```(?:python|py)?\s*(.*?)```", text, re.DOTALL)
    return (m.group(1) if m else text).strip() + "\n"


# The verifier prints this only after its last assertion has run. Grading on the return code
# alone let generated code raising SystemExit(0) pass before reaching a failing assertion.
VERIFY_SENTINEL = "__verify_ok__"


def _child_env():
    """A minimal environment for running model-generated code.

    The verifier imports untrusted generated Python. Handing it the parent environment gave it
    the provider credentials this harness authenticates with; nothing in a solution needs them.
    """
    keep = ("PATH", "PATHEXT", "SYSTEMROOT", "COMSPEC", "TEMP", "TMP", "HOME", "LANG")
    env = {k: v for k, v in os.environ.items() if k in keep}
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def verify_in(wd: Path, snippet: str) -> bool:
    (wd / "_v.py").write_text("import sys;sys.path.insert(0,'.')\n" + snippet +
                              "\nprint('" + VERIFY_SENTINEL + "')", encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, str(wd / "_v.py")], cwd=str(wd),
                           capture_output=True, timeout=30, env=_child_env())
        if r.returncode != 0:
            return False
        # PASS requires the sentinel: the process must have reached the end of the checks.
        return VERIFY_SENTINEL in (r.stdout or b"").decode("utf-8", "replace")
    except Exception:
        return False


def run_one(task, arm, mock, i, model="claude-haiku-4-5-20251001",
             http=True, retain=None):
    """One HTTP draw for (task, arm): one request, one turn, no tools, for every model.
    Returns {'solved': bool, 'cost': float, 'out_tokens': int}. `http` is accepted and ignored;
    it remains only so callers written against the older signature keep working."""
    if mock:
        # Planted ground truth matching the mechanism: api tasks need W1; enc tasks need W2.
        # W1plus contains both -> solves both families. 'none' fails idiosyncratic tasks.
        fam = task["fam"]
        # W1plus contains W2's signal (encoding) PLUS W1's (contract): by the superset/garbling
        # argument it must be >= W2 on EVERY task family -> plant it >= W2 everywhere.
        base = {("api", "W1"): .92, ("api", "W2"): .07, ("api", "none"): .07,
                ("api", "W1plus"): .90,
                ("enc", "W2"): .90, ("enc", "W1"): .05, ("enc", "none"): .05,
                ("enc", "W1plus"): .92,
                # trap task is W1-decisive (needs the post contract), even though it READS
                # like an encoding task -> W2 does not help despite high lexical relevance.
                ("trap", "W1"): .90, ("trap", "W2"): .07, ("trap", "none"): .07,
                ("trap", "W1plus"): .90,
                # padding control: plant the no-length-harm hypothesis (W1pad == W1) so the
                # mock exercises the plumbing; the real run decides the science.
                ("api", "W1pad"): .92, ("enc", "W1pad"): .05, ("trap", "W1pad"): .90,
                ("api", "W1plus_instr"): .90, ("enc", "W1plus_instr"): .90,
                ("trap", "W1plus_instr"): .90,
                ("api", "W1plus_xml"): .90, ("enc", "W1plus_xml"): .90,
                ("trap", "W1plus_xml"): .90}
        # mock cannot model order effects: plant W1plus_rev == W1plus (plumbing test only).
        b = base.get((fam, arm if arm != "W1plus_rev" else "W1plus"))
        import random
        random.seed(hash((task["id"], arm, i)) % 99991)
        # plant a token count so the runtime-harm signal (lead D) has a mock path too.
        toks = 300 + (120 if arm in ("W1plus", "W1plus_rev") else 0) + i
        return {"solved": random.random() < b, "cost": 0.02 + 0.001 * i, "out_tokens": toks}
    wd = Path(tempfile.mkdtemp(prefix="bw_"))
    try:
        ctx = ARMS[arm]
        prompt = ((ctx + "\n\n") if ctx else "") + task["prompt"]
        if True:
            # One HTTP request, one turn, no tools. This is the only measurement path.
            text, toks = _azure_complete(
                " ".join((prompt + " Return ONLY the raw Python file content, no markdown "
                          "fences, no prose.").split()), model)
            if retain:
                import pathlib
                d = pathlib.Path(retain)
                d.mkdir(parents=True, exist_ok=True)
                (d / ("%s__%s__%s__%03d.txt" % (model, task["id"], arm, i))).write_text(
                    text or "", encoding="utf-8")
            (wd / "solution.py").write_text(_extract_code(text), encoding="utf-8")
            return {"solved": verify_in(wd, task["verify"]), "cost": 0.0, "out_tokens": toks}
    except Exception as e:
        return {"solved": False, "cost": 0.0, "out_tokens": 0, "error": str(e)[:80]}
    finally:
        shutil.rmtree(wd, ignore_errors=True)


# ============================================================================================
# (1) ESTIMATOR
# ============================================================================================
def pass_rate(counts):
    """counts = (k, n) ; returns k/n."""
    k, n = counts
    return k / n if n else 0.0


def hat_delta_D(counts_W1, counts_W2, by_task):
    """Empirical deficiency hat_delta_D(W1,W2) = max(0, sup_T [PASS(W2,T)-PASS(W1,T)]).

    counts_W1[tid] = (k1,n), counts_W2[tid] = (k2,n) for each task id in by_task.
    Returns (value, argsup_task_id, per_task_gaps dict tid->(p2-p1)).
    """
    gaps = {}
    for tid in by_task:
        p1 = pass_rate(counts_W1[tid])
        p2 = pass_rate(counts_W2[tid])
        gaps[tid] = p2 - p1
    arg = max(by_task, key=lambda t: gaps[t])
    return max(0.0, gaps[arg]), arg, gaps


# ============================================================================================
# (2) EMPIRICAL INCOMPARABILITY TEST (both directions positive past a threshold tau)
# ============================================================================================
def incomparability_test(counts_A, counts_B, by_task, tau=0.0):
    """Returns (is_incomparable, dAB, dBA). is_incomparable iff both hat_deltas > tau."""
    dAB, *_ = hat_delta_D(counts_A, counts_B, by_task)  # delta_D(A,B): does B beat A somewhere
    dBA, *_ = hat_delta_D(counts_B, counts_A, by_task)  # delta_D(B,A): does A beat B somewhere
    return (dAB > tau and dBA > tau), dAB, dBA


# ============================================================================================
# (3) THE UNIFORM CERTIFICATE  -- exact Clopper-Pearson + Bonferroni over the sup.
# ============================================================================================
# ---- regularized incomplete beta (stdlib only) -> exact binomial tail / CP interval ----
def _betacf(a, b, x):
    TINY = 1e-30
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < TINY: d = TINY
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < TINY: d = TINY
        c = 1.0 + aa / c
        if abs(c) < TINY: c = TINY
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < TINY: d = TINY
        c = 1.0 + aa / c
        if abs(c) < TINY: c = TINY
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-13:
            break
    return h


def _betai(a, b, x):
    if x <= 0.0: return 0.0
    if x >= 1.0: return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def _beta_ppf(p, a, b):
    if p <= 0.0: return 0.0
    if p >= 1.0: return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if _betai(a, b, mid) < p: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)


def clopper_pearson(k, n, alpha):
    """Exact two-sided 1-alpha CI for a Binomial(n,p) success probability. Returns (lo,hi)."""
    if n == 0: return (0.0, 1.0)
    a = alpha / 2.0
    lo = 0.0 if k == 0 else _beta_ppf(a, k, n - k + 1)
    hi = 1.0 if k == n else _beta_ppf(1.0 - a, k + 1, n - k)
    return (lo, hi)


def certify_incomparable(counts_A, counts_B, by_task, eta=0.10):
    """CORRECT uniform certificate that hat_delta_D(A,B)>0 AND hat_delta_D(B,A)>0
    (empirical Blackwell-incomparability), valid at joint confidence >= 1 - eta.

    WHY NAIVE POINTWISE DKW/HOEFFDING IS WRONG
    ------------------------------------------
    hat_delta_D(A,B) = max(0, sup_{T in D}[p_B(T)-p_A(T)]). To CERTIFY this sup is > 0 we must
    exhibit a task whose true gap p_B(T)-p_A(T) > 0 with confidence. The estimator SELECTS the
    empirically largest-gap task (an argmax over |D| tasks). Putting a single 1-eta CI on that
    selected task ignores the selection: under the null (all true gaps = 0) the max of |D| noisy
    gap estimates exceeds any fixed pointwise threshold far more than eta of the time. Monte-Carlo
    (validated during construction): naive single-task false-positive rate climbs 0.02 (|D|=5) ->
    0.08 (20) -> 0.24 (50) -> 0.36 (100), blowing past eta=0.10. DKW bounds the sup deviation of
    ONE empirical CDF from ITS OWN cdf over a single i.i.d. sample; it does not control a max of
    DIFFERENCES of two binomial means across DISTINCT tasks each estimated from its own n-sample.
    The multiplicity is real and must be paid.

    THE FIX (uniform / Bonferroni over the finite task sample)
    ---------------------------------------------------------
    There are 2*|D| per-task proportions (p_A(T), p_B(T) for each T). Give each an exact
    Clopper-Pearson interval at level alpha_pair = eta / (2|D|). By the union bound, ALL 2|D|
    intervals hold SIMULTANEOUSLY with probability >= 1 - 2|D|*alpha_pair = 1 - eta. On that
    joint event, for every task T a simultaneously-valid lower bound on the gap is
        L_T = CPlo(p_B(T)) - CPhi(p_A(T)).
    Then  L_D(A,B) := max_T L_T  is a 1-eta lower confidence bound on sup_T[p_B-p_A], hence on
    hat_delta_D(A,B) (whose population value is max(0,sup gap)). If L_D(A,B) > 0 we have
    CERTIFIED hat_delta_D(A,B) > 0 at confidence >= 1-eta. Symmetrically L_D(B,A). Because both
    directions read off the SAME simultaneously-valid family of 2|D| intervals (CP on every
    p_A,p_B), the two one-sided claims jointly hold at >= 1 - eta (no extra correction needed:
    the 2|D| intervals already cover everything used).

    Returns dict with L_AB, L_BA, alpha_pair, certified (bool: both L>0), per-task detail.
    """
    D = len(by_task)
    alpha_pair = eta / (2 * D)  # 2|D| proportions, union bound to joint level 1-eta
    detail = {}
    L_AB_terms, L_BA_terms = [], []
    for tid in by_task:
        kA, nA = counts_A[tid]
        kB, nB = counts_B[tid]
        Alo, Ahi = clopper_pearson(kA, nA, alpha_pair)
        Blo, Bhi = clopper_pearson(kB, nB, alpha_pair)
        L_AB_terms.append(Blo - Ahi)   # lower bound on p_B - p_A
        L_BA_terms.append(Alo - Bhi)   # lower bound on p_A - p_B
        detail[tid] = {"A_ci": (round(Alo, 3), round(Ahi, 3)),
                       "B_ci": (round(Blo, 3), round(Bhi, 3)),
                       "L_AB": round(Blo - Ahi, 3), "L_BA": round(Alo - Bhi, 3)}
    L_AB = max(L_AB_terms)
    L_BA = max(L_BA_terms)
    return {"L_AB": L_AB, "L_BA": L_BA, "alpha_pair": alpha_pair, "eta": eta,
            "certified_incomparable": (L_AB > 0 and L_BA > 0), "detail": detail}


def certify_dominance(counts_dom, counts_sub, by_task, eta=0.10):
    """Certify hat_delta_D(W_dom, W_sub) = 0 (W_dom dominates: no task where W_sub beats W_dom),
    at confidence >= 1 - eta. This certifies the UPPER side of the sup is <= 0.

    Uniform: alpha_pair = eta / |D| (only |D| one-sided gap-upper bounds are used here).
    For each task an upper bound on p_sub - p_dom is U_T = CPhi(p_sub) - CPlo(p_dom). The
    certified upper bound on the sup is U_D = max(0, max_T U_T). If U_D <= alpha_tol we declare
    empirical dominance (delta_D(dom,sub) <= alpha_tol at confidence 1-eta).

    Note: certifying a sup is EXACTLY 0 is impossible with finite n (any task could have a tiny
    true gap below noise); we certify it is <= alpha_tol. Report U_D and let alpha_tol be the
    practical equivalence margin.
    """
    D = len(by_task)
    alpha_pair = eta / D
    U_terms = []
    detail = {}
    for tid in by_task:
        kd, nd = counts_dom[tid]
        ks, ns = counts_sub[tid]
        dlo, dhi = clopper_pearson(kd, nd, alpha_pair)
        slo, shi = clopper_pearson(ks, ns, alpha_pair)
        U = shi - dlo  # upper bound on p_sub - p_dom
        U_terms.append(U)
        detail[tid] = {"dom_ci": (round(dlo, 3), round(dhi, 3)),
                       "sub_ci": (round(slo, 3), round(shi, 3)), "U": round(U, 3)}
    U_D = max(0.0, max(U_terms))
    return {"U_D": U_D, "alpha_pair": alpha_pair, "eta": eta, "detail": detail}


def required_n(target_halfwidth=0.15, eta=0.10, D=6):
    """Smallest n s.t. a single-proportion exact CP interval at alpha_pair = eta/(2D) has
    half-width <= target_halfwidth at the worst case p=0.5. Gives the n needed for a useful
    (separated-from-0) certificate. Returns n."""
    alpha_pair = eta / (2 * D)
    for n in range(2, 5000):
        k = n // 2  # p_hat ~ 0.5, worst case for CP width
        lo, hi = clopper_pearson(k, n, alpha_pair)
        if (hi - lo) / 2.0 <= target_halfwidth:
            return n
    return -1


def required_n_stark(eta=0.10, D=6):
    """Smallest n that CERTIFIES a STARK crossover (clean 0/n for the loser, n/n for the winner)
    at joint level 1-eta: needs CPlo(n,n) > CPhi(0,n) at alpha_pair=eta/2|D|. Far smaller than
    the p=0.5 worst case -- this is the n you actually need IF Haiku gives a clean ~0% vs ~100%
    split, which the design predicts. Returns n (or -1)."""
    alpha_pair = eta / (2 * D)
    for n in range(2, 5000):
        lo_win, _ = clopper_pearson(n, n, alpha_pair)   # winner k=n
        _, hi_lose = clopper_pearson(0, n, alpha_pair)  # loser  k=0
        if lo_win - hi_lose > 0:
            return n
    return -1


# ============================================================================================
# (4) INTERFERENCE CERTIFICATE (lead A) -- certify a HARMFUL non-monotone interaction:
#     I_T = PASS(W1plus) - PASS(W1) - PASS(W2) + PASS(none).
# I_T < 0 means the superset W1plus returns less than the sum of its parts predicts. NOTE: this
# is NOT evidence of harm and NOT something a monotone submodular set function rules out --
# I_T <= 0 is exactly the submodularity inequality for {W1,W2}. An earlier version of this
# comment claimed the opposite. Harm is the two-arm contrast Delta_T computed by certify_harm;
# I_T is retained as a descriptive interaction term only.
# To bound I_T <= -tau we need an UPPER confidence bound on I_T. The upper bound
# uses CPhi for the + terms (W1plus, none) and CPlo for the - terms (W1, W2), all at a Bonferroni
# level alpha=eta/4 (4 proportions/task) so the per-task claim holds at >= 1-eta.
# ============================================================================================
def certify_harm(counts, by_task, eta=0.10, tau=0.30, selected_post_hoc=False):
    """Verify DIRECT augmentation harm Delta_T = PASS(W1plus,T) - PASS(W1,T) <= -tau.

    This is the quantity the paper verifies. The four-term interaction Psi_T computed
    by certify_interference is NOT harm: Psi_T <= 0 is exactly the submodularity
    inequality for {W1,W2}, and is satisfied by monotone functions with no degradation
    (none=0, W1=W2=W1plus=1 gives Psi=-1 and zero harm). Psi is reported descriptively.

    Confidence budget. Only two endpoints enter the bound: the UPPER endpoint of the
    superset arm and the LOWER endpoint of the W1 arm. Each must therefore carry
    noncoverage at most eta/2, so that the union bound over the two delivers eta. A
    two-sided Clopper-Pearson call at level `eta` puts eta/2 in each tail, which is
    exactly that; calling it at eta/2 (as an earlier version did) spends eta/4 per tail,
    delivers 1-eta/2 rather than 1-eta, and widens the bound for nothing.
    """
    # clopper_pearson takes a TWO-SIDED level and puts half of it in each tail, so the
    # two-sided argument must be twice the noncoverage we want on each endpoint. Marginal
    # case: eta/2 per endpoint -> pass eta. Post-hoc selection from |D| candidate cells:
    # eta/(2|D|) per endpoint over the 2|D| endpoints -> pass eta/|D|. Passing eta/(2|D|)
    # here, as this branch previously did, spends eta/(4|D|) per tail and is twice as
    # conservative as Proposition 4 specifies.
    alpha = eta / float(len(by_task)) if selected_post_hoc else eta
    out, certified = {}, []
    for tid in by_task:
        k1, n1 = counts["W1"][tid]
        kp, np_ = counts["W1plus"][tid]
        delta = pass_rate(counts["W1plus"][tid]) - pass_rate(counts["W1"][tid])
        hi = clopper_pearson(kp, np_, alpha)[1]     # upper on p_{W1plus}
        lo = clopper_pearson(k1, n1, alpha)[0]      # lower on p_{W1}
        d_hi = hi - lo                              # upper confidence bound on Delta_T
        ok = d_hi <= -tau
        if ok:
            certified.append(tid)
        out[tid] = {"delta": round(delta, 4), "delta_hi": round(d_hi, 4),
                    "W1": counts["W1"][tid], "W1plus": counts["W1plus"][tid],
                    "certified_harmful": ok}
    out["certified"] = certified
    out["alpha_two_sided"] = alpha
    out["alpha_per_endpoint"] = alpha / 2.0
    return out


def certify_interference(counts, by_task, eta=0.10, tau=0.30):
    """Per task: point I_T and an upper 1-eta confidence bound; certified harmful iff I_hi<=-tau.
    Requires arms none/W1/W2/W1plus in counts. Returns {tid: {...}} + a 'certified' list."""
    alpha = eta / 4.0
    out, certified = {}, []
    for tid in by_task:
        p = {a: pass_rate(counts[a][tid]) for a in ("none", "W1", "W2", "W1plus")}
        I_T = p["W1plus"] - p["W1"] - p["W2"] + p["none"]
        # upper bound on I_T (worst case it is least-negative):
        hiP = {a: clopper_pearson(*counts[a][tid], alpha) for a in ("none", "W1", "W2", "W1plus")}
        I_hi = hiP["W1plus"][1] - hiP["W1"][0] - hiP["W2"][0] + hiP["none"][1]
        ok = I_hi <= -tau
        if ok:
            certified.append(tid)
        out[tid] = {"I_T": round(I_T, 3), "I_T_upper": round(I_hi, 3), "certified_harm": ok}
    return {"detail": out, "certified_tasks": certified, "alpha": alpha, "tau": tau}


# ============================================================================================
# Driver: measure all arms x tasks, compute estimator + run all three certificates.
# ============================================================================================
def measure(arms, mock, runs, tasks=None, workers=1, model="claude-haiku-4-5-20251001",
            http=True, retain=None):
    """Returns counts[arm][tid]=(k,n), cost[arm][tid]=mean cost, toks[arm][tid]=mean out_tokens,
    draws[arm][tid]=ordered list of 0/1 PASS outcomes (draw i = index i; needed for sequential replay).
    workers>1 runs the n calls of each cell concurrently (calls are subprocess+network bound and
    each uses its own temp dir, so threads are safe and give a near-linear speedup for big n)."""
    from concurrent.futures import ThreadPoolExecutor
    tasks = tasks if tasks is not None else TASKS
    counts = {a: {} for a in arms}
    cost = {a: {} for a in arms}
    toks = {a: {} for a in arms}
    draws = {a: {} for a in arms}   # ordered per-draw PASS sequence, for sequential analysis
    errs = {a: {} for a in arms}    # per-draw transport-error flags (1 = outage-scored, not a real fail)
    for a in arms:
        for t in tasks:
            if workers > 1 and not mock:
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    rows = list(ex.map(lambda i, _t=t, _a=a: run_one(_t, _a, mock, i, model,
                                                             http, retain), range(runs)))
            else:
                rows = [run_one(t, a, mock, i, model, http, retain)
                    for i in range(runs)]
            # A transport failure is not a model answer. Scoring it as PASS=0 meant an arm of
            # outages could certify as a collapse, so errored draws leave the sample entirely and
            # the shortfall is reported; main() then refuses to certify an incomplete cell.
            good = [r for r in rows if not r.get("error")]
            k = sum(1 for r in good if r["solved"])
            counts[a][t["id"]] = (k, len(good))
            draws[a][t["id"]] = [1 if r["solved"] else 0 for r in good]
            errs[a][t["id"]] = [1 if r.get("error") else 0 for r in rows]
            cost[a][t["id"]] = statistics.mean(r["cost"] for r in rows)
            toks[a][t["id"]] = statistics.mean(r.get("out_tokens", 0) for r in rows)
            err = next((r.get("error") for r in rows if r.get("error")), "")
            _n = len(good)
            print(f"  arm={a:<6} {t['id']:<16} PASS {k}/{_n}={(k / _n if _n else 0):.0%}"
                  f"  ${cost[a][t['id']]:.4f}"
                  + (f"  DROPPED {runs - _n} transport failures" if _n != runs else "")
                  + (f"  ERR:{err}" if err else ""))
    return counts, cost, toks, draws, errs


def aggregate_phi(counts_W, counts_none, by_task):
    """OUTCOME-based aggregate scalar (mean PASS lift of W over no-context across D). NOTE:
    this is computed FROM the PASS outcomes, so it is circular and its global order depends on
    the task MIX -- shown only as the weak/contrast case. The real test of Thm 3 is the
    query-CONDITIONED lexical relevance below, a model-free scalar a practitioner uses BEFORE
    running the model."""
    lifts = [pass_rate(counts_W[t]) - pass_rate(counts_none[t]) for t in by_task]
    return statistics.mean(lifts)


def _toks(s):
    import re
    return [w for w in re.split(r"[^a-z0-9]+", s.lower()) if w]


def lexical_relevance(ctx_text, prompt):
    """A REAL, model-free, query-CONDITIONED relevance scalar phi(W,T): bag-of-words cosine
    between a context source and the task prompt -- the kind of score retrieval/RAG actually
    uses to rank candidate context for a query, computed BEFORE running the model. Stdlib only.
    Defeating THIS (relevance ranks one source higher, realized PASS ranks the other higher) is
    the strong form of Thm 3 that the 'just use relevance-of-W-to-T' confound cannot escape."""
    from collections import Counter
    a, b = Counter(_toks(ctx_text)), Counter(_toks(prompt))
    if not a or not b:
        return 0.0
    dot = sum(a[w] * b[w] for w in a if w in b)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5, help="draws per (arm,task) = n")
    ap.add_argument("--eta", type=float, default=0.10, help="certificate failure budget")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--tasks", default="", help="comma list of task ids to measure (default all)")
    ap.add_argument("--arms", default="", help="comma list of arms to measure (default all 4)")
    ap.add_argument("--out", default="blackwell_results.json", help="results filename")
    ap.add_argument("--workers", type=int, default=1, help="concurrent requests per cell")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001", help="model id to query")
    ap.add_argument("--http", action="store_true", default=True,
                    help="accepted and ignored: every draw is one HTTP request, for every model")
    ap.add_argument("--retain", default="", help="directory to write every raw completion to")
    ap.add_argument("--allow-incomplete", action="store_true",
                    help="certify even if transport failures thinned a cell below --runs")

    a = ap.parse_args()
    # INTEGRITY GUARD: never let a --mock run clobber the REAL results file. (A smoke-test mock
    # run silently overwrote blackwell_results.json once, leaving the real anomaly only in the
    # .log -- this prevents a recurrence.)
    if a.mock and a.out == "blackwell_results.json":
        a.out = "blackwell_results_mock.json"
    all_ids = [t["id"] for t in TASKS]
    sel_ids = [x for x in a.tasks.split(",") if x] or all_ids
    bad = [x for x in sel_ids if x not in all_ids]
    if bad:
        ap.error(f"unknown task id(s): {bad}; valid: {all_ids}")
    sel_tasks = [t for t in TASKS if t["id"] in sel_ids]
    by_task = [t["id"] for t in sel_tasks]
    arms = [x for x in a.arms.split(",") if x] or ["none", "W1", "W2", "W1plus"]
    if not {"none", "W1", "W2"} <= set(arms):
        ap.error(f"--arms must include none,W1,W2 (the core A/B analysis); got {arms}")
    total_n_runs = len(arms) * len(sel_tasks) * a.runs
    print(f"BLACKWELL S6 anchor {'MOCK' if a.mock else 'REAL'} | n={a.runs}/cell | "
          f"arms={arms} tasks={by_task} | {total_n_runs} draws | eta={a.eta}\n")

    print(f"  model = {a.model}  [HTTP-API]{'  [RETAIN]' if a.retain else ''}")
    counts, cost, toks, draws, errs = measure(arms, a.mock, a.runs, tasks=sel_tasks, workers=a.workers,
                                 model=a.model,
                                 http=True, retain=(a.retain or None))
    # A certificate is a statement about n valid draws. If transport failures thinned any cell,
    # the sample is not the one the design asked for, and the run must not be certified silently.
    _short = {f"{a_}|{t}": (a.runs - counts[a_][t][1])
              for a_ in arms for t in by_task if counts[a_][t][1] != a.runs}
    if _short:
        print("\n" + "=" * 78)
        print("INCOMPLETE SAMPLE - transport failures reduced these cells below n=%d:" % a.runs)
        for cell, missing in sorted(_short.items()):
            print("   %-28s %d draw(s) lost" % (cell, missing))
        if not a.allow_incomplete:
            print("Refusing to certify. Re-measure the affected cells, or pass")
            print("--allow-incomplete to write the run with its reduced denominators.")
            sys.exit(2)
        print("--allow-incomplete given: certifying on the reduced denominators.")
        print("=" * 78)

    total_cost = sum(cost[a_][t] for a_ in arms for t in by_task) * a.runs
    print(f"\ntotal measured spend = ${total_cost:.4f}  (n={a.runs}/cell, "
          f"{total_n_runs} runs)\n" + "=" * 78)

    # ---- (A) ESTIMATOR + incomparability ----
    inc, dAB, dBA = incomparability_test(counts["W1"], counts["W2"], by_task, tau=0.0)
    _, argA, gapsA = hat_delta_D(counts["W1"], counts["W2"], by_task)  # task where W2 beats W1
    _, argB, gapsB = hat_delta_D(counts["W2"], counts["W1"], by_task)  # task where W1 beats W2
    print("(A) INCOMPARABILITY (estimator)")
    print(f"    hat_delta_D(W1,W2) = {dAB:+.2f}  (sup at task '{argA}': W2 beats W1)")
    print(f"    hat_delta_D(W2,W1) = {dBA:+.2f}  (sup at task '{argB}': W1 beats W2)")
    print(f"    both > 0 ? {inc}  -> {'MUTUAL positive deficiency = EMPIRICAL INCOMPARABILITY' if inc else 'NOT shown'}")

    # ---- certificate for (A) ----
    cert = certify_incomparable(counts["W1"], counts["W2"], by_task, eta=a.eta)
    print(f"    CERTIFICATE (uniform, alpha_pair=eta/2|D|={cert['alpha_pair']:.4f}):")
    print(f"      L_D(W1,W2) lower bound on sup[PASS(W2)-PASS(W1)] = {cert['L_AB']:+.3f}")
    print(f"      L_D(W2,W1) lower bound on sup[PASS(W1)-PASS(W2)] = {cert['L_BA']:+.3f}")
    print(f"      certified incomparable at >= {1-a.eta:.0%} ? "
          f"{cert['certified_incomparable']}")

    # ---- (B) SCALAR MIS-RANK (Theorem 3 instantiated) ----
    prompt_of = {t["id"]: t["prompt"] for t in TASKS}
    print("\n(B) SCALAR MIS-RANK (Theorem 3 instantiated)")

    # (B1) WEAK/CONTRAST: the circular outcome-based aggregate (order depends on task mix).
    phi1 = aggregate_phi(counts["W1"], counts["none"], by_task)
    phi2 = aggregate_phi(counts["W2"], counts["none"], by_task)
    glob = "W1 > W2" if phi1 > phi2 else "W2 > W1"
    print(f"  (B1) outcome-aggregate phi (mean PASS lift, CIRCULAR/contrast only): "
          f"phi(W1)={phi1:+.2f}, phi(W2)={phi2:+.2f} -> ranks {glob} globally")

    # (B2) STRONG: query-CONDITIONED lexical relevance phi_lex(W,T) -- a real model-free scalar
    # computed BEFORE running the model. The strong Thm-3 violation = a task where relevance
    # ranks the sources OPPOSITE to realized PASS. This is what defeats the "just use relevance
    # of W to this task" confound (esp. the 'trap' task: reads like encoding, needs the contract).
    print("  (B2) query-conditioned lexical relevance phi_lex(W,T) vs realized PASS:")
    strong_viol = []
    for t in by_task:
        r1 = lexical_relevance(W1, prompt_of[t])
        r2 = lexical_relevance(W2, prompt_of[t])
        p1, p2 = pass_rate(counts["W1"][t]), pass_rate(counts["W2"][t])
        rel_rank = "W1>W2" if r1 > r2 else ("W2>W1" if r2 > r1 else "tie")
        pass_rank = "W1>W2" if p1 > p2 else ("W2>W1" if p2 > p1 else "tie")
        flip = (r1 > r2 and p2 > p1) or (r2 > r1 and p1 > p2)
        if flip:
            strong_viol.append((t, r1, r2, p1, p2))
        mark = "  <== RELEVANCE MIS-RANKS" if flip else ""
        print(f"      {t:<16} relevance(W1,W2)=({r1:.2f},{r2:.2f})->{rel_rank:<6} "
              f"PASS(W1,W2)=({p1:.0%},{p2:.0%})->{pass_rank:<6}{mark}")
    if strong_viol:
        t, r1, r2, p1, p2 = strong_viol[0]
        print(f"    [OK] STRONG Thm-3: on '{t}' relevance prefers "
              f"{'W2' if r2 > r1 else 'W1'} but PASS prefers "
              f"{'W1' if p1 > p2 else 'W2'} -> no query-conditioned relevance score can rank "
              f"these sources correctly for all tasks.")
    else:
        print("    [--] no query-conditioned relevance mis-rank at this n -- the STRONG claim "
              "is NOT demonstrated on this sample (honest null; raise --runs or revisit the "
              "trap task). The source-level incomparability in (A) still holds for "
              "query-INDEPENDENT ranking.")
    viol = strong_viol

    # ---- (C) DOMINANCE control: W1plus vs W2 (skipped unless W1plus was measured) ----
    dpv = dvp = None
    one_dir = dom_certified = strict_other_way = False
    domc = {"U_D": None, "alpha_pair": None}
    alpha_tol = 0.15
    if "W1plus" in arms:
        print("\n(C) DOMINANCE control: W1plus = W2 ++ W1 (literal superset of W2's signal)")
        incp, dpv, dvp = incomparability_test(counts["W1plus"], counts["W2"], by_task, tau=0.0)
        print(f"    hat_delta_D(W1plus,W2) = {dpv:+.2f}  (expect 0: no task where W2 beats W1plus)")
        print(f"    hat_delta_D(W2,W1plus) = {dvp:+.2f}  (expect >0: W1plus wins API tasks)")
        # one-directional dominance is a CONJUNCTION of two claims; split the eta budget so the
        # joint statement holds at >= 1-eta (each sub-claim at eta/2, union bound).
        eta_half = a.eta / 2.0
        domc = certify_dominance(counts["W1plus"], counts["W2"], by_task, eta=eta_half)
        print(f"    CERTIFICATE (uniform, alpha_pair=(eta/2)/|D|={domc['alpha_pair']:.4f}, "
              f"margin alpha_tol={alpha_tol}):")
        print(f"      U_D(W1plus,W2) upper bound on sup[PASS(W2)-PASS(W1plus)] = {domc['U_D']:.3f}")
        # one-directional dominance = (a) W1plus not beaten by W2 anywhere within margin AND
        # (b) W1plus strictly beats W2 somewhere (certified incomparability direction).
        dom_certified = (domc["U_D"] <= alpha_tol)
        strict_other_way = certify_incomparable(counts["W1plus"], counts["W2"], by_task,
                                                eta=eta_half)["L_BA"] > 0
        one_dir = dom_certified and strict_other_way
        print(f"      delta_D(W1plus,W2) <= {alpha_tol} certified ? {dom_certified}   "
              f"AND W1plus strictly beats W2 somewhere (certified) ? {strict_other_way}")
        print(f"    one-directional (W1plus dominates W2) ? {one_dir}  -> "
              f"{'for-all-tasks dominance REALIZED' if one_dir else 'not clean at this n -- raise --runs'}")
    else:
        print("\n(C) DOMINANCE control: SKIPPED (W1plus not in --arms)")

    # ---- (D) INTERFERENCE certificate (lead A): anti-monotonicity as a certified negative I_T --
    interf = None
    if "W1plus" in arms:
        interf = certify_interference(counts, by_task, eta=a.eta, tau=0.30)
        print("\n(D) INTERFERENCE I_T = PASS(W1plus)-PASS(W1)-PASS(W2)+PASS(none) "
              f"(certify harm I_T<=-{interf['tau']}, alpha=eta/4):")
        for t in by_task:
            d = interf["detail"][t]
            mark = "  <== CERTIFIED HARM" if d["certified_harm"] else ""
            print(f"      {t:<16} I_T={d['I_T']:+.2f}  upper={d['I_T_upper']:+.2f}{mark}")
        msg = (str(interf["certified_tasks"]) if interf["certified_tasks"] else
               "NONE at this n (I_T compounds 4 cells; needs ~n>=80/cell -- the harm is real in "
               "the point estimates but not yet CERTIFIED here)")
        print(f"    certified-harm tasks: {msg}")

    # ---- (E) ORDER control (lead C): is the harm order-invariant or lost-in-the-middle? ----
    order = None
    if "W1plus" in arms and "W1plus_rev" in arms:
        order = {}
        margin = 0.20
        print("\n(E) ORDER control: does REORDERING RECOVER the collapse? "
              "(W1plus=W2++W1 [W1 last] vs W1plus_rev=W1++W2 [W1 first]; ref = W1-alone)")
        # The decision-relevant question is NOT 'do the two orderings differ' (noise) but
        # 'does the BETTER ordering recover toward W1-alone'. If neither ordering recovers on a
        # collapsed task -> harm is order-robust -> HARDENS anti-monotonicity (not lost-in-middle).
        collapse_both, recovered = [], []
        for t in by_task:
            pf = pass_rate(counts["W1plus"][t])
            pr = pass_rate(counts["W1plus_rev"][t])
            w1 = pass_rate(counts["W1"][t]) if "W1" in arms else None
            best = max(pf, pr)
            tag = ""
            if w1 is not None:
                if w1 - best > margin:        # even the better ordering stays well below W1-alone
                    collapse_both.append(t); tag = "  <== collapse persists in BOTH orders"
                elif w1 - min(pf, pr) > margin:  # one order recovers, the other doesn't
                    recovered.append(t); tag = "  <== one ordering RECOVERS (positional)"
            order[t] = {"W1plus": pf, "W1plus_rev": pr, "W1": w1, "gap": round(pr - pf, 3)}
            ref = f"  W1={w1:.0%}" if w1 is not None else ""
            print(f"      {t:<16} W1plus={pf:.0%}  W1plus_rev={pr:.0%}{ref}  gap={pr-pf:+.0%}{tag}")
        if "W1" in arms:
            verdict = ("ORDER-ROBUST HARM: reordering does NOT recover W1-alone PASS on "
                       f"{len(collapse_both)}/{len(by_task)} tasks -> NOT a lost-in-the-middle "
                       "artifact -> HARDENS anti-monotonicity"
                       if len(collapse_both) >= len(recovered) else
                       f"POSITIONAL: a reordering recovers PASS on {len(recovered)} task(s) -> "
                       "harm is partly lost-in-the-middle")
            print(f"    -> {verdict}  (note: per-task order gaps may be noisy at small n; "
                  "recovery-vs-W1 is the decision-relevant test, not gap sign)")
        else:
            print("    (add W1 to --arms for the recovery verdict)")

    # ---- (F) RUNTIME token tell (lead D): paired output-token inflation on the harmful arm ----
    tokgap = None
    if "W1plus" in arms:
        print("\n(F) RUNTIME tell: paired output_tokens W1plus vs W1 (same task)")
        tokgap = {}
        for t in by_task:
            a1 = toks["W1"][t]
            ap_ = toks["W1plus"][t]
            rel = (ap_ - a1) / a1 if a1 else 0.0
            tokgap[t] = {"W1": round(a1, 1), "W1plus": round(ap_, 1), "rel": round(rel, 3)}
            print(f"      {t:<16} W1={a1:.0f}tok  W1plus={ap_:.0f}tok  ({rel:+.0%})")

    # ---- sample-size guidance ----
    nstar = required_n(target_halfwidth=0.15, eta=a.eta, D=len(TASKS))
    nstark = required_n_stark(eta=a.eta, D=len(TASKS))
    print("\n" + "=" * 78)
    print(f"sample-size (alpha_pair=eta/2|D|, |D|={len(TASKS)}):")
    print(f"  worst case (p~0.5, CP half-width<=0.15): n >= {nstar}/cell.")
    print(f"  STARK crossover (clean ~0% vs ~100%, as designed): n >= {nstark}/cell "
          f"-> START HERE; raise n only if the real split is noisy.")
    print("=" * 78)

    out = {
        "counts": {f"{a_}|{t}": counts[a_][t] for a_ in arms for t in by_task},
        "draws": {f"{a_}|{t}": draws[a_][t] for a_ in arms for t in by_task},
        "errs": {f"{a_}|{t}": errs[a_][t] for a_ in arms for t in by_task},
        "estimator": {"hat_delta_W1_W2": dAB, "hat_delta_W2_W1": dBA,
                      "argsup_W2_beats_W1": argA, "argsup_W1_beats_W2": argB,
                      "incomparable": inc},
        "scalar": {"phi_W1": phi1, "phi_W2": phi2, "global_rank": glob,
                   "pointwise_violations": [v[0] for v in viol]},
        "certificate_incomparable": {k: v for k, v in cert.items() if k != "detail"},
        "certificate_incomparable_detail": cert["detail"],
        "dominance": {"hat_delta_W1plus_W2": dpv, "hat_delta_W2_W1plus": dvp,
                      "one_directional": one_dir, "U_D_W1plus_W2": domc["U_D"],
                      "alpha_tol": alpha_tol, "dom_certified": dom_certified,
                      "strict_other_way": strict_other_way},
        "interference": interf,   # lead A: certified anti-monotone I_T
        "order_control": order,   # lead C: order-invariance of the harm
        "runtime_tokens": tokgap,  # lead D: paired output-token tell
        "n_per_cell": a.runs, "eta": a.eta, "total_cost_usd": total_cost,
        "required_n_halfwidth_0.15": nstar, "mock": a.mock,
    }
    (REPO / a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote {REPO / a.out}")


if __name__ == "__main__":
    main()
