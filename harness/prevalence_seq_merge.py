# Merge isolated cell re-runs into a sequential prevalence result and recompute the two-stage
# verdicts: pairs verified in stage 1 (n_at_verdict < nmax) are kept; every other pair is re-tested
# with fixed-n Clopper-Pearson at alpha/2 on the merged counts (stage 2).
#   python harness/prevalence_seq_merge.py MAIN.json [ISO.json ...]
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "sequential"))
from seq_replay import cp_interval
ETA = 0.10
main_p = Path(sys.argv[1]); main = json.load(open(main_p, encoding="utf-8"))
tainted = sorted(c for c, f in main["errs"].items() if any(f))
replaced = []
for p in sys.argv[2:]:
    iso = json.load(open(p, encoding="utf-8"))
    for cell, kn in iso["counts"].items():
        if any(iso["errs"].get(cell, [0])):
            print("  WARNING", cell, "re-run still has outage draws; not merged"); continue
        main["counts"][cell] = kn; main["draws"][cell] = iso["draws"][cell]; main["errs"][cell] = iso["errs"][cell]
        main.setdefault("stop_n", {})[cell] = kn[1]; replaced.append(cell)
still = sorted(set(tainted) - set(replaced))
print("tainted:", tainted); print("replaced:", replaced)
if still: print("STILL TAINTED:", still)
clean = main["clean_tasks"]; pool = main["pool"]; nmax = main["nmax"]
alpha = ETA / (2 * len(clean)); a2 = alpha / 2
def iv(x, t):
    k, n = main["counts"][f"{x}|{t}"]; return cp_interval(k, n, a2)
def L(A, B):
    return max(iv(B, t)[0] - iv(A, t)[1] for t in clean)
rows = []
for r in main["pairs"]:
    a, b = r["pair"]
    if r["verdict"] == "INCOMPARABLE" and r["n_at_verdict"] < nmax and not ({a, b} & set(c.split("|")[0] for c in replaced)):
        rows.append(r); continue                       # stage-1 verdict on untouched cells stands
    lab, lba = L(a, b), L(b, a)
    st = "INCOMPARABLE" if (lab > 0 and lba > 0) else "unresolved"
    pat = "incomparable" if (lab > 0 and lba > 0) else ("one-way evidence" if (lab > 0 or lba > 0) else "no evidence")
    rows.append({**r, "verdict": st, "pattern": pat, "L_AB": round(lab, 3), "L_BA": round(lba, 3), "n_at_verdict": nmax})
main["pairs"] = rows
main["tally"] = dict(Counter(r["verdict"] for r in rows))
main["pattern_all"] = dict(Counter(r["pattern"] for r in rows))
main["pattern_co"] = dict(Counter(r["pattern"] for r in rows if r["co_retrieved"]))
main["merged_from"] = sys.argv[2:]; main["still_tainted"] = still
out = main_p.with_suffix(".merged.json"); out.write_text(json.dumps(main, indent=1), encoding="utf-8")
print("verdicts:", main["tally"], "| patterns ALL", main["pattern_all"], "CO", main["pattern_co"])
print(f"calls {main['calls']} vs fixed {main['fixed_calls']} -> {main['fixed_calls']/max(main['calls'],1):.2f}x")
print("wrote", out)
