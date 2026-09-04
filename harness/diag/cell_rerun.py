"""Clean re-measurement of ONE cell (model, task, arm) with the retry harness; re-draws any
draw that still ends in a transport error so the reported n contains no outage-scored zeros.
Usage: cell_rerun.py MODEL TASK ARM N OUT.json"""
import sys, json
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard\tokenbench")
import measure_blackwell as mb
model, tid, arm, n, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
task = next(t for t in mb.TASKS if t["id"] == tid)
def draw(i): return mb.run_one(task, arm, False, i, model, singleshot=True)
with ThreadPoolExecutor(max_workers=3) as ex: rows = list(ex.map(draw, range(n)))
for extra in range(2):                       # re-draw residual transport failures
    bad = [i for i, r in enumerate(rows) if r.get("error")]
    if not bad: break
    print(f"  re-drawing {len(bad)} errored draw(s), pass {extra+1}")
    with ThreadPoolExecutor(max_workers=2) as ex:
        for i, r in zip(bad, ex.map(draw, bad)): rows[i] = r
k = sum(1 for r in rows if r["solved"]); errs = sum(1 for r in rows if r.get("error"))
print(f"{model} {arm}|{tid}  PASS {k}/{n} = {k/n:.0%}   errs={errs}   spend ${sum(r['cost'] for r in rows):.3f}")
json.dump({"model": model, "cell": f"{arm}|{tid}", "counts": [k, n], "errs": errs,
           "rows": [{k_: r.get(k_) for k_ in ("solved", "cost", "out_tokens", "error")} for r in rows]},
          open(out, "w", encoding="utf-8"), indent=1)
