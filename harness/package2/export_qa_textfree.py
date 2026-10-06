r"""Text-free public export of the natural-data records.

The natural-data records (natural_data/, gitignored) contain text from HotpotQA (CC BY-SA 4.0),
MuSiQue (CC BY 4.0) and TAT-QA (CC BY 4.0) and the models' replies, so they are not redistributed.
This script writes what can be released without reproducing any of that text: question and request
identifiers, dataset and role labels, splits, paragraph INDICES (never titles or text), every
ranking as an index list, the scores computed by the project's own scorers, missingness and
transport status, resource use, and SHA-256 digests of every prompt and of every released
paragraph, so that a rebuild from the public datasets can be checked byte for byte.

  confirm   the package-2 QA benchmarks (Sections 4.7 and 5.9; Tables 12 and 13), from
            natural_data/package2/{items_confirm.jsonl, rankings_local_confirm.jsonl, splits.json,
            confirmation_*.txt, items_pilot.jsonl, confirm_qa/} -> results/package2/confirm_qa_textfree/
  pilot     the 2 October exploratory pilot (development data), from natural_data/stage1/ and
            natural_data/stage2/ -> results/natural_pilot_textfree/

Scores, parses and selected-paragraph lists are computed with the functions the analysis used
(run_qa.score, run_qa.parse_ranking, harness/natural/scoring.score); before anything is written,
every prompt is rebuilt from the exported indices and checked against its recorded SHA-256, so the
exported selections are exactly what was sent. Deterministic: no clock, no network, no model call;
standard library only, given natural_data/hotpot_dev_distractor.jsonl (qa_data.py writes it from the
parquet with PyArrow). Rows keep the order of the source records (the bootstrap in analyze_qa.py
resamples in that order, so the intervals are reproducible from the export).

  python harness/package2/export_qa_textfree.py [confirm|pilot|all]      (default: all)

Then run the leak check and the reproduction check:
  python harness/package2/check_textfree_leaks.py
  python harness/package2/verify_qa_textfree.py
"""
import hashlib
import io
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "harness" / "natural"))
import qa_data as D  # noqa: E402
import run_qa as Q  # noqa: E402

ND = ROOT / "natural_data"
P2 = ND / "package2"
OUT_CONFIRM = ROOT / "results" / "package2" / "confirm_qa_textfree"
OUT_PILOT = ROOT / "results" / "natural_pilot_textfree"
Q.SET.update(Q.SETS["confirm"])

ANSWER_LINE = re.compile(r"(?:final answer|answer)\s*[:\-]", re.I)     # analyze_qa.py's compliance test
RANK_ID = re.compile(r"\[(\d+)\]")                                        # run_qa.parse_ranking's pattern
# Usage fields that are not exported because every record has the same value (asserted below).
CONSTANT_USAGE = {
    "Haiku-4.5": {"cache_creation.ephemeral_1h_input_tokens": 0, "cache_creation.ephemeral_5m_input_tokens": 0,
                  "cache_creation_input_tokens": 0, "service_tier": "standard", "inference_geo": "not_available"},
    "GPT-5.5": {"input_tokens_details.cache_write_tokens": 0},
    "DeepSeek-V4-Pro": {"audio_prompt_tokens": 0},
}
EXPORTED_USAGE = {"input_tokens", "output_tokens", "prompt_tokens", "completion_tokens", "total_tokens",
                  "output_tokens_details.reasoning_tokens", "input_tokens_details.cached_tokens",
                  "prompt_tokens_details.cached_tokens", "cache_read_input_tokens"}


# ---- helpers -----------------------------------------------------------------------------------
def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    return len(rows)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=1) + "\n")


def copy_lf(src, dst):
    """Copy a text file with LF line ends (git stores LF; the manifest hashes those bytes)."""
    text = Path(src).read_bytes().decode("utf-8").replace("\r\n", "\n")
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def flat(d, prefix=""):
    out = {}
    for k, v in (d or {}).items():
        key = prefix + k
        if isinstance(v, dict):
            out.update(flat(v, key + "."))
        else:
            out[key] = v
    return out


