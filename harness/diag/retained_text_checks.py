"""Textual checks over the retained completions, with the rules written out.

The manuscript reports four things read off the retained replies behind the anti-monotonicity
table: whether the extractor found code at all, whether the `import ledger` line is present,
whether the reply declined the task, and whether the superset reply carries W2's wire encoding.
Each is a regular expression over the reply, and each is printed here beside its result so the
number in the paper and the rule that produced it cannot drift apart.

That last check is the one that needed republishing. An earlier version of it looked for the
encoded amount as a quoted literal, `['\"]\\s*[+-]\\d`, which finds nothing when the reply builds
the string at run time -- as in

    sign = '+' if cents >= 0 else '-'
    check = sum(int(d) for d in str(abs(cents))) % 10
    amount = f"{sign}{digits}#{check}"

so it reported zero hits on replies that plainly do carry the encoding. The rule below is the one
the released audit code uses (`audit_any.py`), and it is the one the paper now quotes.

Read what it is: a textual flag for the encoding being present in the reply. It is not a semantic
check, not a correctness test, and not evidence of causation. On the two API cells it fires on
238/240 of the W2 replies, and every one of those replies FAILS the API verifier -- W2 passes 0/240
there. The cell where applying the encoding is the contract is enc_amount, a different population,
and both PASS and the flag are printed for it below so the two are not confused again.

Usage:  python harness/diag/retained_text_checks.py
"""
import os, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "harness"))
import measure_blackwell as mb                                      # noqa: E402

RETAIN = os.path.join(ROOT, "results", "retain_api")

# --- the four rules, verbatim -------------------------------------------------------------
WIRE = re.compile(r"#\{|f\"\{sign\}|check\s*=|% 10")                # as in audit_any.py:138
IMPORT = re.compile(r"^\s*(import ledger|from ledger import)", re.M)
REFUSAL = re.compile(r"\bI can(?:no|')t\b|\bI won't\b|\bI'm (?:not able|unable)\b"
                     r"|\bunable to (?:help|assist|comply)\b|\bI must decline\b", re.I)
# The refusal screen runs on prose only: `as an AI` and the like occur inside generated
# docstrings, and one Haiku reply matches on a docstring line while solving the task.
def prose_of(raw):
    return re.sub(r"```.*?```", " ", raw, flags=re.S)


MODELS = [("haiku", "claude-haiku-4-5", "Haiku-4.5"),
          ("sonnet", "claude-sonnet-4-6", "Sonnet-4.6"),
          ("opus", "claude-opus-4-8", "Opus-4.8")]
TASKS = ["api_post_ok", "api_argorder", "enc_amount", "trap_store_wire"]
COLLAPSE = ["api_post_ok", "api_argorder"]
ARMS = ["none", "W1", "W2", "W1plus"]
N = 40

cells = {}
for d, mid, _label in MODELS:
    for t in TASKS:
        for a in ARMS:
            wire = imp = ref = empty = n = 0
            length = 0
            for i in range(N):
                p = os.path.join(RETAIN, d, "%s__%s__%s__%03d.txt" % (mid, t, a, i))
                if not os.path.exists(p):
                    continue
                raw = open(p, encoding="utf-8").read()
                code = mb._extract_code(raw)
                n += 1
                length += len(code)
                empty += not code.strip()
                wire += bool(WIRE.search(code))
                imp += bool(IMPORT.search(code))
                ref += bool(REFUSAL.search(prose_of(raw)))
            cells[(d, t, a)] = dict(wire=wire, imp=imp, ref=ref, empty=empty, n=n,
                                    mean=length / max(1, n))

print("Rules applied (each over the extracted code, except the refusal screen, which runs on the")
print("prose outside the fences):")
print("  wire encoding   %s" % WIRE.pattern)
print("  import present  %s" % IMPORT.pattern)
print("  refusal         %s" % REFUSAL.pattern)
print()
print("%-11s %-17s %-8s %7s %7s %7s %7s %8s" %
      ("model", "cell", "arm", "wire", "import", "empty", "refusal", "mean len"))
for d, mid, label in MODELS:
    for t in TASKS:
        for a in ARMS:
            c = cells[(d, t, a)]
            print("%-11s %-17s %-8s %3d/%-3d %3d/%-3d %7d %7d %8.0f" %
                  (label, t, a, c["wire"], c["n"], c["imp"], c["n"], c["empty"], c["ref"],
                   c["mean"]))


def agg(arms, tasks, key):
    return (sum(cells[(d, t, a)][key] for d, _, _ in MODELS for t in tasks for a in arms),
            sum(cells[(d, t, a)]["n"] for d, _, _ in MODELS for t in tasks for a in arms))


print()
print("Over the two collapse cells on all three models:")
for a in ("W1plus", "W1", "W2", "none"):
    k, n = agg([a], COLLAPSE, "wire")
    print("  wire flag on %-7s %3d/%d" % (a, k, n))
for a in ("W1plus", "W1"):
    k, n = agg([a], COLLAPSE, "imp")
    print("  import on    %-7s %3d/%d" % (a, k, n))
k, n = agg(["W1", "W1plus"], COLLAPSE, "ref")
print("  refusals on W1 and W1plus together %d/%d" % (k, n))
k, n = agg(["W1", "W1plus"], COLLAPSE, "empty")
print("  empty extractions, same set        %d/%d" % (k, n))

# The flag beside realized PASS, so the two are never read as the same thing. On the API cells the
# flagged W2 replies all fail; the cell where the encoding is the contract is enc_amount.
import json                                                          # noqa: E402
RUNS = {"haiku": "blackwell_haiku_api_n40", "sonnet": "blackwell_sonnet_api_n40",
        "opus": "blackwell_opus_api_n40"}
PASS = {}
for d, _mid, _label in MODELS:
    c = json.load(open(os.path.join(ROOT, "results", RUNS[d] + ".json"), encoding="utf-8"))["counts"]
    for t in TASKS:
        for a in ARMS:
            PASS[(d, t, a)] = tuple(c["%s|%s" % (a, t)])
print()
print("The flag against realized PASS:")
for tasks, lab in ((COLLAPSE, "two API cells"), (["enc_amount"], "enc_amount")):
    for a in ("W1plus", "W1", "W2"):
        fk, fn = agg([a], tasks, "wire")
        pk = sum(PASS[(d, t, a)][0] for d, _, _ in MODELS for t in tasks)
        pn = sum(PASS[(d, t, a)][1] for d, _, _ in MODELS for t in tasks)
        print("  %-14s %-7s flag %3d/%-4d PASS %3d/%d" % (lab, a, fk, fn, pk, pn))

print()
print("LaTeX rows for the appendix table:")
for d, mid, label in MODELS:
    first = True
    for t in COLLAPSE:
        for a in ("W1", "W1plus"):
            c = cells[(d, t, a)]
            print("%-10s & %-22s & %-9s & $%d$ & $%d/%d$ & $%d/%d$ & $%d$ / $%d$ \\\\" % (
                label if first else "", r"\texttt{%s}" % t.replace("_", r"\_") if a == "W1" else "",
                "$W_1$" if a == "W1" else "$W_{1+}$",
                round(c["mean"]), c["imp"], c["n"], c["wire"], c["n"], c["empty"], c["ref"]))
            first = False
