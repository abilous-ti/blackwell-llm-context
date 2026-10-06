r"""Structural certificate for every source pair: the premises of Lemma 1, checked by enumeration.

For each pair, over its whole declared family (pairs.py):

  1. non-degeneracy   each source's convention space has at least two states;
  2. injectivity      distinct states of a source render to distinct texts, so the text determines
                      the convention (the rendering map of Section 3.1.2 is invertible on its range);
  3. separation       a source's text is rendered from its own state only (by construction), and no
                      literal of the other source's conventions occurs in it or in any task prompt;
  4. decisiveness     (strict pairs) the verifier of each task is generated from its decisive state
                      only; the reference program for a state passes under that state, for every
                      state of the other source, and fails under every other decisive state;
  5. strictness       (strict pairs) a program that tries a wrong convention first and falls back to
                      the right one fails, because the stub records the non-conforming call.

1-3 with a product prior give Lemma 1: the two sources are structurally (Blackwell-) incomparable.
4-5 bound the guessing cap of Lemma 2(a) for programs that use the module only through its calls:
a program passes under at most the states that agree with its first call (and, for a broad
exception handler, any exception name), so the cap without the decisive source is at most
max_s mu(S = s) times that count. The cache pair keeps its published verifier, which is not
strict, so only 1-3 are claimed for it.

Usage:  python harness/package2/certify_pairs.py      (writes results/package2/certificates.json)
"""
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import pairs as P  # noqa: E402
import measure_blackwell as mb  # noqa: E402   (verify_in only; no globals are changed)


def run(code, verifier):
    wd = Path(tempfile.mkdtemp(prefix="cert_"))
    try:
        (wd / "solution.py").write_text(code, encoding="utf-8")
        return mb.verify_in(wd, verifier)
    finally:
        import shutil
        shutil.rmtree(wd, ignore_errors=True)


def gaming_programs(fn):
    """The two kinds of test-gaming GPT-5.5 produced in the pilot, as adversarial programs:
    an object equal to every string, and a function that returns a string constant read from the
    calling test's own code."""
    always_equal = ("class _S(str):\n"
                    "    def __eq__(self, o):\n        return True\n"
                    "    def __ne__(self, o):\n        return False\n"
                    "    __hash__ = str.__hash__\n"
                    "def %s(*a, **k):\n    return _S('x')\n" % fn)
    frame_reader = ("import sys\n"
                    "def %s(*a, **k):\n"
                    "    f = sys._getframe(1)\n"
                    "    consts = [c for c in f.f_code.co_consts if isinstance(c, str) and len(c) > 3]\n"
                    "    names = [v for v in f.f_globals.values() if isinstance(v, str)]\n"
                    "    pool = consts + names\n"
                    "    return pool[0] if pool else ''\n" % fn)
    return {"always-equal": always_equal, "frame-reader": frame_reader}


def literals(pair_id, side, state):
    """Strings that identify a convention value (checked for leaks into other texts and prompts)."""
    if pair_id == "cache":
        return [state["kw"] + "=", state["exc"]] if side == "A" else [state["prefix"]]
    if pair_id == "inventory":
        return [state["kw"] + "=", state["exc"]] if side == "A" else [state["prefix"], state["check"].split(":")[1]]
    if pair_id == "audit":
        if side == "A":
            return [c for c in P.AUDIT_TABLES[state["table"]].values()]
        return []        # separators and case are single characters or words; examples checked below
    raise KeyError(pair_id)


def published_cache():
    """The published pair-2 texts and verifiers, read in a separate process (importing
    measure_blackwell_pair2 patches measure_blackwell's globals, so it must not run here)."""
    code = ("import json,sys;sys.path.insert(0,%r);import measure_blackwell_pair2 as p;"
            "print(json.dumps({'V1':p.V1,'V2':p.V2,'tasks':{t['id']:{'prompt':t['prompt'],"
            "'verify':t['verify']} for t in p.TASKS}}))" % str(HERE.parent))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8")
    return json.loads(out.stdout)


