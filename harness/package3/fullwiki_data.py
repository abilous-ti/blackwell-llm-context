r"""Package 3 data: the HotpotQA fullwiki validation file -> the confirmatory sample, the smoke
items, the annotation-defined subgroup and BM25's document frequencies (PROTOCOL_FULLWIKI.md,
Sections 2-3).

  python harness/package3/fullwiki_data.py --check         download check (size, SHA-256, SHA256SUMS.txt)
  python harness/package3/fullwiki_data.py                 build natural_data/package3/{sample.json,
                                                           items_confirm.jsonl, items_smoke.jsonl,
                                                           idf_fullwiki.json}
  python harness/package3/fullwiki_data.py --verify-draw   recompute everything in memory and compare
                                                           with those files (writes nothing)

Main Python (pyarrow reads the parquet). In this setting each question's context paragraphs are the
ones HotpotQA's own retrieval system returned; the gold supporting paragraphs are not guaranteed to
be among them. They are kept exactly as released: no gold paragraph is inserted and nothing is
reordered (the file order is input order o0, as in package 2). A candidate is 'supporting' when its
title is one of the question's supporting_facts titles; the subgroup is decided from those titles
alone, never from a model output. The build is refused once the package-3 freeze exists.
"""
import hashlib
import io
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True          # never write bytecode next to package 2's modules
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "package2"))
import rank_local as RL  # noqa: E402  (BM25's tokenizer and passage format; no model is loaded)

ND = ROOT / "natural_data"
P2 = ND / "package2"
OUT = ND / "package3"
SRC = ND / "hotpot_dev_fullwiki.parquet"
SRC_URL = ("https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/fullwiki/"
           "validation-00000-of-00001.parquet")
SRC_BYTES = 28041820
SRC_SHA256 = "78933c0a31a5f7b420d4effdf4cd4eed573b28c6a3da6179dcf7a02b39e51d03"
SEED = 20261007
N_CONFIRM = 300
N_SMOKE = 10
N_CANDIDATES = 10
N_SUPPORTING = 2
FREEZE = ROOT / "results" / "package3" / "FREEZE_fullwiki.json"
HEX24 = re.compile(rb"(?<![0-9a-f])[0-9a-f]{24}(?![0-9a-f])")
# Files whose HotpotQA ids are not uses of a question: the source datasets, package 2's list of its
# never-read confirmation pool (and any copy of it, matched by name), and this package's own outputs.
SCAN_SKIP_FILES = {"natural_data/hotpot_dev_fullwiki.parquet", "natural_data/hotpot_dev_distractor.parquet",
                   "natural_data/hotpot_dev_distractor.jsonl"}
