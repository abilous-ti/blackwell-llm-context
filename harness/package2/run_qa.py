r"""Pilot runner for the natural-data benchmarks: rankers, transfer, augmentation, overhead.

Phase 1 (ranking requests)
  rankgpt   RankGPT-style listwise ranking (Sun et al., 2023) of each ranking item's whole pool by
            the ranking model (Haiku), in two input orders: the dataset's order (o0, the one used
            for answering) and a seeded shuffle (o1, for stability only).
  overhead  the same prompt on the overhead items at 5, 10 and 20 candidates (all supporting
            paragraphs plus seeded distractors), two input orders, for each overhead model:
            latency, tokens, extra attempts, parse validity, ranking stability.
Phase 2 (answers), for each answer model
  ranking items     none | full (whole pool) | bm25 | mmr | bge | e5 | minilm | rankgpt, the
                    ranked conditions at one matched budget: the top K paragraphs of each ranker
                    (K = 2 for HotpotQA, 4 for MuSiQue), presented in rank order;
  augmentation      none | gold (the supporting paragraphs, dataset order) | gold+dist (two
  items             checked distractors appended) | dist+gold (prepended); a diagnostic sample,
                    selected with the supporting-fact annotations.

Answers are scored with the official HotpotQA exact match and F1 (maximum over MuSiQue's
aliases). Evidence retrieval is reported separately from answer quality. Requests go through the
replication transport with the same per-model endpoints and keys; keys are never printed.

This is a PILOT on development items only (natural_data/package2/splits.json).

  python harness/package2/run_qa.py --mock
  python harness/package2/run_qa.py                 (needs BW_* for Haiku, GPT-5.5, DeepSeek)
  python harness/package2/run_qa.py --summary
"""
import argparse
import hashlib
import io
import json
import os
import random
import re
import string
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "replication"))
import transport  # noqa: E402

DESIGN = json.load(open(HERE.parent / "replication" / "design.json", encoding="utf-8"))
MODELS = {m["label"]: m for m in DESIGN["models"]}
ND = ROOT / "natural_data" / "package2"
ANSWER_MODELS = ("Haiku-4.5", "GPT-5.5", "DeepSeek-V4-Pro")
RANK_MODEL = "Haiku-4.5"
OVERHEAD_MODELS = ("Haiku-4.5", "GPT-5.5")
BUDGET = {"hotpotqa": 2, "musique": 4}
RANKED = ("bm25", "mmr", "bge", "e5", "minilm", "rankgpt")
SIZES = (5, 10, 20)
SEED = 20261005
SETS = {"pilot": {"items": "items_pilot.jsonl", "rankings": "rankings_local_pilot.jsonl", "out": "pilot_qa"},
        "confirm": {"items": "items_confirm.jsonl", "rankings": "rankings_local_confirm.jsonl", "out": "confirm_qa"}}
SET = dict(SETS["pilot"])

RANK_PROMPT = ("I will provide you with {n} passages, each indicated by a numerical identifier []. "
               "Rank the passages based on their relevance to the query: {q}\n\n{passages}\n\n"
               "Search Query: {q}\nRank the {n} passages above based on their relevance to the search "
               "query. List them in descending order using identifiers, the most relevant first. The "
               "output format should be [] > [], e.g., [2] > [1]. Only respond with the ranking, "
               "without any explanation.")
# Amended after the pilot (5 October): Haiku reasoned step by step on multi-hop questions despite
# an instruction to answer only, so the first line was not the answer. Reasoning is now allowed and
# the answer is read from a required final line.
ANSWER_CTX = ("Answer the question using the context passages. You may reason briefly first. End your "
              "reply with one final line of the form 'Answer: <answer>', where <answer> is only a short "
              "phrase, name, number, date, or yes/no.\n\nContext:\n{ctx}\n\nQuestion: {q}")
ANSWER_NONE = ("Answer the question. You may reason briefly first. End your reply with one final line of "
               "the form 'Answer: <answer>', where <answer> is only a short phrase, name, number, date, "
               "or yes/no.\n\nQuestion: {q}")


