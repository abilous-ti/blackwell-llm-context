# Splice isolated cell re-runs (harness/diag/cell_rerun.py output) into a harness results JSON
# that carries per-draw 'draws', producing MAIN.clean.json with no outage-scored draws.
#   python splice_rerun.py MAIN.json RERUN1.json [RERUN2.json ...]
import json, sys
from pathlib import Path
main_p = Path(sys.argv[1]); main = json.load(open(main_p, encoding="utf-8"))
main.setdefault("errs", {})
for p in sys.argv[2:]:
    d = json.load(open(p, encoding="utf-8")); cell = d["cell"]
    draws = [1 if r["solved"] else 0 for r in d["rows"]]
    errs = [1 if r.get("error") else 0 for r in d["rows"]]
    if any(errs):
        print(f"  WARNING {cell}: {sum(errs)} residual outage draw(s) -> NOT spliced"); continue
    old = main["counts"].get(cell)
    main["counts"][cell] = d["counts"]; main["draws"][cell] = draws; main["errs"][cell] = errs
    print(f"  spliced {cell}: {old} -> {d['counts']}  (n={len(draws)}, outage draws 0)")
main["spliced_from"] = sys.argv[2:]
out = main_p.with_suffix(".clean.json")
out.write_text(json.dumps(main, indent=1), encoding="utf-8")
print("wrote", out)