def token_fields(model, usage):
    """Input/output tokens as run_qa.toks reads them, plus reasoning, cached and total tokens.
    Every other usage field must hold its constant value, so nothing is silently dropped."""
    if usage is None:
        return {"input_tokens": None, "output_tokens": None, "reasoning_tokens": None,
                "cached_input_tokens": None, "total_tokens": None}
    f = flat(usage)
    const = CONSTANT_USAGE.get(model, {})
    for k, v in f.items():
        if k in EXPORTED_USAGE:
            continue
        if k not in const or const[k] != v:
            raise SystemExit("unexpected usage field %s=%r for %s: extend the export" % (k, v, model))
    cached = f.get("input_tokens_details.cached_tokens", f.get("prompt_tokens_details.cached_tokens",
                                                                 f.get("cache_read_input_tokens")))
    return {"input_tokens": f.get("input_tokens", f.get("prompt_tokens")),
            "output_tokens": f.get("output_tokens", f.get("completion_tokens")),
            "reasoning_tokens": f.get("output_tokens_details.reasoning_tokens"),
            "cached_input_tokens": cached, "total_tokens": f.get("total_tokens")}


def attempt_entry(a):
    """One attempt without the provider's error text: status, an error class and, for content-filter
    refusals, which side was filtered and the provider's label where the stored body names it."""
    body = a.get("error_body") or ""
    cls = src = label = ptoks = None
    if a.get("error"):
        m = re.search(r'"code"\s*:\s*"([A-Za-z_]+)"', body)
        cls = m.group(1) if m else a["error"].split(":")[0]
        if cls == "content_filter":
            m = re.search(r"blocked by label '([A-Za-z_]+)'", body)
            if m:                                   # DeepSeek (Azure AI Foundry): the reply was blocked
                src, label = "completion", m.group(1)
            m = re.search(r'"blocked"\s*:\s*true\s*,\s*"source_type"\s*:\s*"([a-z_]+)"', body)
            if m:                                   # GPT-5.5 (Azure OpenAI): the prompt was blocked
                src = m.group(1)
        m = re.search(r'"prompt_tokens"\s*:\s*(\d+)', body)
        ptoks = int(m.group(1)) if m else None
    return {"attempt": a.get("attempt"), "start_utc": a.get("start_utc"), "end_utc": a.get("end_utc"),
            "http_status": a.get("http_status"), "error_class": cls, "filter_source": src,
            "filter_label": label, "prompt_tokens": ptoks}


def filter_flags(resp):
    """Categories the provider's content filter marked as filtered in a received response."""
    out = set()
    for c in (resp or {}).get("content_filters") or []:
        for cat, v in (c.get("content_filter_results") or {}).items():
            if isinstance(v, dict) and v.get("filtered"):
                out.add("%s:%s" % (c.get("source_type"), cat))
    for ch in (resp or {}).get("choices") or []:
        for cat, v in (ch.get("content_filter_results") or {}).items():
            if isinstance(v, dict) and v.get("filtered"):
                out.add("completion:%s" % cat)
    return sorted(out)


REQUESTED = {"Haiku-4.5": "claude-haiku-4-5", "GPT-5.5": "gpt-5.5", "DeepSeek-V4-Pro": "DeepSeek-V4-Pro"}


def request_fields(rc, issued_utc, wall_s):
    """Status, missingness and resource use of one request. The requested model id is not repeated
    per row: it is fixed per model label (REQUESTED, asserted here)."""
    if rc.get("requested_model") != REQUESTED[rc["model"]]:
        raise SystemExit("requested model %r for %s" % (rc.get("requested_model"), rc["model"]))
    atts = rc.get("attempts") or []
    trivial = len(atts) == 1 and not atts[0].get("error") and atts[0].get("http_status") == 200
    log = None if trivial else [attempt_entry(a) for a in atts]
    failed = bool(rc.get("transport_failed"))
    missing = None
    if failed:
        missing = "content_filter" if log and all(x["error_class"] == "content_filter" for x in log) else "transport_error"
    resp = rc.get("response") or {}
    out = {"issued_utc": issued_utc, "wall_s": wall_s,
           "returned_model": rc.get("returned_model"), "response_id": rc.get("response_id"),
           "stop_reason": rc.get("stop_reason"),
           "incomplete_reason": (resp.get("incomplete_details") or {}).get("reason"),
           "filtered_categories": filter_flags(resp), "transport_failed": failed, "missing_reason": missing,
           "attempts": len(atts), "attempt_log": log}
    out.update(token_fields(rc["model"], rc.get("usage")))
    out["prompt_sha256"] = rc.get("prompt_sha256")
    return out