# ---- scoring: the official HotpotQA definitions ---------------------------------------------
def normalize_answer(s):
    s = str(s).lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def f1_score(pred, gold):
    p, g = normalize_answer(pred), normalize_answer(gold)
    if (p in ("yes", "no", "noanswer") or g in ("yes", "no", "noanswer")) and p != g:
        return 0.0
    pt, gt = p.split(), g.split()
    same = sum((Counter(pt) & Counter(gt)).values())
    if same == 0:
        return 0.0
    prec, rec = same / len(pt), same / len(gt)
    return 2 * prec * rec / (prec + rec)


def clean_answer(text):
    """The text of the last 'Answer:' line; without one, the last non-empty line."""
    if not text:
        return ""
    lines = [l.strip() for l in str(text).strip().splitlines() if l.strip()]
    tagged = [m.group(1) for m in (re.search(r"(?:final answer|answer)\s*[:\-]\s*(.*)$", l.strip("*# "), re.I)
                                   for l in lines) if m and m.group(1).strip()]
    a = tagged[-1] if tagged else (lines[-1] if lines else "")
    return a.strip().strip("*").strip().strip('"').strip("'").rstrip(".").strip()


def score(pred, golds):
    a = clean_answer(pred)
    em = max(float(normalize_answer(a) == normalize_answer(g)) for g in golds)
    f1 = max(f1_score(a, g) for g in golds)
    contains = max(float(bool(normalize_answer(g)) and normalize_answer(g) in normalize_answer(pred or ""))
                   for g in golds)
    return em, f1, contains


# ---- requests --------------------------------------------------------------------------------
def passage(p):
    return "%s: %s" % (p["title"], p["text"])


def parse_ranking(text, n):
    ids = [int(x) for x in re.findall(r"\[(\d+)\]", text or "")]
    seen, order = set(), []
    dup = 0
    for i in ids:
        if 1 <= i <= n:
            if i - 1 in seen:
                dup += 1
                continue
            seen.add(i - 1)
            order.append(i - 1)
    valid = len(order)
    order += [i for i in range(n) if i not in seen]          # RankGPT convention: append the rest
    return order, {"returned": valid, "duplicates": dup, "complete": valid == n}


def subset_pool(item, size, rng):
    sup = [i for i, p in enumerate(item["paragraphs"]) if p["supporting"]]
    rest = [i for i, p in enumerate(item["paragraphs"]) if not p["supporting"]]
    rng.shuffle(rest)
    keep = sorted(sup + rest[:max(0, size - len(sup))])
    return keep[:size] if size < len(item["paragraphs"]) else list(range(len(item["paragraphs"])))


def build_rank_requests(items):
    reqs = []
    for it in items:
        if it["role"] in ("hotpot_rank", "musique_rank"):
            pool = list(range(len(it["paragraphs"])))
            orders = [pool, pool[:]]
            random.Random("%s|%s" % (SEED, it["id"])).shuffle(orders[1])
            for j, o in enumerate(orders):
                reqs.append({"id": "rank|%s|%s|o%d" % (RANK_MODEL, it["id"], j), "kind": "rank",
                             "model": RANK_MODEL, "item": it["id"], "pool": o, "order_idx": j, "size": len(o)})
        if it["role"] == "musique_overhead":
            for size in SIZES:
                keep = subset_pool(it, size, random.Random("%s|%s|%d" % (SEED, it["id"], size)))
                orders = [keep, keep[:]]
                random.Random("%s|%s|%d|o1" % (SEED, it["id"], size)).shuffle(orders[1])
                for m in OVERHEAD_MODELS:
                    for j, o in enumerate(orders):
                        reqs.append({"id": "over|%s|%s|%d|o%d" % (m, it["id"], size, j), "kind": "overhead",
                                     "model": m, "item": it["id"], "pool": o, "order_idx": j, "size": size})
    return reqs


def rank_prompt(it, pool):
    ps = "\n".join("[%d] %s" % (k + 1, passage(it["paragraphs"][i])) for k, i in enumerate(pool))
    return RANK_PROMPT.format(n=len(pool), q=it["question"], passages=ps)


def answer_conditions(it):
    if it["role"] in ("hotpot_rank", "musique_rank"):
        return ("none", "full") + RANKED
    if it["role"] == "hotpot_aug":
        return ("none", "gold", "gold+dist", "dist+gold")
    return ()