SCAN_SKIP_NAMES = {"confirmation_hotpotqa.txt", "confirmation_musique.txt"}
SCAN_SKIP_DIRS = (".git/", "natural_data/package3/", "results/package3/")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_download():
    """Problems with the downloaded file (empty list = size, SHA-256 and checksum line correct)."""
    if not SRC.exists():
        return ["missing %s (download %s)" % (SRC.relative_to(ROOT).as_posix(), SRC_URL)]
    problems = []
    if SRC.stat().st_size != SRC_BYTES:
        problems.append("size %d bytes, expected %d" % (SRC.stat().st_size, SRC_BYTES))
    h = sha(SRC)
    if h != SRC_SHA256:
        problems.append("SHA-256 %s, expected %s" % (h, SRC_SHA256))
    line = "%s *%s" % (SRC_SHA256, SRC.name)
    if line not in (ND / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        problems.append("natural_data/SHA256SUMS.txt lacks the line '%s'" % line)
    return problems


def convert(r):
    """Package 2's conversion (qa_data.load_hotpot), plus HotpotQA's level field."""
    sup = sorted(set(r["supporting_facts"]["title"]))
    paras = [{"title": t, "text": "".join(s), "supporting": t in sup}
             for t, s in zip(r["context"]["title"], r["context"]["sentences"])]
    return {"id": r["id"], "question": r["question"], "answers": [r["answer"]], "type": r["type"],
            "level": r["level"], "supporting_titles": sup, "paragraphs": paras}


def load():
    import pyarrow.parquet as pq
    return [convert(r) for r in pq.read_table(SRC).to_pylist()]


def eligible(it):
    """Annotation and pool size only (never retrieval success): exactly ten released candidates and
    two distinct supporting titles, mirroring package 2's eligibility for its ranking items."""
    return len(it["paragraphs"]) == N_CANDIDATES and len(it["supporting_titles"]) == N_SUPPORTING


def used_ids(valid):
    """Every HotpotQA question used before, by id: the listed sources, then a byte scan of the
    repository for any other validation id (the dev questions are the same in both settings)."""
    def jl(p):
        return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    s1 = json.load(open(ND / "stage1" / "sample.json", encoding="utf-8"))
    splits = json.load(open(P2 / "splits.json", encoding="utf-8"))["splits"]["hotpotqa"]
    s2 = json.load(open(ND / "stage2" / "items.json", encoding="utf-8"))
    s2_keys = sorted({x["id"].split("-")[0] for x in s2 if x["dataset"] == "hotpotqa"})
    sources = {
        "natural_data/package2/items_confirm.jsonl (ranking and augmentation items)":
            [x["id"] for x in jl(P2 / "items_confirm.jsonl") if x["dataset"] == "hotpotqa"],
        "natural_data/package2/items_pilot.jsonl (ranking and augmentation items)":
            [x["id"] for x in jl(P2 / "items_pilot.jsonl") if x["dataset"] == "hotpotqa"],
        "natural_data/package2/splits.json (development pool)": splits["dev"],
        "natural_data/package2/splits.json (excluded: the stage-1 sample)": splits["excluded"],
        "natural_data/stage1/sample.json": [x["id"] for x in s1["hotpotqa"]],
        # stage-2 items are labelled Hkk = the kk-th stage-1 HotpotQA question (stage2_pilot.py)
        "natural_data/stage2/items.json (Hkk = k-th stage-1 question)":
            [s1["hotpotqa"][int(k[1:])]["id"] for k in s2_keys],
    }
    explicit = set().union(*map(set, sources.values()))
    not_valid = sorted(explicit - valid)
    if not_valid:
        raise SystemExit("listed ids not in the validation file: %s" % not_valid[:5])
    hits, scanned, unreadable = {}, 0, []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(SCAN_SKIP_DIRS) or rel in SCAN_SKIP_FILES or p.name in SCAN_SKIP_NAMES or not p.is_file():
            continue
        try:
            data = p.read_bytes()
        except OSError:
            unreadable.append(rel)
            continue
        scanned += 1
        for m in set(HEX24.findall(data)):
            s = m.decode("ascii")
            if s in valid:
                hits.setdefault(s, []).append(rel)
    per_file = Counter(f for fs in hits.values() for f in fs)
    beyond = sorted(set(hits) - explicit)
    report = {"sources": {k: len(set(v)) for k, v in sources.items()},
              "explicit_union": len(explicit),
              "scan": {"files_scanned": scanned, "unreadable": unreadable,
                       "skipped": sorted(SCAN_SKIP_FILES) + ["any file named " + n for n in sorted(SCAN_SKIP_NAMES)]
                                  + list(SCAN_SKIP_DIRS),
                       "validation_ids_found": len(hits), "files_with_validation_ids": dict(sorted(per_file.items())),
                       "ids_beyond_listed_sources": beyond,
                       "files_with_ids_beyond_listed_sources": sorted({f for i in beyond for f in hits[i]})},
              "excluded_total": len(explicit | set(hits))}
    return explicit | set(hits), report


def draw(items, excluded):
    """Non-excluded ids in file order, shuffled once with SEED; the first N_CONFIRM eligible ids are
    the confirmatory sample, the next N_SMOKE eligible ids the smoke items."""
    by_id = {it["id"]: it for it in items}
    pool = [it["id"] for it in items if it["id"] not in excluded]
    random.Random(SEED).shuffle(pool)
    confirm, smoke, skipped = [], [], []
    for i in pool:
        if len(smoke) == N_SMOKE:
            break
        if not eligible(by_id[i]):
            skipped.append(i)
            continue
        (confirm if len(confirm) < N_CONFIRM else smoke).append(by_id[i])
    return confirm, smoke, skipped, pool


def annotate(it, role):
    k = sum(p["supporting"] for p in it["paragraphs"])
    return dict(it, dataset="hotpotqa", setting="fullwiki", role=role, supporting_in_pool=k,
                group="sufficient" if k == len(it["supporting_titles"]) else "complement")


def doc_freqs(items, vocab):
    """BM25 document frequencies over every paragraph of the fullwiki file, counted as
    rank_local.idf_table counts them (each paragraph once per question it appears in), kept for the
    query vocabulary: bm25_scores reads the IDF of query tokens only, so this is exact."""
    df, n = Counter(), 0
    for it in items:
        for p in it["paragraphs"]:
            df.update(set(RL.toks(RL.passage(p))) & vocab)
            n += 1
    return n, df


def text_check(sample):
    """Descriptive: a supporting candidate's text against the gold paragraph of the distractor file."""
    want = {it["id"] for it in sample}
    gold = {}
    for line in open(ND / "hotpot_dev_distractor.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r["id"] in want:
            gold[r["id"]] = {p["title"]: p["text"] for p in r["paragraphs"] if p["supporting"]}
    same = nbsp = diff = 0
    for it in sample:
        for p in it["paragraphs"]:
            if p["supporting"]:
                g = gold.get(it["id"], {}).get(p["title"])
                if g == p["text"]:
                    same += 1
                elif g is not None and g == p["text"].replace("\xa0", " "):
                    nbsp += 1
                else:
                    diff += 1
    return {"supporting_candidates": same + nbsp + diff, "identical_to_distractor_gold_text": same,
            "identical_except_no_break_spaces": nbsp, "different": diff,
            "note": "the candidates are used as released, no-break spaces (U+00A0) included"}


def jsonl_text(rows):
    return "".join(json.dumps(r) + "\n" for r in rows)


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:      # LF, as the repository stores text
        fh.write(text)


def build():
    """The whole draw, in memory: (files to write, sample record)."""
    items = load()
    valid = {it["id"] for it in items}
    excluded, exrep = used_ids(valid)
    confirm, smoke, skipped, pool = draw(items, excluded)
    if len(confirm) < N_CONFIRM or len(smoke) < N_SMOKE:
        raise SystemExit("pool too small")
    confirm = [annotate(it, "fullwiki_rank") for it in confirm]
    smoke = [annotate(it, "fullwiki_smoke") for it in smoke]
    vocab = set().union(*(set(RL.toks(it["question"])) for it in confirm + smoke))
    n_par, df = doc_freqs(items, vocab)
    idf = {"source": SRC.name, "source_sha256": SRC_SHA256, "questions": len(items), "paragraphs": n_par,
           "counting": "every paragraph of the file, once per question it appears in (rank_local.idf_table)",
           "tokens": "rank_local.toks of 'title. text' (rank_local.passage)",
           "idf": "log(1 + (paragraphs - df + 0.5) / (df + 0.5)), rank_local.idf_table's formula",
           "vocabulary": "tokens of the confirmatory and smoke questions that occur in some paragraph "
                         "(bm25_scores reads no other IDF; a token absent here has IDF 0, as in rank_local)",
           "df": dict(sorted(df.items()))}
    in_pool = Counter(it["supporting_in_pool"] for it in confirm)
    elig_all = sum(eligible(it) for it in items)
    elig_pool = sum(eligible(it) for it in items if it["id"] not in excluded)
    sample = {
        "source": {"file": "natural_data/" + SRC.name, "url": SRC_URL, "bytes": SRC_BYTES, "sha256": SRC_SHA256,
                   "license": "CC BY-SA 4.0 (HotpotQA)"},
        "seed": SEED,
        "draw": "non-excluded ids in file order, shuffled once with random.Random(seed); the first %d eligible "
                "ids form the confirmatory sample, the next %d eligible ids the smoke items" % (N_CONFIRM, N_SMOKE),
        "eligibility": "exactly %d released candidates and %d distinct supporting titles (annotation and pool "
                       "size only)" % (N_CANDIDATES, N_SUPPORTING),
        "subgroup": "sufficient = every supporting title is among the released candidates; complement = otherwise",
        "counts": {
            "questions": len(items),
            "candidates_per_question": dict(sorted(Counter(len(it["paragraphs"]) for it in items).items())),
            "supporting_titles_per_question": dict(sorted(Counter(len(it["supporting_titles"]) for it in items).items())),
            "eligible_all": elig_all, "ineligible_all": len(items) - elig_all,
            "excluded": len(excluded), "pool_after_exclusion": len(pool),
            "eligible_after_exclusion": elig_pool, "ineligible_after_exclusion": len(pool) - elig_pool,
            "ineligible_skipped_in_draw": len(skipped), "positions_read_in_draw": len(confirm) + len(smoke) + len(skipped),
            "confirm": len(confirm), "smoke": len(smoke),
            "confirm_sufficient": sum(it["group"] == "sufficient" for it in confirm),
            "confirm_complement": sum(it["group"] == "complement" for it in confirm),
            "confirm_supporting_in_pool": {str(k): in_pool[k] for k in sorted(in_pool)},
            "confirm_types": dict(Counter(it["type"] for it in confirm)),
            "all_sufficient": sum(1 for it in items if eligible(it) and
                                  sum(p["supporting"] for p in it["paragraphs"]) == N_SUPPORTING),
        },
        "exclusion": exrep,
        "supporting_text_check": text_check(confirm + smoke),
        "bm25_idf": {"paragraphs": n_par, "query_tokens": len(vocab), "tokens_with_df": len(df)},
        "confirm": [{"id": it["id"], "group": it["group"], "supporting_in_pool": it["supporting_in_pool"],
                     "candidate_titles": [p["title"] for p in it["paragraphs"]]} for it in confirm],
        "smoke": [{"id": it["id"], "group": it["group"], "supporting_in_pool": it["supporting_in_pool"],
                   "candidate_titles": [p["title"] for p in it["paragraphs"]]} for it in smoke],
        "ineligible_skipped_ids": skipped,
    }
    files = {"items_confirm.jsonl": jsonl_text(confirm), "items_smoke.jsonl": jsonl_text(smoke),
             "idf_fullwiki.json": json.dumps(idf, indent=0) + "\n"}
    return files, sample


def report(sample):
    c, ex = sample["counts"], sample["exclusion"]
    print("questions %d; eligible %d (ineligible %d: %s candidates)" % (
        c["questions"], c["eligible_all"], c["ineligible_all"],
        {k: v for k, v in c["candidates_per_question"].items() if int(k) != N_CANDIDATES}))
    print("excluded as used before: %d (listed sources %d; repository scan of %d files found %d validation ids, "
          "%d beyond the sources)" % (c["excluded"], ex["explicit_union"], ex["scan"]["files_scanned"],
                                      ex["scan"]["validation_ids_found"], len(ex["scan"]["ids_beyond_listed_sources"])))
    if ex["scan"]["unreadable"]:
        print("WARNING: %d files could not be read by the id scan: %s" % (
            len(ex["scan"]["unreadable"]), ex["scan"]["unreadable"][:10]))
    print("pool after exclusion %d (eligible %d); draw read %d positions, skipped %d ineligible" % (
        c["pool_after_exclusion"], c["eligible_after_exclusion"], c["positions_read_in_draw"], c["ineligible_skipped_in_draw"]))
    print("confirmatory %d: sufficient %d, complement %d (supporting in pool: %s); smoke %d" % (
        c["confirm"], c["confirm_sufficient"], c["confirm_complement"], c["confirm_supporting_in_pool"], c["smoke"]))
    print("supporting-text check: %s" % sample["supporting_text_check"])
    print("BM25 IDF: %(paragraphs)d paragraphs, %(query_tokens)d query tokens (%(tokens_with_df)d with df > 0)" % sample["bm25_idf"])


def verify_draw():
    """Recompute the draw and compare it with the files on disk; nothing is written."""
    files, sample = build()
    report(sample)
    problems = []
    for name, text in files.items():
        p = OUT / name
        if not p.exists():
            problems.append("missing %s" % name)
        elif p.read_text(encoding="utf-8") != text:
            problems.append("%s differs" % name)
    disk = json.loads((OUT / "sample.json").read_text(encoding="utf-8"))
    for key in ("seed", "counts", "confirm", "smoke", "ineligible_skipped_ids", "supporting_text_check", "bm25_idf"):
        if json.loads(json.dumps(sample[key])) != disk.get(key):
            problems.append("sample.json differs in '%s'" % key)
    return problems


def main():
    problems = check_download()
    if "--check" in sys.argv:
        print("download check: " + ("OK (%d bytes, SHA-256 %s, listed in SHA256SUMS.txt)" % (SRC_BYTES, SRC_SHA256)
                                    if not problems else "; ".join(problems)))
        return 1 if problems else 0
    if problems:
        raise SystemExit("download check failed: " + "; ".join(problems))
    if "--verify-draw" in sys.argv:
        problems = verify_draw()
        print("draw verified: items, IDF table and sample reproduced exactly" if not problems
              else "draw NOT reproduced: " + "; ".join(problems))
        return 1 if problems else 0
    if FREEZE.exists():
        raise SystemExit("package 3 is frozen (%s): its items are never regenerated" % FREEZE.name)
    files, sample = build()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        write_text(OUT / name, text)
    write_text(OUT / "sample.json", json.dumps(sample, indent=1) + "\n")
    report(sample)
    return 0


if __name__ == "__main__":
    sys.exit(main())