def parse_info(raw_text, n):
    """run_qa.parse_ranking, plus the counts it implies (identifiers out of range, appended)."""
    order, info = Q.parse_ranking(raw_text, n)
    ids = [int(x) for x in RANK_ID.findall(raw_text or "")]
    return order, {"returned": info["returned"], "duplicates": info["duplicates"],
                   "out_of_range": sum(1 for i in ids if not 1 <= i <= n),
                   "appended": n - info["returned"], "complete": info["complete"]}


def supporting(it):
    return [i for i, p in enumerate(it["paragraphs"]) if p["supporting"]]


def context_indices(it, cond, rankings):
    """The paragraph indices run_qa.context_for presents, in order (None: no context block)."""
    if cond == "none":
        return None
    if cond == "full":
        return list(range(len(it["paragraphs"])))
    if cond in Q.RANKED:
        return list(rankings[(it["id"], cond)][:Q.BUDGET[it["dataset"]]])
    gold, dist = supporting(it), it["augment_distractors"]
    return {"gold": gold, "gold+dist": gold + dist, "dist+gold": dist + gold}[cond]


def prompt_from_indices(it, idx):
    if idx is None:
        return Q.ANSWER_NONE.format(q=it["question"])
    ctx = "\n".join("[%d] %s" % (k + 1, Q.passage(it["paragraphs"][i])) for k, i in enumerate(idx))
    return Q.ANSWER_CTX.format(ctx=ctx, q=it["question"])


