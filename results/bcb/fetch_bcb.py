"""Pull BigCodeBench through the HF datasets-server (JSON, so no pyarrow needed)
and find library pairs whose task sets are disjoint -- the natural analogue of the
paper's hand-built W1/W2 opposition."""
import json, urllib.request, os, sys, io, itertools, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = r"C:\Users\ANDRIY~1\AppData\Local\Temp\claude\C--Users-AndriyBilous-Documents-GitHub-tokenguard\5393d1a5-e56d-4ada-be5a-64d011ebda1a\scratchpad\bcb.json"
BASE = ("https://datasets-server.huggingface.co/rows?dataset=bigcode%2Fbigcodebench"
        "&config=default&split=v0.1.4&offset={off}&length=100")

if os.path.exists(OUT):
    rows = json.load(open(OUT, encoding="utf-8"))
    print("cached:", len(rows), "tasks")
else:
    rows, off = [], 0
    while True:
        with urllib.request.urlopen(BASE.format(off=off), timeout=60) as r:
            d = json.loads(r.read().decode("utf-8"))
        batch = [x["row"] for x in d.get("rows", [])]
        if not batch:
            break
        rows += batch
        off += len(batch)
        print("  fetched", off, flush=True)
        if off >= d.get("num_rows_total", 0):
            break
    json.dump(rows, open(OUT, "w", encoding="utf-8"))
    print("fetched", len(rows), "tasks ->", OUT)

# --- library -> task sets --------------------------------------------------
def libs_of(r):
    v = r.get("libs")
    if isinstance(v, str):
        try:
            v = json.loads(v.replace("'", '"'))
        except Exception:
            v = [x.strip().strip("'\"") for x in v.strip("[]").split(",") if x.strip()]
    return set(v or [])

by_lib = collections.defaultdict(set)
for r in rows:
    for L in libs_of(r):
        by_lib[L].add(r["task_id"])

print()
print("libraries:", len(by_lib))
top = sorted(by_lib.items(), key=lambda kv: -len(kv[1]))[:14]
for L, ts in top:
    print("   %-14s %4d tasks" % (L, len(ts)))

# --- disjoint pairs: tasks using A but not B, and B but not A --------------
print()
print("pairs with the largest disjoint task sets (A-only / B-only, zero overlap needed):")
cands = [L for L, ts in by_lib.items() if len(ts) >= 25]
scored = []
for A, B in itertools.combinations(cands, 2):
    a_only = by_lib[A] - by_lib[B]
    b_only = by_lib[B] - by_lib[A]
    if len(a_only) >= 10 and len(b_only) >= 10:
        scored.append((min(len(a_only), len(b_only)), A, B, len(a_only), len(b_only),
                       len(by_lib[A] & by_lib[B])))
scored.sort(reverse=True)
for s, A, B, na, nb, ov in scored[:12]:
    print("   %-12s / %-12s  A-only %3d  B-only %3d  overlap %3d" % (A, B, na, nb, ov))
print()
print("usable pairs:", len(scored))
