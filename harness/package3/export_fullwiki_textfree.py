r"""Text-free public export of package 3: listwise reranking on HotpotQA's retrieved candidates
(fullwiki setting; harness/package3/PROTOCOL_FULLWIKI.md; manuscript Table tab:fullwiki).

The records (natural_data/package3/, gitignored) contain HotpotQA text (CC BY-SA 4.0) and the models'
replies, so they are not redistributed. This script writes what can be released without reproducing
any of that text, with the conventions and the helpers of package 2's export
(harness/package2/export_qa_textfree.py, imported, not copied): question and request ids, labels,
paragraph INDICES (never titles or text), every ranking as an index list, the scores computed by the
project's own scorers, missingness and transport status, resource use, and SHA-256 digests of every
prompt and of every question, title and paragraph, so that a rebuild from the public parquet can be
checked byte for byte.

  natural_data/package3/{items_confirm.jsonl, sample.json, rankings_local_confirm.jsonl,
  local_models.json, idf_fullwiki.json, confirm_fullwiki/records.jsonl, confirm_fullwiki/summary.txt}
  and results/package3/analysis_fullwiki.{json,md}  ->  results/package3/confirm_fullwiki_textfree/

Every row is built in memory first. Nothing is written unless the freeze verifies, every frozen input
matches its digest and every prompt (600 ranking, 7,200 answer) rebuilt from the exported indices
matches its recorded SHA-256 and length, so the exported selections are exactly what was sent. The
freeze itself (results/package3/FREEZE_fullwiki.json) lists every candidate title, so the authors keep
it; provenance.json records its SHA-256 and every digest it lists. Scores
and parses come from the functions the analysis used (run_qa.score, run_qa.parse_ranking).
Deterministic: no clock, no network, no model call; standard library only. Rows keep the order of the
source records. The analysis sorts by question id, so its intervals do not depend on row order; the
order of first appearance only fixes the order of the models in its answer-line line.

  python harness/package3/export_fullwiki_textfree.py

Then run the leak check and the reproduction check:
  python harness/package3/check_fullwiki_leaks.py
  python harness/package3/verify_fullwiki_textfree.py
"""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True          # never write bytecode next to package 2's modules
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "package2"))
import export_qa_textfree as X  # noqa: E402  (package 2's export helpers)
import freeze_fullwiki as FZ  # noqa: E402
import fullwiki_data as FD  # noqa: E402
import run_fullwiki as RF  # noqa: E402

Q = RF.Q
K = RF.K
P3 = RF.P3
REC_DIR = RF.SETS["confirm"]["out"]
RES3 = ROOT / "results" / "package3"
OUT = RES3 / "confirm_fullwiki_textfree"
P2_EXPORT = ROOT / "results" / "package2" / "confirm_qa_textfree"
ND2 = ROOT / "natural_data" / "package2"
INPUTS = ("natural_data/package3/items_confirm.jsonl", "natural_data/package3/sample.json",
          "natural_data/package3/rankings_local_confirm.jsonl", "natural_data/package3/local_models.json",
          "natural_data/package3/idf_fullwiki.json", "natural_data/package3/confirm_fullwiki/records.jsonl",
          "natural_data/package3/confirm_fullwiki/summary.txt")
CODE = ("harness/package3/PROTOCOL_FULLWIKI.md", "harness/package3/fullwiki_data.py",
        "harness/package3/run_fullwiki.py", "harness/package3/analyze_fullwiki.py",
        "harness/package3/freeze_fullwiki.py", "harness/package3/export_fullwiki_textfree.py",
        "harness/package2/run_qa.py", "harness/package2/analyze_qa.py", "harness/package2/rank_local.py",
        "harness/package2/export_qa_textfree.py", "harness/replication/transport.py")


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def read_records(path):
    """Every record, strictly: a damaged line or a repeated id stops the export (run_qa.load_records,
    which the analysis uses, skips damaged lines silently; both readings are compared below)."""
    st, other = {"issued": {}, "receipt": {}}, Counter()
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("type") in st:
            if r["id"] in st[r["type"]]:
                raise SystemExit("repeated %s record %s" % (r["type"], r["id"]))
            st[r["type"]][r["id"]] = r
        else:
            other[r.get("type")] += 1
    loose = Q.load_records(path)
    if any(list(loose[t]) != list(st[t]) for t in st):
        raise SystemExit("run_qa.load_records reads %s differently" % path)
    return st, other