def context_for(it, cond, rankings):
    P = it["paragraphs"]
    if cond == "none":
        return None
    if cond == "full":
        idx = list(range(len(P)))
    elif cond in RANKED:
        idx = rankings[(it["id"], cond)][:BUDGET[it["dataset"]]]
    else:
        gold = [i for i, p in enumerate(P) if p["supporting"]]
        dist = it["augment_distractors"]
        idx = {"gold": gold, "gold+dist": gold + dist, "dist+gold": dist + gold}[cond]
    return "\n".join("[%d] %s" % (k + 1, passage(P[i])) for k, i in enumerate(idx))


def answer_prompt(it, cond, rankings):
    ctx = context_for(it, cond, rankings)
    return ANSWER_NONE.format(q=it["question"]) if ctx is None else ANSWER_CTX.format(ctx=ctx, q=it["question"])


# ---- records ---------------------------------------------------------------------------------
def load_records(path):
    st = {"issued": {}, "receipt": {}}
    if path.exists():
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("type") in st:
                st[r["type"]][r["id"]] = r
    return st


def local_rankings():
    out = {}
    for line in open(ND / SET["rankings"], encoding="utf-8"):
        r = json.loads(line)
        out[(r["id"], r["ranker"])] = r["order"]
    return out


def rankgpt_rankings(st, items_by_id):
    out = {}
    for i, rc in st["receipt"].items():
        if i.startswith("rank|") and i.endswith("|o0") and not rc.get("transport_failed"):
            it = items_by_id[rc["item"]]
            order, _ = parse_ranking(rc.get("raw_text"), len(rc["pool"]))
            out[(it["id"], "rankgpt")] = [rc["pool"][k] for k in order]
    return out


def mock_text(req, items_by_id):
    it = items_by_id[req["item"]]
    if req["kind"] in ("rank", "overhead"):
        pool = req["pool"]
        sup_first = sorted(range(len(pool)), key=lambda k: (not it["paragraphs"][pool[k]]["supporting"], k))
        return " > ".join("[%d]" % (k + 1) for k in sup_first)
    return it["answers"][0] if req["cond"] != "none" else "unknown"


def run(out_dir, mock=False, lanes=2, phases=("rank", "answer")):
    out_dir.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in open(ND / SET["items"], encoding="utf-8")]
    by_id = {it["id"]: it for it in items}
    rec_path = out_dir / "records.jsonl"
    st = load_records(rec_path)
    lock = threading.Lock()
    fh = open(rec_path, "a", encoding="utf-8", newline="\n")

    def write(rec):
        with lock:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def endpoint(m):
        spec = MODELS[m]
        return spec["id"], os.environ.get(spec["endpoint_env"]), os.environ.get(spec["key_env"])

    def execute(reqs):
        need = sorted({r["model"] for r in reqs})
        if not mock:
            missing = [m for m in need if not all(endpoint(m)[1:])]
            if missing:
                raise SystemExit("no endpoint or key for: %s" % ", ".join(missing))
        todo = defaultdict(list)
        for k, r in enumerate(reqs):
            if r["id"] not in st["issued"]:
                todo[(r["model"], k % lanes)].append(r)

        def worker(m, lane):
            mid, ep, key = endpoint(m)
            fails = 0
            for r in todo[(m, lane)]:
                write({"type": "issued", "id": r["id"], "utc": transport.utc_now()})
                t0 = time.perf_counter()
                if mock:
                    resp = {"text": mock_text(r, by_id), "returned_model": mid, "response_id": "mock",
                            "usage": {}, "stop_reason": "mock", "response": None, "transport_failed": False,
                            "attempts": [{"attempt": 1, "http_status": 200, "error": None}]}
                else:
                    resp = transport.post(r["prompt"], mid, ep, key)
                rec = {k: v for k, v in r.items() if k != "prompt"}
                rec.update({"type": "receipt", "wall_s": round(time.perf_counter() - t0, 3),
                            "prompt_sha256": hashlib.sha256(r["prompt"].encode("utf-8")).hexdigest(),
                            "prompt_chars": len(r["prompt"]), "requested_model": mid,
                            "returned_model": resp.get("returned_model"), "response_id": resp.get("response_id"),
                            "usage": resp.get("usage"), "stop_reason": resp.get("stop_reason"),
                            "attempts": resp.get("attempts"), "transport_failed": resp.get("transport_failed"),
                            "raw_text": resp.get("text"), "response": resp.get("response")})
                write(rec)
                fails = fails + 1 if resp.get("transport_failed") else 0
                if fails >= 3:
                    write({"type": "halt", "id": "%s|lane%d" % (m, lane), "reason": "three consecutive transport failures"})
                    return
        threads = [threading.Thread(target=worker, args=key) for key in todo]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    if "rank" in phases:
        reqs = build_rank_requests(items)
        for r in reqs:
            r["prompt"] = rank_prompt(by_id[r["item"]], r["pool"])
        execute(reqs)
        st = load_records(rec_path)
    if "answer" in phases:
        rankings = local_rankings()
        rankings.update(rankgpt_rankings(st, by_id))
        reqs = []
        for it in items:
            for cond in answer_conditions(it):
                if cond == "rankgpt" and (it["id"], "rankgpt") not in rankings:
                    continue                     # its ranking request failed: recorded, not imputed
                for m in ANSWER_MODELS:
                    reqs.append({"id": "ans|%s|%s|%s" % (m, it["id"], cond), "kind": "answer", "model": m,
                                 "item": it["id"], "cond": cond, "role": it["role"], "dataset": it["dataset"],
                                 "prompt": answer_prompt(it, cond, rankings)})
        execute(reqs)
    fh.close()
    return summary(out_dir)


