r"""Reply checks behind Section 5.7 of the manuscript (independent pairs), all on stored replies:

  1. the pilot re-graded with the hardened checks: which replies change grade (expected: the five
     GPT-5.5 no-context replies that passed equality-based checks without the convention);
  2. DeepSeek's failures on the inventory contract task with the contract: how many lack an import
     of the inventory module;
  3. Haiku's failures on the audit code task with the code table: how many call a language-model API;
  4. failing superset replies (AB and BA) on the two contract tasks with harm: how many apply the
     other source's transformation to the argument (cache: key normalization; inventory: SKU code).
Checks 2-4 are pattern counts over the extracted code, descriptive only.

  python harness/package2/failure_checks.py      (writes results/package2/failure_checks.json)
"""
import io
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "replication"))
import measure_blackwell as mb  # noqa: E402
import run_pairs as RP  # noqa: E402

PILOT = ROOT / "results" / "package2" / "pilot_pairs"
CONFIRM = ROOT / "results" / "package2" / "confirm_pairs"
OUT = ROOT / "results" / "package2" / "failure_checks.json"


def load(d):
    rec, grd = {}, {}
    for line in open(Path(d) / "records.jsonl", encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("type") == "receipt":
            rec[r["id"]] = r
        elif r.get("type") == "grade":
            grd[r["id"]] = r
    sched = {json.loads(l)["id"]: json.loads(l) for l in open(Path(d) / "schedule.jsonl", encoding="utf-8") if l.strip()}
    return rec, grd, sched


def code(rc):
    return mb._extract_code((rc or {}).get("raw_text") or "")


def regrade_pilot():
    rec, grd, sched = load(PILOT)
    ids = [i for i in grd if i in rec and not rec[i].get("transport_failed")]

    def one(i):
        s = sched[i]
        hard = RP.request_text(s["group"], s["task"], s["arm"])[1][1]
        return i, bool(RP.grade(rec[i].get("raw_text"), hard))

    with ThreadPoolExecutor(max_workers=8) as ex:
        hardened = dict(ex.map(one, ids))
    changed = sorted(i for i in ids if bool(grd[i]["pass"]) != hardened[i])
    return {"replies": len(ids), "changed": changed,
            "changed_published_pass_to_hardened_fail": sum(1 for i in changed if grd[i]["pass"] and not hardened[i])}


def failures(rec, grd, model, task, arm):
    return sorted(i for i, g in grd.items() if i.startswith(model + "|") and ("|%s|" % task) in i
                  and i.rsplit("|", 1)[1] == arm and not g.get("pass_hardened", g["pass"]))


def replication_gaming():
    """5. Passing replies of the randomized replication whose code shows test-gaming patterns (a str
    subclass overriding __eq__, or frame and source introspection); the original battery's checks
    compare returned values with == and were never hardened."""
    pat = re.compile(r"class\s+\w+\s*\(\s*str\s*\)[\s\S]*?__eq__|\binspect\b|_getframe|f_locals|f_back|co_consts")
    graded, hits = 0, []
    for f in sorted((ROOT / "results" / "replication" / "records").glob("*.jsonl")):
        rec = {}
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("type") == "receipt":
                rec[r["schedule_id"]] = r
            elif r.get("type") == "grade":
                graded += 1
                c = code(rec.get(r["schedule_id"]))
                if r.get("pass_published") and pat.search(c):
                    hits.append({"id": r["schedule_id"], "model": r["model"], "task": r["task"],
                                 "condition": r["condition"]})
    return {"graded": graded, "passing_replies_with_gaming_patterns": hits}


def main():
    res = {"pilot_regrade": regrade_pilot(), "replication_gaming_scan": replication_gaming()}
    rec, grd, _ = load(CONFIRM)
    imp = re.compile(r"^\s*(import\s+inventory\b|from\s+inventory\s+import\b)", re.M)
    f = failures(rec, grd, "DeepSeek-V4-Pro", "inv_book", "A")
    res["deepseek_inventory_contract_failures"] = {"failures": len(f), "without_inventory_import": sum(
        1 for i in f if not imp.search(code(rec[i])))}
    api = re.compile(r"import\s+anthropic|messages\.create|openai")
    f = failures(rec, grd, "Haiku-4.5", "audit_code", "A")
    res["haiku_audit_code_failures"] = {"failures": len(f), "calling_a_language_model_api": sum(
        1 for i in f if api.search(code(rec[i])))}
    pat = {"cache_put_ok": re.compile(r"kx7|re\.sub|\.lower\(\)"), "inv_book": re.compile(r"iv9|zfill|%\s*7|KMPRTWY")}
    for task, p in pat.items():
        fs = [i for i, g in grd.items() if ("|%s|" % task) in i and i.rsplit("|", 1)[1] in ("AB", "BA")
              and not g.get("pass_hardened", g["pass"])]
        hit = [i for i in fs if p.search(code(rec[i]))]
        res["superset_failures_%s" % task] = {"failures": len(fs), "applying_other_source_transformation": len(hit),
                                             "by_model": dict(Counter(i.split("|")[0] for i in hit))}
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: (v if k != "pilot_regrade" else {**v, "changed": v["changed"]}) for k, v in res.items()}, indent=1))


if __name__ == "__main__":
    main()