def public_exclusions():
    """The 520 HotpotQA ids used before package 3, from package 2's public text-free export: its
    confirmatory items, development pool (which holds the pilot items) and excluded list (the
    stage-1 sample, which is also the stage-2 items)."""
    sp = json.load(open(P2_EXPORT / "splits.json", encoding="utf-8"))["datasets"]["hotpotqa"]
    ids = set(sp["excluded"]) | set(sp["dev"]) | {x["id"] for x in sp["pilot_items"] + sp["confirm_items"]}
    ids |= {x["id"] for x in jl(P2_EXPORT / "items.jsonl") if x["dataset"] == "hotpotqa"}
    return sorted(ids)


def listed_exclusions():
    """The same ids from the sources fullwiki_data.used_ids lists (natural_data, local only)."""
    p2, nd = ND2, ROOT / "natural_data"
    s1 = json.load(open(nd / "stage1" / "sample.json", encoding="utf-8"))["hotpotqa"]
    sp = json.load(open(p2 / "splits.json", encoding="utf-8"))["splits"]["hotpotqa"]
    s2 = {x["id"].split("-")[0] for x in json.load(open(nd / "stage2" / "items.json", encoding="utf-8"))
          if x["dataset"] == "hotpotqa"}
    ids = {x["id"] for f in ("items_confirm.jsonl", "items_pilot.jsonl") for x in jl(p2 / f) if x["dataset"] == "hotpotqa"}
    return sorted(ids | set(sp["dev"]) | set(sp["excluded"]) | {x["id"] for x in s1}
                  | {s1[int(k[1:])]["id"] for k in s2})


def status_fields(rc):
    """analyze_fullwiki's status of a request ('received'; 'failed_http400' when every attempt ended in
    HTTP 400, else 'failed_other'), the HTTP status of its last attempt, and for a request that failed,
    the provider's error class of its last attempt (export_qa_textfree.attempt_entry)."""
    atts = rc.get("attempts") or []
    last = X.attempt_entry(atts[-1]) if atts else None
    failed = bool(rc.get("transport_failed"))
    return {"status": "failed_" + RF.failure_class(rc) if failed else "received",
            "http_status": last["http_status"] if last else None,
            "error_class": last["error_class"] if failed and last else None}


def request_row(row, rc, issued):
    """package 2's request fields (export_qa_textfree.request_fields), the status fields, then the
    prompt's digest and length."""
    rf = X.request_fields(rc, issued[rc["id"]]["utc"], rc["wall_s"])
    sha = rf.pop("prompt_sha256")
    row.update(rf)
    row.update(status_fields(rc))
    row["prompt_sha256"] = sha
    row["prompt_chars"] = rc["prompt_chars"]
    return row


def df_digest(df):
    """SHA-256 of BM25's document frequencies in a canonical form (sorted keys, no spaces)."""
    return X.sha_text(json.dumps(df, sort_keys=True, separators=(",", ":")))


