# Merge a prevalence run with isolated cell re-runs (outage protocol) and re-analyse.
#   python harness/prevalence_merge.py MAIN.json [ISO.json ...] [--log MAIN.log]
# Tainted cells = cells whose log line carries an ERR: tag (transport-outage draws scored as 0),
# or whose JSON errs flags contain a 1. Each ISO.json (from --only-cells) replaces those cells.
import argparse, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_prevalence import analyse

ap = argparse.ArgumentParser()
ap.add_argument("main"); ap.add_argument("iso", nargs="*"); ap.add_argument("--log", default="")
a = ap.parse_args()
main = json.load(open(a.main, encoding="utf-8"))

tainted = set()
if a.log:
    for line in open(a.log, encoding="utf-8", errors="replace"):
        m = re.match(r"^\s+arm=(\S+)\s+(\S+)\s+PASS.*ERR:", line)
        if m:
            tainted.add(m.group(1) + "|" + m.group(2))
for cell, flags in main.get("errs", {}).items():
    if any(flags):
        tainted.add(cell)

replaced = set()
for p in a.iso:
    iso = json.load(open(p, encoding="utf-8"))
    for cell, kn in iso["counts"].items():
        if any(iso.get("errs", {}).get(cell, [0])):
            print(f"  WARNING: isolated re-run of {cell} still has outage draws; not merged")
            continue
        main["counts"][cell] = kn
        main["draws"][cell] = iso["draws"][cell]
        main.setdefault("errs", {})[cell] = iso["errs"][cell]
        replaced.add(cell)

still = sorted(tainted - replaced)
print("tainted cells :", sorted(tainted))
print("replaced      :", sorted(replaced))
if still:
    print("STILL TAINTED :", still, "-> re-run with --only-cells before trusting verdicts")

arms = ["none"] + main["pool"]
by_task = list(main["topk"].keys())
counts = {x: {t: tuple(main["counts"][f"{x}|{t}"]) for t in by_task} for x in arms}
res = analyse(counts, by_task, main["pool"], main["topk"])
main["analysis"] = res
main["merged_from"] = a.iso
main["still_tainted"] = still
out = Path(a.main).with_suffix(".merged.json")

print("none-baseline PASS:", {t: f"{v:.0%}" for t, v in res["none_pass"].items()},
      "| leaky (excluded):", res["leaky_tasks"])
print(f"pairs: {res['n_pairs']} total, {res['n_co_retrieved']} co-retrieved")
print("verdicts ALL          :", res["tally_all"])
print("verdicts CO-RETRIEVED :", res["tally_co_retrieved"])

# Sign-pattern breakdown. Certified dominance (U_D <= 0) needs A >= B with margin on EVERY task,
# which finite n cannot certify when both sources tie at 0 on some task; so "one-way evidence"
# (L > 0 in exactly one direction) is the practical nested-vs-incomparable signal at small n.
def pattern(r):
    a, b = r["L_AB"] > 0, r["L_BA"] > 0
    return "incomparable" if (a and b) else ("one-way evidence" if (a or b) else "no evidence")
from collections import Counter as _C
pat_all = _C(pattern(r) for r in res["pairs"])
pat_co = _C(pattern(r) for r in res["pairs"] if r["co_retrieved"])
print("sign pattern ALL          :", dict(pat_all))
print("sign pattern CO-RETRIEVED :", dict(pat_co))
main["analysis"]["pattern_all"] = dict(pat_all)
main["analysis"]["pattern_co_retrieved"] = dict(pat_co)
print("per pair:")
for r in res["pairs"]:
    tag = "*" if r["co_retrieved"] else " "
    print(f"  {tag} {r['verdict']:<13} L={r['L_AB']:+.2f}/{r['L_BA']:+.2f}  {r['pair'][0]}  vs  {r['pair'][1]}")
print("wrote", out)
out.write_text(json.dumps(main, indent=1), encoding="utf-8")