# ---- package 2: confirmatory QA benchmarks -----------------------------------------------------
def export_confirm():
    out = OUT_CONFIRM
    out.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in open(P2 / "items_confirm.jsonl", encoding="utf-8")]
    by_id = {it["id"]: it for it in items}
    st = Q.load_records(P2 / "confirm_qa" / "records.jsonl")
    R, issued = st["receipt"], st["issued"]
    if set(issued) != set(R):
        raise SystemExit("issued and received requests differ; the export assumes every request has a receipt")

    # items ------------------------------------------------------------------------------------
    rows = []
    for it in items:
        row = {"id": it["id"], "dataset": it["dataset"], "role": it["role"], "split": "confirmation",
               "type": it["type"], "n_paragraphs": len(it["paragraphs"]), "supporting": supporting(it),
               "n_gold_answers": len(it["answers"]), "question_sha256": sha_text(it["question"]),
               "title_sha256": [sha_text(p["title"]) for p in it["paragraphs"]],
               "text_sha256": [sha_text(p["text"]) for p in it["paragraphs"]]}
        if it["role"] == "hotpot_aug":
            assert it["augment_distractors"] == D.checked_distractors(it)[:2], it["id"]
            row["augment_distractors"] = it["augment_distractors"]
        rows.append(row)
    n_items = write_jsonl(out / "items.jsonl", rows)

    # splits -------------------------------------------------------------------------------------
    sp = json.load(open(P2 / "splits.json", encoding="utf-8"))
    pilot = [json.loads(l) for l in open(P2 / "items_pilot.jsonl", encoding="utf-8")]
    splits = {"seed": D.SEED, "confirm_draw_seed": D.SEED + 1, "dev_size": D.DEV_SIZE,
              "sources_sha256": sp["sources"], "datasets": {}}
    for ds in ("hotpotqa", "musique"):
        conf = [l.strip() for l in open(P2 / ("confirmation_%s.txt" % ds), encoding="utf-8") if l.strip()]
        s = sp["splits"][ds]
        assert hashlib.sha256("\n".join(conf).encode()).hexdigest() == s["confirmation_sha256"], ds
        assert len(conf) == s["confirmation_size"], ds
        with open(out / ("confirmation_%s.txt" % ds), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(conf) + "\n")
        splits["datasets"][ds] = {
            "excluded": s["excluded"], "dev": s["dev"], "confirmation_size": s["confirmation_size"],
            "confirmation_sha256": s["confirmation_sha256"], "confirmation_file": "confirmation_%s.txt" % ds,
            "pilot_items": [{"id": p["id"], "role": p["role"]} for p in pilot if p["dataset"] == ds],
            "confirm_items": [{"id": it["id"], "role": it["role"]} for it in items if it["dataset"] == ds]}
    write_json(out / "splits.json", splits)

    # rankings: five local rankers and RankGPT ----------------------------------------------------
    local = [json.loads(l) for l in open(P2 / "rankings_local_confirm.jsonl", encoding="utf-8")]
    rank_rows = []
    rankings = {}
    for r in local:
        rank_rows.append({"kind": "local", "ranker": r["ranker"], "item": r["id"], "dataset": r["dataset"],
                          "role": r["role"], "order": r["order"], "scores": r["scores"]})
        rankings[(r["id"], r["ranker"])] = r["order"]
    expected = {q["id"]: q for q in Q.build_rank_requests(items)}
    n_prompts = 0
    for rid, rc in R.items():
        if rc["kind"] != "rank":
            continue
        it = by_id[rc["item"]]
        assert expected[rid]["pool"] == rc["pool"], rid
        assert sha_text(Q.rank_prompt(it, rc["pool"])) == rc["prompt_sha256"], rid
        n_prompts += 1
        failed = bool(rc.get("transport_failed"))
        order, info = (None, None) if failed else parse_info(rc.get("raw_text"), len(rc["pool"]))
        ranking = None if failed else [rc["pool"][k] for k in order]
        if ranking is not None and rc["order_idx"] == 0:
            rankings[(it["id"], "rankgpt")] = ranking
        row = {"kind": "rankgpt", "ranker": "rankgpt", "item": it["id"], "dataset": it["dataset"],
               "role": it["role"], "order": ranking, "scores": None, "id": rid, "model": rc["model"],
               "order_idx": rc["order_idx"], "used_for_answers": rc["order_idx"] == 0 and not failed,
               "size": rc["size"], "pool": rc["pool"], "parse": info}
        row.update(request_fields(rc, issued[rid]["utc"], rc["wall_s"]))
        row["prompt_chars"] = rc["prompt_chars"]
        rank_rows.append(row)
    assert rankings.keys() >= set(Q.rankgpt_rankings(st, by_id)) and all(
        rankings[k] == v for k, v in Q.rankgpt_rankings(st, by_id).items())
    n_rank = write_jsonl(out / "rankings.jsonl", rank_rows)

    # answers --------------------------------------------------------------------------------------
    ans_rows = []
    for rid, rc in R.items():
        if rc["kind"] != "answer":
            continue
        it = by_id[rc["item"]]
        idx = context_indices(it, rc["cond"], rankings)
        prompt = prompt_from_indices(it, idx)
        assert prompt == Q.answer_prompt(it, rc["cond"], rankings), rid
        assert sha_text(prompt) == rc["prompt_sha256"] and len(prompt) == rc["prompt_chars"], rid
        n_prompts += 1
        failed = bool(rc.get("transport_failed"))
        em = f1 = contains = tag = None
        if not failed:
            em, f1, contains = Q.score(rc.get("raw_text"), it["answers"])
            tag = bool(ANSWER_LINE.search(rc.get("raw_text") or ""))
        row = {"id": rid, "item": it["id"], "dataset": it["dataset"], "role": rc["role"], "model": rc["model"],
               "cond": rc["cond"], "context": idx, "em": em, "f1": f1, "contains": contains,
               "has_answer_line": tag}
        row.update(request_fields(rc, issued[rid]["utc"], rc["wall_s"]))
        row["prompt_chars"] = rc["prompt_chars"]
        ans_rows.append(row)
    n_ans = write_jsonl(out / "answers.jsonl", ans_rows)

    # overhead -------------------------------------------------------------------------------------
    ov_rows = []
    for rid, rc in R.items():
        if rc["kind"] != "overhead":
            continue
        it = by_id[rc["item"]]
        assert expected[rid]["pool"] == rc["pool"], rid
        assert sha_text(Q.rank_prompt(it, rc["pool"])) == rc["prompt_sha256"], rid
        n_prompts += 1
        failed = bool(rc.get("transport_failed"))
        order, info = (None, None) if failed else parse_info(rc.get("raw_text"), len(rc["pool"]))
        ranking = None if failed else [rc["pool"][k] for k in order]
        sup = set(supporting(it))
        assert sup <= set(rc["pool"]), rid
        k = len(sup)
        row = {"id": rid, "item": it["id"], "dataset": it["dataset"], "role": it["role"], "model": rc["model"],
               "size": rc["size"], "order_idx": rc["order_idx"], "pool": rc["pool"], "order": ranking,
               "parse": info, "k": k,
               "recall_at_k": None if failed else len(set(ranking[:k]) & sup) / k}
        row.update(request_fields(rc, issued[rid]["utc"], rc["wall_s"]))
        row["prompt_chars"] = rc["prompt_chars"]
        ov_rows.append(row)
    n_ov = write_jsonl(out / "overhead.jsonl", ov_rows)

    # augmentation design --------------------------------------------------------------------------
    aug_rows = []
    for it in items:
        if it["role"] != "hotpot_aug":
            continue
        gold, dist = supporting(it), it["augment_distractors"]
        aug_rows.append({"item": it["id"], "dataset": it["dataset"], "role": it["role"], "supporting": gold,
                         "eligible_distractors": D.checked_distractors(it), "added": dist,
                         "contexts": {c: context_indices(it, c, rankings) for c in Q.answer_conditions(it)}})
    n_aug = write_jsonl(out / "augmentation.jsonl", aug_rows)

    # analysis outputs (numbers only) and provenance -------------------------------------------------
    for f in ("analysis_qa.json", "analysis_qa.md", "summary.txt"):
        copy_lf(P2 / "confirm_qa" / f, out / f)
    fz = json.load(open(ROOT / "results" / "package2" / "FREEZE.json", encoding="utf-8"))["sha256"]
    inputs = {}
    for rel in ("natural_data/package2/items_confirm.jsonl", "natural_data/package2/rankings_local_confirm.jsonl",
                "natural_data/package2/splits.json", "natural_data/package2/items_pilot.jsonl",
                "natural_data/package2/confirm_qa/records.jsonl", "natural_data/package2/confirm_qa/analysis_qa.json"):
        inputs[rel] = sha_file(ROOT / rel)
        if rel in fz and fz[rel] != inputs[rel]:
            raise SystemExit("%s differs from its digest in results/package2/FREEZE.json" % rel)
    code = {rel: sha_file(ROOT / rel) for rel in (
        "harness/package2/qa_data.py", "harness/package2/rank_local.py", "harness/package2/run_qa.py",
        "harness/package2/analyze_qa.py", "harness/package2/export_qa_textfree.py")}
    kinds = Counter(rc["kind"] for rc in R.values())
    write_json(out / "provenance.json", {
        "frozen_inputs_match_FREEZE_json": [r for r in inputs if r in fz],
        "inputs_sha256": inputs, "code_sha256": code,
        "counts": {"items": n_items, "local_rankings": len(local), "requests": len(R),
                   "requests_by_kind": dict(sorted(kinds.items())),
                   "transport_failed": sum(1 for rc in R.values() if rc.get("transport_failed")),
                   "prompts_rebuilt_and_matched": n_prompts}})
    print("confirm -> %s" % out.relative_to(ROOT).as_posix())
    print("  items %d | rankings %d (local %d, RankGPT %d) | answers %d | overhead %d | augmentation %d"
          % (n_items, n_rank, len(local), n_rank - len(local), n_ans, n_ov, n_aug))
    print("  requests %d %s; transport failures %d; prompts rebuilt from the exported indices and matched: %d"
          % (len(R), dict(sorted(kinds.items())), sum(1 for rc in R.values() if rc.get("transport_failed")), n_prompts))
    return n_prompts