def build():
    problems = FZ.check()
    if problems:
        raise SystemExit("the package-3 freeze does not verify: " + "; ".join(problems))
    fz = json.loads(FZ.FREEZE.read_text(encoding="utf-8"))
    items = RF.load_items("confirm")
    by_id = {it["id"]: it for it in items}
    st, other = read_records(REC_DIR / "records.jsonl")
    R, issued = st["receipt"], st["issued"]
    if set(issued) != set(R):
        raise SystemExit("issued and received requests differ; the export assumes every request has a receipt")
    if other:
        raise SystemExit("records of other types (%s): extend the export" % dict(other))
    n_prompts = 0

    # items --------------------------------------------------------------------------------------
    item_rows = []
    for it in items:
        sup = [i for i, p in enumerate(it["paragraphs"]) if p["supporting"]]
        assert it["setting"] == "fullwiki" and it["role"] == "fullwiki_rank" and FD.eligible(it), it["id"]
        assert len(sup) == it["supporting_in_pool"] and it["group"] == (
            "sufficient" if len(sup) == len(it["supporting_titles"]) else "complement"), it["id"]
        assert sorted(it["paragraphs"][i]["title"] for i in sup) == sorted(
            t for t in it["supporting_titles"] if t in {p["title"] for p in it["paragraphs"]}), it["id"]
        item_rows.append({
            "id": it["id"], "dataset": it["dataset"], "setting": it["setting"], "role": it["role"],
            "type": it["type"], "level": it["level"], "eligible": FD.eligible(it),
            "n_candidates": len(it["paragraphs"]), "n_supporting_titles": len(it["supporting_titles"]),
            "supporting": sup, "supporting_in_pool": it["supporting_in_pool"], "group": it["group"],
            "n_gold_answers": len(it["answers"]), "question_sha256": X.sha_text(it["question"]),
            "supporting_title_sha256": [X.sha_text(t) for t in it["supporting_titles"]],
            "title_sha256": [X.sha_text(p["title"]) for p in it["paragraphs"]],
            "text_sha256": [X.sha_text(p["text"]) for p in it["paragraphs"]]})

    # sample: the draw, without titles ----------------------------------------------------------
    smp = json.load(open(P3 / "sample.json", encoding="utf-8"))
    if [x["id"] for x in smp["confirm"]] != [it["id"] for it in items]:
        raise SystemExit("sample.json and items_confirm.jsonl list different questions")
    excluded = public_exclusions()
    ex = smp["exclusion"]
    if excluded != listed_exclusions() or not (len(excluded) == smp["counts"]["excluded"] == ex["explicit_union"]
                                               == ex["excluded_total"]) or ex["scan"]["ids_beyond_listed_sources"]:
        raise SystemExit("the exclusions derived from package 2's export differ from the frozen sample's")
    if set(excluded) & {x["id"] for x in smp["confirm"] + smp["smoke"]}:
        raise SystemExit("an excluded id was drawn")
    idf = json.load(open(P3 / "idf_fullwiki.json", encoding="utf-8"))
    assert idf["source_sha256"] == FD.SRC_SHA256 and idf["paragraphs"] == smp["bm25_idf"]["paragraphs"]
    assert len(idf["df"]) == smp["bm25_idf"]["tokens_with_df"]
    sample = {
        "source": {"file": FD.SRC.name, "url": FD.SRC_URL, "bytes": FD.SRC_BYTES, "sha256": FD.SRC_SHA256,
                   "license": "CC-BY-SA-4.0"},
        "seed": FD.SEED,
        "eligibility": {"n_candidates": FD.N_CANDIDATES, "n_supporting_titles": FD.N_SUPPORTING},
        "excluded": {"count": len(excluded), "ids_sha256": X.sha_text("\n".join(excluded)),
                     "derived_from": {"file": "results/package2/confirm_qa_textfree/splits.json",
                                      "keys": ["datasets.hotpotqa.excluded", "datasets.hotpotqa.dev",
                                               "datasets.hotpotqa.pilot_items", "datasets.hotpotqa.confirm_items"]},
                     "ids": excluded},
        "counts": smp["counts"],
        "supporting_text_check": {k: v for k, v in smp["supporting_text_check"].items() if k != "note"},
        "bm25_idf": dict(smp["bm25_idf"], df_sha256=df_digest(idf["df"])),
        "confirm": [{"id": x["id"], "group": x["group"], "supporting_in_pool": x["supporting_in_pool"]}
                    for x in smp["confirm"]],
        "smoke": [{"id": x["id"], "group": x["group"], "supporting_in_pool": x["supporting_in_pool"]}
                  for x in smp["smoke"]],
        "ineligible_skipped_ids": smp["ineligible_skipped_ids"]}

    # rankings: five local rankers, then RankGPT ---------------------------------------------------
    local = jl(P3 / "rankings_local_confirm.jsonl")
    rank_rows, rankings = [], {}
    for r in local:
        assert r["ranker"] in RF.LOCAL and r["id"] in by_id and sorted(r["order"]) == list(range(10)), r["id"]
        assert (r["id"], r["ranker"]) not in rankings and r["role"] == "fullwiki_rank", r["id"]
        rankings[(r["id"], r["ranker"])] = r["order"]
        rank_rows.append({"kind": "local", "ranker": r["ranker"], "item": r["id"], "order": r["order"],
                          "top_k": r["order"][:K], "scores": r["scores"]})
    if rankings != RF.load_local("confirm") or len(rankings) != len(RF.LOCAL) * len(items):
        raise SystemExit("local rankings incomplete or read differently from run_fullwiki.load_local")
    expected = {q["id"]: q for q in RF.rank_requests(items)}
    rank_ids = [rid for rid, rc in R.items() if rc["kind"] == "rank"]
    if set(rank_ids) != set(expected):
        raise SystemExit("ranking requests differ from run_fullwiki.rank_requests")
    for rid in rank_ids:
        rc, e = R[rid], expected[rid]
        it = by_id[rc["item"]]
        assert (rc["pool"], rc["order_idx"], rc["size"], rc["model"]) == (e["pool"], e["order_idx"], e["size"], e["model"]), rid
        prompt = Q.rank_prompt(it, rc["pool"])
        assert X.sha_text(prompt) == rc["prompt_sha256"] and len(prompt) == rc["prompt_chars"], rid
        n_prompts += 1
        failed = bool(rc.get("transport_failed"))
        order, info = (None, None) if failed else X.parse_info(rc.get("raw_text"), len(rc["pool"]))
        ranking = None if failed else [rc["pool"][k] for k in order]
        if info is not None:
            info["repaired"] = bool(info["appended"] or info["duplicates"] or info["out_of_range"])
        if ranking is not None and rc["order_idx"] == 0:
            rankings[(it["id"], "rankgpt")] = ranking
        rank_rows.append(request_row({
            "kind": "rankgpt", "ranker": "rankgpt", "item": it["id"], "id": rid, "model": rc["model"],
            "order_idx": rc["order_idx"], "used_for_answers": rc["order_idx"] == 0 and not failed,
            "size": rc["size"], "pool": rc["pool"], "order": ranking,
            "top_k": None if ranking is None else ranking[:K], "parse": info}, rc, issued))
    gpt = Q.rankgpt_rankings(st, by_id)
    assert all(rankings[k] == v for k, v in gpt.items()) and len(gpt) == sum(k[1] == "rankgpt" for k in rankings)

    # answers --------------------------------------------------------------------------------------
    planned = {q["id"]: q for q in RF.answer_requests(items, rankings)}
    ans_ids = [rid for rid, rc in R.items() if rc["kind"] == "answer"]
    if set(ans_ids) != set(planned):
        raise SystemExit("answer requests differ from run_fullwiki.answer_requests")
    ans_rows = []
    for rid in ans_ids:
        rc = R[rid]
        it = by_id[rc["item"]]
        assert (rc["role"], rc["dataset"], rc["model"], rc["cond"]) == (
            it["role"], it["dataset"], planned[rid]["model"], planned[rid]["cond"]), rid
        idx = X.context_indices(it, rc["cond"], rankings)
        prompt = X.prompt_from_indices(it, idx)
        assert prompt == Q.answer_prompt(it, rc["cond"], rankings) == planned[rid]["prompt"], rid
        assert X.sha_text(prompt) == rc["prompt_sha256"] and len(prompt) == rc["prompt_chars"], rid
        n_prompts += 1
        failed = bool(rc.get("transport_failed"))
        em = f1 = contains = tag = None
        if not failed:
            em, f1, contains = Q.score(rc.get("raw_text"), it["answers"])
            tag = bool(RF.ANSWER_LINE.search(rc.get("raw_text") or ""))
        ans_rows.append(request_row({
            "id": rid, "item": it["id"], "group": it["group"], "model": rc["model"], "cond": rc["cond"],
            "context": idx, "em": em, "f1": f1, "contains": contains, "has_answer_line": tag}, rc, issued))
    if n_prompts != len(R):
        raise SystemExit("%d of %d prompts rebuilt" % (n_prompts, len(R)))

    # provenance ------------------------------------------------------------------------------------
    inputs = {rel: X.sha_file(ROOT / rel) for rel in INPUTS}
    frozen = [rel for rel in INPUTS if rel in fz["sha256"]]
    bad = [rel for rel in frozen if fz["sha256"][rel] != inputs[rel]]
    if bad:
        raise SystemExit("inputs differ from their digests in FREEZE_fullwiki.json: %s" % bad)
    models = json.load(open(P3 / "local_models.json", encoding="utf-8"))
    assert models["offline"] == {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    status = Counter(x["status"] for x in rank_rows[len(local):] + ans_rows)
    provenance = {
        # The freeze lists every candidate title, so the authors keep it (public: false). Its own
        # digest and every digest it lists are recorded here, so that a rebuild can still be checked.
        "freeze": {"file": "results/package3/FREEZE_fullwiki.json", "public": False, "sha256": X.sha_file(FZ.FREEZE),
                   "frozen_at_utc": fz["frozen_at_utc"], "files": len(fz["sha256"]), "verified": True,
                   "frozen_sha256": fz["sha256"]},
        "frozen_inputs_match_FREEZE_fullwiki_json": frozen,
        "inputs_sha256": inputs,
        "analysis_sha256": {rel: X.sha_file(ROOT / rel) for rel in (
            "results/package3/analysis_fullwiki.json", "results/package3/analysis_fullwiki.md")},
        "code_sha256": {rel: X.sha_file(ROOT / rel) for rel in CODE},
        "local_models": {"offline": True, "models": models["models"]},
        "counts": {"items": len(item_rows), "groups": dict(Counter(it["group"] for it in items)),
                   "local_rankings": len(local), "requests": len(R),
                   "requests_by_kind": dict(sorted(Counter(rc["kind"] for rc in R.values()).items())),
                   "status": dict(sorted(status.items())),
                   "transport_failed": sum(1 for rc in R.values() if rc.get("transport_failed")),
                   "prompts_rebuilt_and_matched": n_prompts}}
    files = {"items.jsonl": item_rows, "sample.json": sample, "rankings.jsonl": rank_rows,
             "answers.jsonl": ans_rows, "provenance.json": provenance}
    return files, n_prompts


def main():
    files, n_prompts = build()                 # every check passes before anything is written
    OUT.mkdir(parents=True, exist_ok=True)
    for name, obj in files.items():
        (X.write_jsonl if name.endswith(".jsonl") else X.write_json)(OUT / name, obj)
    for src in (RES3 / "analysis_fullwiki.json", RES3 / "analysis_fullwiki.md", REC_DIR / "summary.txt"):
        X.copy_lf(src, OUT / src.name)
    rk, ans = files["rankings.jsonl"], files["answers.jsonl"]
    c = files["provenance.json"]["counts"]
    print("confirm -> %s" % OUT.relative_to(ROOT).as_posix())
    print("  items %d (%s) | rankings %d (local %d, RankGPT %d) | answers %d"
          % (c["items"], c["groups"], len(rk), c["local_rankings"], len(rk) - c["local_rankings"], len(ans)))
    print("  requests %d %s; status %s" % (c["requests"], c["requests_by_kind"], c["status"]))
    print("  prompts rebuilt from the exported indices and matched (SHA-256 and length): %d" % n_prompts)
    for p in sorted(OUT.iterdir()):
        print("  %-24s %9d bytes" % (p.name, p.stat().st_size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
