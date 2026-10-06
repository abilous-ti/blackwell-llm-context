r"""Items for the natural-data benchmarks (HotpotQA, MuSiQue): splits and pilot sets.

Each dataset is permuted with a fixed seed after excluding every question used before (the 20
HotpotQA questions of the earlier natural-data pilot). The first DEV_SIZE questions form the
development pool: pilots and any tuning draw only from it. The rest is the confirmation pool,
which no pilot or tuning step reads; a confirmatory sample is drawn from it only after the
protocol is frozen. The split, the seed and the SHA-256 of every source file are recorded.

Candidate pools are the datasets' own: HotpotQA's distractor setting gives each question its two
supporting paragraphs among ten; MuSiQue gives twenty paragraphs with its supporting ones flagged.

  python harness/package2/qa_data.py        (main Python: needs pyarrow for the HotpotQA parquet)
"""
import hashlib
import io
import json
import random
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent.parent
ND = ROOT / "natural_data"
OUT = ND / "package2"
SEED = 20261005
DEV_SIZE = {"hotpotqa": 200, "musique": 100}
PILOT = {"hotpot_rank": 30, "hotpot_aug": 20, "musique_rank": 20, "musique_overhead": 10}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def norm(s):
    import re
    import string
    s = str(s).lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def load_hotpot():
    jl = ND / "hotpot_dev_distractor.jsonl"
    if not jl.exists():
        import pyarrow.parquet as pq
        rows = pq.read_table(ND / "hotpot_dev_distractor.parquet").to_pylist()
        with open(jl, "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                sup = sorted(set(r["supporting_facts"]["title"]))
                paras = [{"title": t, "text": "".join(s), "supporting": t in sup}
                         for t, s in zip(r["context"]["title"], r["context"]["sentences"])]
                fh.write(json.dumps({"id": r["id"], "question": r["question"], "answers": [r["answer"]],
                                     "type": r["type"], "supporting_titles": sup, "paragraphs": paras}) + "\n")
    return [json.loads(l) for l in open(jl, encoding="utf-8")]


def load_musique():
    rows = []
    for l in open(ND / "musique_ans_v1.0_dev.jsonl", encoding="utf-8"):
        r = json.loads(l)
        paras = [{"title": p["title"], "text": p["paragraph_text"], "supporting": bool(p["is_supporting"])}
                 for p in r["paragraphs"]]
        rows.append({"id": r["id"], "question": r["question"],
                     "answers": [r["answer"]] + list(r.get("answer_aliases") or []),
                     "type": r["id"].split("__")[0], "paragraphs": paras})
    return rows


def checked_distractors(item):
    """Non-supporting paragraphs that do not contain any gold answer string (normalized)."""
    golds = [norm(a) for a in item["answers"] if norm(a)]
    out = []
    for i, p in enumerate(item["paragraphs"]):
        if p["supporting"]:
            continue
        body = " " + norm(p["title"] + " " + p["text"]) + " "
        if any((" " + g + " ") in body for g in golds):
            continue
        out.append(i)
    return out


CONFIRM = {"hotpot_rank": 200, "hotpot_aug": 100, "musique_rank": 100, "musique_overhead": 20}


def confirm():
    """Draw the confirmatory items from the confirmation pools (seeded, same eligibility rules as
    the pilot). No pilot or tuning step reads these items; models see them only after the freeze."""
    data = {"hotpotqa": load_hotpot(), "musique": load_musique()}
    out = []
    for ds, rows in data.items():
        by_id = {r["id"]: r for r in rows}
        conf = [l.strip() for l in open(OUT / ("confirmation_%s.txt" % ds), encoding="utf-8") if l.strip()]
        rng = random.Random(SEED + 1)
        rng.shuffle(conf)
        pos = 0

        def take(role, n, ok):
            nonlocal pos
            got = 0
            while got < n and pos < len(conf):
                r = by_id[conf[pos]]
                pos += 1
                if ok(r):
                    out.append(dict(r, dataset=ds, role=role))
                    got += 1
        if ds == "hotpotqa":
            full = lambda r: len(r["paragraphs"]) == 10 and sum(p["supporting"] for p in r["paragraphs"]) == 2
            take("hotpot_rank", CONFIRM["hotpot_rank"], full)
            take("hotpot_aug", CONFIRM["hotpot_aug"], lambda r: full(r) and len(checked_distractors(r)) >= 2)
        else:
            full = lambda r: len(r["paragraphs"]) == 20
            take("musique_rank", CONFIRM["musique_rank"], full)
            take("musique_overhead", CONFIRM["musique_overhead"], full)
    for it in out:
        if it["role"] == "hotpot_aug":
            it["augment_distractors"] = checked_distractors(it)[:2]
    with open(OUT / "items_confirm.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for it in out:
            fh.write(json.dumps(it) + "\n")
    print("confirmatory items:", {k: sum(1 for i in out if i["role"] == k) for k in CONFIRM})


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        return confirm()
    OUT.mkdir(parents=True, exist_ok=True)
    stage1 = json.load(open(ND / "stage1" / "sample.json", encoding="utf-8"))
    excluded = {"hotpotqa": sorted(x["id"] for x in stage1["hotpotqa"]), "musique": []}
    data = {"hotpotqa": load_hotpot(), "musique": load_musique()}
    splits, pilot = {}, []
    for ds, rows in data.items():
        elig = [r for r in rows if r["id"] not in set(excluded[ds])]
        ids = [r["id"] for r in elig]
        random.Random(SEED).shuffle(ids)
        dev, conf = ids[:DEV_SIZE[ds]], ids[DEV_SIZE[ds]:]
        splits[ds] = {"seed": SEED, "excluded": excluded[ds], "dev": dev, "confirmation_size": len(conf),
                      "confirmation_sha256": hashlib.sha256("\n".join(conf).encode()).hexdigest()}
        (OUT / ("confirmation_%s.txt" % ds)).write_text("\n".join(conf) + "\n", encoding="utf-8")
        by_id = {r["id"]: r for r in rows}
        pos = 0

        def take(role, n, ok):
            nonlocal pos
            got = 0
            while got < n and pos < len(dev):
                r = by_id[dev[pos]]
                pos += 1
                if ok(r):
                    pilot.append(dict(r, dataset=ds, role=role))
                    got += 1
        if ds == "hotpotqa":
            full = lambda r: len(r["paragraphs"]) == 10 and sum(p["supporting"] for p in r["paragraphs"]) == 2
            take("hotpot_rank", PILOT["hotpot_rank"], full)
            take("hotpot_aug", PILOT["hotpot_aug"], lambda r: full(r) and len(checked_distractors(r)) >= 2)
        else:
            full = lambda r: len(r["paragraphs"]) == 20
            take("musique_rank", PILOT["musique_rank"], full)
            take("musique_overhead", PILOT["musique_overhead"], full)
    for it in pilot:
        if it["role"] == "hotpot_aug":
            it["augment_distractors"] = checked_distractors(it)[:2]
    with open(OUT / "items_pilot.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for it in pilot:
            fh.write(json.dumps(it) + "\n")
    meta = {"sources": {"hotpot_dev_distractor.parquet": sha(ND / "hotpot_dev_distractor.parquet"),
                        "musique_ans_v1.0_dev.jsonl": sha(ND / "musique_ans_v1.0_dev.jsonl")},
            "splits": splits, "pilot_counts": {k: sum(1 for i in pilot if i["role"] == k) for k in PILOT}}
    json.dump(meta, open(OUT / "splits.json", "w", encoding="utf-8"), indent=1)
    print("dev pools: %s; confirmation pools: %s" % (
        {k: len(v["dev"]) for k, v in splits.items()}, {k: v["confirmation_size"] for k, v in splits.items()}))
    print("pilot items:", meta["pilot_counts"])


if __name__ == "__main__":
    main()