# ---- 2 October exploratory pilot -----------------------------------------------------------------
NOT_EXCLUSIVE = {"T09-table", "T18-table", "T17-text"}   # STAGE2-REPORT.md: answer derivable from the other source


def verdict_class(v):
    return None if v is None else v.split(":")[0].strip()


def export_pilot():
    import scoring as S
    import stage2_pilot as P
    out = OUT_PILOT
    out.mkdir(parents=True, exist_ok=True)
    sample = json.load(open(ND / "stage1" / "sample.json", encoding="utf-8"))
    audit = json.load(open(ND / "stage1" / "audit.json", encoding="utf-8"))
    items = json.load(open(ND / "stage2" / "items.json", encoding="utf-8"))
    hot_src = {r["id"]: r for r in D.load_hotpot() if r["id"] in {h["id"] for h in sample["hotpotqa"]}}

    # Stage 1 audit (labels only; the verdict reasons and notes are prose and stay local) ------------
    s1 = []
    tat_verdict = {(r["item"], r["kind"]): r for r in audit["tatqa"]}
    for k, doc in enumerate(sample["tatqa"]):
        tag = "T%02d" % k
        qs = []
        for kind, q in doc["questions"].items():
            a = tat_verdict.get((tag, kind))
            assert a is None or a["uid"] == q["uid"]
            qs.append({"kind": kind, "tatqa_question_uid": q["uid"], "answer_type": q["answer_type"],
                       "scale": q["scale"], "evidence_in_table": q["evidence_in_table"],
                       "evidence_in_text": q["evidence_in_text"], "verdict": verdict_class(a and a["verdict"])})
        s1.append({"item": tag, "dataset": "tatqa", "tatqa_doc_uid": doc["doc_uid"], "questions": qs})
    gold_idx = {}
    for k, (h, a) in enumerate(zip(sample["hotpotqa"], audit["hotpotqa"])):
        tag = "H%02d" % k
        assert a["item"] == tag and a["id"] == h["id"]
        titles = [p["title"] for p in hot_src[h["id"]]["paragraphs"]]
        gi = [titles.index(t) for t in h["gold_titles"]]
        for t, i in zip(h["gold_titles"], gi):           # the pilot's sources are these paragraphs, verbatim
            assert hot_src[h["id"]]["paragraphs"][i]["text"] == h["paragraphs"][t]
        gold_idx[tag] = gi
        s1.append({"item": tag, "dataset": "hotpotqa", "hotpotqa_id": h["id"], "type": h["type"],
                   "gold_paragraphs": gi, "original_verdict": verdict_class(a["original_verdict"]),
                   "leak_noted": "leak" in a["note"],
                   "subquestions": [{"source": sq["source"], "in_own": sq["in_own"], "in_other": sq["in_other"],
                                     "verdict": verdict_class(sq["verdict"])} for sq in a["subquestions"]]})
    write_jsonl(out / "stage1_audit.jsonl", s1)

    # Stage 2 items -----------------------------------------------------------------------------------
    rows, by_id = [], {}
    for it in items:
        by_id[it["id"]] = it
        tag, rest = it["id"].split("-", 1)
        if it["dataset"] == "tatqa":
            doc = sample["tatqa"][int(tag[1:])]
            q = doc["questions"][rest]
            src = {"tatqa_doc_uid": doc["doc_uid"], "tatqa_question_uid": q["uid"], "answer_type": q["answer_type"]}
            origin = "dataset"
            verdict = verdict_class(tat_verdict[(tag, rest)]["verdict"])
            assert it["A"] == "Table:\n" + doc["table"] and it["B"] == "Text:\n" + doc["text"]
        else:
            h = sample["hotpotqa"][int(tag[1:])]
            a = audit["hotpotqa"][int(tag[1:])]
            sub = None if rest == "orig" else int(rest[2:])
            assert [it["A"], it["B"]] == ["%s\n%s" % (t, h["paragraphs"][t]) for t in h["gold_titles"]], it["id"]
            src = {"hotpotqa_id": h["id"], "hotpotqa_type": h["type"], "A_paragraph": gold_idx[tag][0],
                   "B_paragraph": gold_idx[tag][1], "subquestion": sub}
            origin = "dataset" if sub is None else "project"
            verdict = verdict_class(a["original_verdict"] if sub is None else a["subquestions"][sub - 1]["verdict"])
        # The Stage 2 derivability check covered TAT-QA single-source questions only.
        exclusive = (it["id"] not in NOT_EXCLUSIVE) if it["dataset"] == "tatqa" and it["own"] in ("A", "B") else None
        rows.append({"id": it["id"], "dataset": it["dataset"], "task": it["task"], "own": it["own"],
                     "score_kind": it["score_kind"], "scale": it["scale"], "question_origin": origin,
                     "stage1_verdict": verdict, "exclusive": exclusive, "source": src,
                     "question_sha256": sha_text(it["question"]), "A_sha256": sha_text(it["A"]),
                     "B_sha256": sha_text(it["B"])})
    n_items = write_jsonl(out / "items.jsonl", rows)

    # Stage 2 requests --------------------------------------------------------------------------------
    issued, receipts = {}, {}
    for line in open(ND / "stage2" / "records" / "pilot.jsonl", encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r["type"] == "issued":
            issued[r["schedule_id"]] = r
        elif r["type"] == "receipt":
            receipts[r["schedule_id"]] = r
    sched = [json.loads(l) for l in open(ND / "stage2" / "schedule.jsonl", encoding="utf-8") if l.strip()]
    assert set(issued) == set(receipts) == {s["schedule_id"] for s in sched}
    # The report's scores (scored.json, one row per reply, no draw index): compared per cell below.
    scored, mine = Counter(), Counter()
    for r in json.load(open(ND / "stage2" / "scored.json", encoding="utf-8")):
        scored[(r["model"], r["item"], r["cond"], r["ok"], r["f1"])] += 1
    req_rows = []
    for sid, rc in receipts.items():
        it = by_id[rc["item"]]
        assert sha_text(P.prompt(it, rc["condition"])) == rc["prompt_sha256"], sid
        failed = bool(rc.get("transport_failed"))
        ok = f1 = refusal = has_num = None
        if not failed:
            ok, f1 = S.score(rc["raw_text"], it["gold"], it["score_kind"], it["scale"])
            ok = bool(ok)
            refusal = bool(S.REFUSAL.search(str(rc["raw_text"])))
            if it["score_kind"] == "number":
                has_num = bool(S.numbers_in(rc["raw_text"] or ""))
        mine[(rc["model"], rc["item"], rc["condition"], bool(ok), f1)] += 1
        wall = (datetime.fromisoformat(rc["end_utc"]) - datetime.fromisoformat(rc["start_utc"])).total_seconds()
        row = {"id": sid, "item": rc["item"], "model": rc["model"], "condition": rc["condition"], "draw": rc["draw"],
               "window": rc["window"], "seq": rc["seq"], "lane": rc["lane"], "pass": ok, "f1": f1,
               "refusal": refusal, "has_number": has_num}
        row.update(request_fields(rc, issued[sid]["utc"], round(wall, 3)))
        row["end_utc"] = rc["end_utc"]
        req_rows.append(row)
    mism = sum(((scored - mine) + (mine - scored)).values())
    if mism:
        raise SystemExit("%d pilot scores differ from natural_data/stage2/scored.json" % mism)
    n_req = write_jsonl(out / "requests.jsonl", req_rows)
    inputs = {rel: sha_file(ROOT / rel) for rel in (
        "natural_data/stage1/sample.json", "natural_data/stage1/audit.json", "natural_data/stage2/items.json",
        "natural_data/stage2/schedule.jsonl", "natural_data/stage2/records/pilot.jsonl",
        "natural_data/stage2/scored.json")}
    code = {rel: sha_file(ROOT / rel) for rel in (
        "harness/natural/stage1_sample.py", "harness/natural/stage1_annotate.py", "harness/natural/stage2_pilot.py",
        "harness/natural/scoring.py", "harness/package2/export_qa_textfree.py")}
    write_json(out / "provenance.json", {
        "inputs_sha256": inputs, "code_sha256": code,
        "sources_sha256": {"hotpot_dev_distractor.parquet": "c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6",
                           "tatqa_dataset_dev.json": sha_file(ND / "tatqa_dataset_dev.json")},
        "counts": {"stage1_items": len(s1), "items": n_items, "requests": n_req,
                   "transport_failed": sum(1 for r in req_rows if r["transport_failed"]),
                   "prompts_rebuilt_and_matched": n_req, "scores_matching_scored_json": n_req - mism}})
    assert sha_file(ND / "hotpot_dev_distractor.parquet") == "c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6"
    print("pilot -> %s" % out.relative_to(ROOT).as_posix())
    print("  stage-1 audit records %d | items %d (%s) | requests %d %s | transport failures %d"
          % (len(s1), n_items, dict(Counter(r["dataset"] for r in rows)), n_req,
             dict(Counter(r["model"] for r in req_rows)), sum(1 for r in req_rows if r["transport_failed"])))
    print("  prompts rebuilt and matched: %d; scores identical to scored.json: %d" % (n_req, n_req - mism))


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what not in ("confirm", "pilot", "all"):
        raise SystemExit(__doc__)
    if what in ("confirm", "all"):
        export_confirm()
    if what in ("pilot", "all"):
        export_pilot()


if __name__ == "__main__":
    main()
