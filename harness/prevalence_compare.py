# Like-for-like: fixed-n prevalence (measure_prevalence *.merged.json) vs sequential (prevalence_seq).
#   python harness/prevalence_compare.py FIXED.merged.json SEQ.json
import json, sys
from collections import Counter
F = json.load(open(sys.argv[1], encoding="utf-8")); S = json.load(open(sys.argv[2], encoding="utf-8"))
fp = {tuple(sorted(r["pair"])): r for r in F["analysis"]["pairs"]}
sp = {tuple(sorted(r["pair"])): r for r in S["pairs"]}
common = sorted(set(fp) & set(sp))
agree = Counter()
for k in common:
    fv = "INC" if fp[k]["verdict"] == "INCOMPARABLE" else "other"
    sv = "INC" if sp[k]["verdict"] == "INCOMPARABLE" else "other"
    agree[(fv, sv)] += 1
print(f"pairs compared: {len(common)}   (fixed-only {len(set(fp)-set(sp))}, seq-only {len(set(sp)-set(fp))})")
print("verdict agreement (fixed, seq):", dict(agree))
fpat = Counter(("incomparable" if (r["L_AB"] > 0 and r["L_BA"] > 0) else "one-way evidence" if (r["L_AB"] > 0 or r["L_BA"] > 0) else "no evidence") for r in fp.values())
print("patterns fixed:", dict(fpat), "| seq:", S["pattern_all"])
fixed_calls = (len(F["pool"]) + 1) * len(F["topk"]) * F["n_per_cell"]
print(f"calls: fixed {fixed_calls}  seq {S['calls']}  -> {fixed_calls/max(S['calls'],1):.2f}x")
for k in common:
    if (fp[k]["verdict"] == "INCOMPARABLE") != (sp[k]["verdict"] == "INCOMPARABLE"):
        print("  DISAGREE", k, "fixed:", fp[k]["verdict"], f"({fp[k]['L_AB']:+.2f}/{fp[k]['L_BA']:+.2f})",
              "seq:", sp[k]["verdict"], f"({sp[k]['L_AB']:+.2f}/{sp[k]['L_BA']:+.2f})")