def certify(pair_id):
    p = P.PAIRS[pair_id]
    a_states, b_states = P.states(p["A_space"]), P.states(p["B_space"])
    problems, notes = [], []
    # 1. non-degeneracy
    if len(a_states) < 2 or len(b_states) < 2:
        problems.append("a source has fewer than two states")
    # 2. injectivity
    a_texts = [p["render_a"](s) for s in a_states]
    b_texts = [p["render_b"](s) for s in b_states]
    if len(set(a_texts)) != len(a_texts):
        problems.append("A's rendering is not injective")
    if len(set(b_texts)) != len(b_texts):
        problems.append("B's rendering is not injective")
    # 3. separation: no literal of B's family in any A text (and vice versa), none in any prompt
    prompts = [t["prompt"] for t in p["tasks"]]
    for side, own_texts, other_states in (("A", a_texts, b_states), ("B", b_texts, a_states)):
        other = "B" if side == "A" else "A"
        for st in other_states:
            for lit in literals(pair_id, other, st):
                if any(lit in t for t in own_texts):
                    problems.append("%s text mentions %s literal %r" % (side, other, lit))
    for s in a_states:
        for lit in literals(pair_id, "A", s):
            if any(lit in pr for pr in prompts):
                problems.append("a task prompt mentions A literal %r" % lit)
    for s in b_states:
        for lit in literals(pair_id, "B", s):
            if any(lit in pr for pr in prompts):
                problems.append("a task prompt mentions B literal %r" % lit)
    real_a, real_b = P.texts(pair_id)
    if pair_id == "audit":       # the line-format example must not appear in A or in a prompt
        for s in b_states:
            ex = P.audit_line(s, "ann", "login", 255)
            if ex in real_a or any(ex in pr for pr in prompts):
                problems.append("audit line example leaks")
    # cache: realized texts and verifiers must equal the published ones
    if pair_id == "cache":
        pub = published_cache()
        if real_a != pub["V1"] or real_b != pub["V2"]:
            problems.append("cache realized texts differ from the published V1/V2")
        for t in p["tasks"]:
            if pub["tasks"][t["id"]]["verify"] != t["verify_real"] or pub["tasks"][t["id"]]["prompt"] != t["prompt"]:
                problems.append("cache task %s differs from the published one" % t["id"])
        notes.append("published verifiers kept (not strict): only premises 1-3 are claimed")
        # hardened variants: correct programs pass, the pilot's gaming programs fail
        good = {"cache_put_ok": "import cache\ndef store(k, v, secs):\n    return cache.put(k, v, ttl=secs)\n",
                "key_norm": ("import re\ndef make_key(label):\n"
                             "    s=re.sub(r'[^0-9a-z]+','_',label.lower()).strip('_')\n    return 'kx7-'+s\n")}
        for t in p["tasks"]:
            if not run(good[t["id"]], t["verify_hard"]):
                problems.append("%s: a correct program fails the hardened check" % t["id"])
        cheat = gaming_programs("make_key")
        for name, prog in cheat.items():
            if run(prog, p["tasks"][1]["verify_hard"]):
                problems.append("key_norm: %s program passes the hardened check" % name)
            notes.append("key_norm, %s program under the published check: %s" % (
                name, "passes" if run(prog, p["tasks"][1]["verify_real"]) else "fails"))
    # 4-5. decisiveness and strictness (strict pairs)
    caps = {}
    if p["strict"]:
        for t in p["tasks"]:
            dec_states = a_states if t["decisive"] == "A" else b_states
            n_runs = 0
            for s in dec_states:
                ref = t["reference"](s)
                for s2 in dec_states:
                    ok = run(ref, t["verify"](s2))
                    n_runs += 1
                    if (s == s2) != ok:
                        problems.append("%s: reference for %s %s under %s" % (
                            t["id"], P.key_of(s), "fails" if s == s2 else "passes", P.key_of(s2)))
            # fallback programs (API task of the inventory pair): wrong convention first, right second
            if t["id"] == "inv_book":
                real = p["A_real"]
                for wrong in dec_states:
                    if (wrong["order"], wrong["kw"]) == (real["order"], real["kw"]):
                        continue
                    call = lambda st: ("inventory.reserve(n, code, %s=30)" if st["order"] == "qty_first"
                                       else "inventory.reserve(code, n, %s=30)") % st["kw"]
                    prog = ("import inventory\n"
                            "def book_units(code, n):\n"
                            "    for f in (lambda: %s, lambda: %s):\n"
                            "        try:\n"
                            "            return f()\n"
                            "        except TypeError:\n"
                            "            continue\n"
                            "        except Exception:\n"
                            "            return -1\n"
                            "    return -1\n" % (call(wrong), call(real)))
                    n_runs += 1
                    if run(prog, t["verify"](real)):
                        problems.append("fallback program passes after a wrong first call (%s)" % P.key_of(wrong))
                # broad handler: passes under every exception name -> pass set <= |exc alternatives|
                n_exc = len(p["A_space"]["exc"])
                caps[t["id"]] = {"max_pass_states": n_exc, "states": len(dec_states),
                                 "cap_uniform_prior": n_exc / len(dec_states)}
            else:
                caps[t["id"]] = {"max_pass_states": 1, "states": len(dec_states),
                                 "cap_uniform_prior": 1 / len(dec_states)}
                fn = {"inv_sku": "sku_code", "audit_code": "status_code", "audit_line": "audit_line"}[t["id"]]
                real = p["A_real"] if t["decisive"] == "A" else p["B_real"]
                for name, prog in gaming_programs(fn).items():
                    n_runs += 1
                    if run(prog, t["verify"](real)):
                        problems.append("%s: %s program passes" % (t["id"], name))
            notes.append("%s: %d verifier runs" % (t["id"], n_runs))
    return {"pair": pair_id, "A_states": len(a_states), "B_states": len(b_states),
            "A_real": p["A_real"], "B_real": p["B_real"],
            "A_chars": len(real_a), "B_chars": len(real_b),
            "premises_1_3": not [x for x in problems if "reference" not in x and "fallback" not in x],
            "strict": p["strict"], "caps": caps, "problems": problems, "notes": notes,
            "conclusion": ("structurally incomparable by Lemma 1 (declared family, product prior)"
                           if not problems else "NOT CERTIFIED")}


def main():
    out = {pid: certify(pid) for pid in P.PAIRS}
    d = ROOT / "results" / "package2"
    d.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(d / "certificates.json", "w", encoding="utf-8"), indent=1)
    for pid, c in out.items():
        print("== %s: %s" % (pid, c["conclusion"]))
        print("   states A %d, B %d; realized text lengths A %d, B %d chars" % (
            c["A_states"], c["B_states"], c["A_chars"], c["B_chars"]))
        for k, v in c["caps"].items():
            print("   %s: a program passes under at most %d of %d decisive states -> cap <= %.3f "
                  "under a uniform prior" % (k, v["max_pass_states"], v["states"], v["cap_uniform_prior"]))
        for n in c["notes"]:
            print("   note:", n)
        for pr in c["problems"]:
            print("   PROBLEM:", pr)
    return 0 if all(not c["problems"] for c in out.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