# ---- summary ---------------------------------------------------------------------------------
def kendall_tau(a, b):
    pos = {x: i for i, x in enumerate(b)}
    n, s = len(a), 0
    for i in range(n):
        for j in range(i + 1, n):
            s += 1 if pos[a[i]] < pos[a[j]] else -1
    return s / (n * (n - 1) / 2) if n > 1 else 1.0


def toks(rc):
    u = rc.get("usage") or {}
    return (u.get("input_tokens", u.get("prompt_tokens")) or 0, u.get("output_tokens", u.get("completion_tokens")) or 0)


def summary(out_dir):
    items = {json.loads(l)["id"]: json.loads(l) for l in open(ND / SET["items"], encoding="utf-8")}
    st = load_records(out_dir / "records.jsonl")
    R = st["receipt"]
    L = []
    fail = sum(1 for r in R.values() if r.get("transport_failed"))
    L.append("issued %d, received %d (transport failures %d), issued without receipt %d" % (
        len(st["issued"]), len(R), fail, sum(1 for i in st["issued"] if i not in R)))
    # evidence retrieval at the matched budget, local rankers and RankGPT (o0)
    rankings = local_rankings()
    rankings.update(rankgpt_rankings(st, items))
    L.append("\nEVIDENCE RETRIEVAL at the matched budget (support recall | all supporting retrieved)")
    for ds in ("hotpotqa", "musique"):
        role = "hotpot_rank" if ds == "hotpotqa" else "musique_rank"
        row = []
        for rk in RANKED:
            v = []
            for it in items.values():
                if it["role"] != role or (it["id"], rk) not in rankings:
                    continue
                sup = {i for i, p in enumerate(it["paragraphs"]) if p["supporting"]}
                top = set(rankings[(it["id"], rk)][:BUDGET[ds]])
                v.append((len(top & sup) / len(sup), float(sup <= top)))
            if v:
                row.append("%s %.2f|%.2f (n=%d)" % (rk, sum(a for a, _ in v) / len(v), sum(b for _, b in v) / len(v), len(v)))
        L.append("  %-9s K=%d  %s" % (ds, BUDGET[ds], "   ".join(row)))
    # answers
    acc = defaultdict(list)
    for i, rc in R.items():
        if rc.get("kind") != "answer" or rc.get("transport_failed"):
            continue
        it = items[rc["item"]]
        acc[(rc["role"], rc["cond"], rc["model"])].append(score(rc.get("raw_text"), it["answers"]))
    for role, conds in (("hotpot_rank", ("none", "full") + RANKED), ("musique_rank", ("none", "full") + RANKED),
                        ("hotpot_aug", ("none", "gold", "gold+dist", "dist+gold"))):
        L.append("\nANSWERS %s: EM / F1 (n)" % role)
        L.append("  %-16s" % "model" + "".join("%17s" % c for c in conds))
        for m in ANSWER_MODELS:
            cells = []
            for c in conds:
                v = acc.get((role, c, m), [])
                cells.append("%17s" % ("%.2f/%.2f (%d)" % (sum(x[0] for x in v) / len(v), sum(x[1] for x in v) / len(v), len(v)) if v else "-"))
            L.append("  %-16s" % m + "".join(cells))
    # RankGPT parse quality and stability (ranking items)
    par, stab = [], []
    for it in items.values():
        if it["role"] not in ("hotpot_rank", "musique_rank"):
            continue
        r0, r1 = R.get("rank|%s|%s|o0" % (RANK_MODEL, it["id"])), R.get("rank|%s|%s|o1" % (RANK_MODEL, it["id"]))
        got = []
        for rc in (r0, r1):
            if rc and not rc.get("transport_failed"):
                order, info = parse_ranking(rc.get("raw_text"), len(rc["pool"]))
                par.append(info["complete"])
                got.append([rc["pool"][k] for k in order])
        if len(got) == 2:
            k = BUDGET[it["dataset"]]
            stab.append((len(set(got[0][:k]) & set(got[1][:k])) / k, kendall_tau(got[0], got[1])))
    if par:
        L.append("\nRANKGPT (ranking items): complete parses %d/%d; top-K agreement across input orders %.2f; "
                 "Kendall tau %.2f (n=%d)" % (sum(par), len(par), sum(a for a, _ in stab) / max(1, len(stab)),
                                              sum(b for _, b in stab) / max(1, len(stab)), len(stab)))
    # overhead
    L.append("\nOVERHEAD (listwise ranking by candidate count): latency s | input tok | output tok | "
             "extra attempts | complete parses | top-K agreement | support recall@K")
    for m in OVERHEAD_MODELS:
        for size in SIZES:
            rows = [rc for rc in R.values() if rc.get("kind") == "overhead" and rc["model"] == m and rc["size"] == size
                    and not rc.get("transport_failed")]
            if not rows:
                continue
            lat = sum(rc["wall_s"] for rc in rows) / len(rows)
            ti = sum(toks(rc)[0] for rc in rows) / len(rows)
            to = sum(toks(rc)[1] for rc in rows) / len(rows)
            extra = sum(len(rc.get("attempts") or []) - 1 for rc in rows)
            comp = sum(parse_ranking(rc.get("raw_text"), len(rc["pool"]))[1]["complete"] for rc in rows)
            ag, rec = [], []
            for it_id in {rc["item"] for rc in rows}:
                pair = {rc["order_idx"]: rc for rc in rows if rc["item"] == it_id}
                it = items[it_id]
                sup = {i for i, p in enumerate(it["paragraphs"]) if p["supporting"]}
                k = len(sup)
                orders = {}
                for j, rc in pair.items():
                    o, _ = parse_ranking(rc.get("raw_text"), len(rc["pool"]))
                    orders[j] = [rc["pool"][x] for x in o]
                    rec.append(len(set(orders[j][:k]) & sup) / k)
                if len(orders) == 2:
                    ag.append(len(set(orders[0][:k]) & set(orders[1][:k])) / k)
            L.append("  %-16s %2d cand.  %6.1f | %6.0f | %5.0f | %d | %d/%d | %.2f | %.2f" % (
                m, size, lat, ti, to, extra, comp, len(rows), sum(ag) / max(1, len(ag)), sum(rec) / max(1, len(rec))))
    text = "\n".join(L)
    (out_dir / "summary.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--phase", choices=("all", "rank", "answer"), default="all")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--set", choices=tuple(SETS), default="pilot",
                    help="pilot (development items) or confirm (confirmation items, after the freeze)")
    ap.add_argument("--lanes", type=int, default=2, help="concurrent requests per model")
    a = ap.parse_args()
    SET.update(SETS[a.set])
    out = Path(a.out) if a.out else ND / (SET["out"] + ("_mock" if a.mock else ""))
    if a.summary:
        summary(out)
        return
    run(out, mock=a.mock, lanes=a.lanes, phases=("rank", "answer") if a.phase == "all" else (a.phase,))


if __name__ == "__main__":
    main()
