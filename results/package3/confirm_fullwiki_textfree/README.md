# Reranking on retrieved candidates (HotpotQA fullwiki): text-free records

These files are the public record of the fullwiki benchmark of the manuscript (Table
`tab:fullwiki`; Sections `sec:natural` and `sec:results-natural`). It ran as package 3, fixed in
`harness/package3/PROTOCOL_FULLWIKI.md` and frozen before the first request (see "The freeze"
below). The files cover the 300 confirmatory questions and all 7,800 requests, collected on
6 October 2026 from 07:51 to 08:58 UTC. Each question has the ten candidate paragraphs that
HotpotQA's own retrieval system returned. Of the 300 questions, 90 have both supporting paragraphs
among their candidates (the sufficient subgroup) and 210 do not (the complement: 150 with one, 60
with none).

One descriptive figure of the frozen protocol is corrected in
`harness/package3/PROTOCOL_FULLWIKI_ERRATA.md`: of the 7,342 eligible questions in the file, 2,066
are sufficient, not 2,089 (2,089 is the count over all 7,405 questions). No setting, sample,
subgroup label or result depends on it.

Every published number can be recomputed from this directory alone:

```bash
python harness/package3/verify_fullwiki_textfree.py
```

The script recomputes all of `analysis_fullwiki.json` with the analysis code
(`analyze_fullwiki.py`, `analyze_qa.py`). That covers 1,022 numbers, bootstrap intervals included,
and every one agrees within 1e-12. It then regenerates `analysis_fullwiki.md` and `summary.txt`
from the recomputed results, and both come out identical. Finally, it checks Table `tab:fullwiki`
and the figures quoted in the text as printed in the manuscript. Its consistency checks also read
package 2's export, which lists the excluded questions, and compare the frozen protocol and code in
this repository with their frozen digests. The few checks that need the freeze file itself run
only on the authors' copy; elsewhere they print "freeze not public; skipped".

## What is released and what is not

**Released:** question and request identifiers; group, type, condition and model labels; the
draw; paragraph **indices**; every ranking as a list of indices; exact match and F1 for every
answer; parse, missingness and transport status; resource use; and SHA-256 digests. The digests
cover every prompt sent and every question, paragraph title, paragraph text and supporting title
used, so a rebuild from the public dataset can be checked byte for byte.

**Not released:** question text, gold answers, paragraph titles and texts, the models' replies and
the answers read from them, the providers' response envelopes, and the providers' error messages.
These records reproduce benchmark text or reply text. They are kept by the authors and are
available on request. `provenance.json` gives the SHA-256 of the record file they are in.

**The freeze.** Before the first request, `harness/package3/freeze_fullwiki.py` froze the protocol,
the code, the source file, the sample, the items, the IDF table, the local rankings and the seeds.
It wrote the SHA-256 of 18 files, the design parameters and the sample to
`results/package3/FREEZE_fullwiki.json` at 2026-10-06T07:43:08+00:00. That file lists every
candidate title of the 300 confirmatory and 10 smoke questions, so the authors keep it with the
records and it is not in this repository. Its SHA-256 is
`2097df870e2b1a4803188f9647797dbc626a2c4699d6350231dbf3d5d5457d97`, and it is available on
request. `provenance.json` records that digest and every digest the freeze lists
(`freeze.frozen_sha256`). The frozen protocol and code in this repository, and a rebuild of the
inputs, are checked against those digests.

**Licence of the source data.** HotpotQA (Yang et al., 2018) is released under CC BY-SA 4.0. The
identifiers, supporting-paragraph indices and digests in this directory are derived from that
release, with attribution to it. The text-bearing records, and the freeze with its titles, are
omitted, so no benchmark text is redistributed here: it stays under its own licence and is obtained
from the original release.

## Files

| File | Rows | Content |
|---|---|---|
| `items.jsonl` | 300 | one row per confirmatory question, in drawing order |
| `sample.json` | - | the draw: source file, seed, eligibility, the 520 excluded ids, counts, and the confirmatory and smoke ids with their groups |
| `rankings.jsonl` | 2,100 | 1,500 local rankings (5 rankers x 300 questions) and the 600 RankGPT ranking requests |
| `answers.jsonl` | 7,200 | one row per answer request |
| `analysis_fullwiki.json`, `analysis_fullwiki.md` | - | the analysis output (`harness/package3/analyze_fullwiki.py`), numbers only; copies of the files in `results/package3/` |
| `summary.txt` | - | the runner's summary (`harness/package3/run_fullwiki.py --confirm --summary`), numbers only |
| `provenance.json` | - | SHA-256 of the freeze and every digest it lists, of the local inputs, the analysis files and the code at export time; the local models' revisions; counts |

The export is written by `harness/package3/export_fullwiki_textfree.py`, which is deterministic
and reads only the local records and package 2's export. It refuses to write unless the freeze
verifies and every frozen input matches its digest. Before writing anything, it rebuilds every one
of the 7,800 prompts from the exported indices and checks it against the recorded SHA-256 and
length, so the exported selections are exactly what was sent.

`harness/package3/check_fullwiki_leaks.py` checks the export in three ways:

- every JSON string is an identifier, digest, label, timestamp or model id;
- no file in this directory or in `harness/package3/` shares 30 or more characters with any
  question, answer, title, paragraph, reply or provider error message in the records;
- no JSON string equals a gold answer, apart from a digit used as a key of a count distribution
  (`3` in `counts.candidates_per_question` of `sample.json` means questions with three
  candidates), which the check lists.

## Conventions

- **Paragraph index:** the 0-based position of a candidate among the question's ten released
  candidates (the `context` of the fullwiki file), in the file's order. The candidates are used as
  released: a supporting paragraph may be missing, and none is ever inserted.
- **Supporting paragraphs** are the candidates whose title is one of the question's
  `supporting_facts` titles.
- **Group:** `sufficient` when both supporting titles are among the candidates, otherwise
  `complement`. It is decided from the annotation alone, never from a ranking or a reply.
- **Row order** follows the source records: drawing order for questions, and the order in which the
  receipts were written for requests. The analysis sorts by question id, so its intervals do not
  depend on row order. Keep the order anyway: the order of the models in the answer-line line of
  `analysis_fullwiki.md` follows their first appearance.
- `null` means not applicable or not available, for example the scores of a request that received
  no response.
- **Digests** are SHA-256, hex, of the UTF-8 bytes of the string.
- **Requested model ids** are constant per label, so they are not repeated per row: Haiku-4.5 is
  `claude-haiku-4-5`, GPT-5.5 is `gpt-5.5` and DeepSeek-V4-Pro is `DeepSeek-V4-Pro`. RankGPT ran on
  Haiku-4.5.

## Fields

### `items.jsonl`

| Field | Meaning |
|---|---|
| `id` | HotpotQA question id (24 hex digits) |
| `dataset`, `setting`, `role` | `hotpotqa`, `fullwiki`, `fullwiki_rank` |
| `type`, `level` | HotpotQA's question type (`bridge`, `comparison`) and level (`hard` for every question here) |
| `eligible` | the eligibility rule holds: exactly 10 released candidates and 2 distinct supporting titles (true for every confirmatory question) |
| `n_candidates`, `n_supporting_titles` | 10 and 2 |
| `supporting` | the indices of the supporting candidates (none, one or two) |
| `supporting_in_pool` | their number |
| `group` | `sufficient` or `complement` |
| `n_gold_answers` | 1, HotpotQA's answer |
| `question_sha256` | digest of the question string |
| `supporting_title_sha256` | digests of the two supporting titles, in sorted title order, including titles missing from the candidates |
| `title_sha256`, `text_sha256` | one digest per candidate, in index order, of its title and of its text. The text is the paragraph's sentences concatenated with no separator (`fullwiki_data.convert`), with no-break spaces kept as released |

### `sample.json`

| Field | Meaning |
|---|---|
| `source` | the fullwiki validation file: name, URL, size, SHA-256 and licence (SPDX id) |
| `seed` | 20261007: the non-excluded ids, in file order, are shuffled once with `random.Random(seed)`; the first 300 eligible ids form the confirmatory sample and the next 10 eligible ids the smoke items (`fullwiki_data.draw`) |
| `eligibility` | 10 candidates and 2 supporting titles |
| `excluded` | the 520 HotpotQA questions used before: package 2's confirmatory items, its development pool (which holds its pilot items) and its excluded list (the 2 October sample, also the source of the stage-2 items). Count, sorted ids, the SHA-256 of the ids joined by a line feed, and where package 2's export lists them |
| `counts` | as recorded at the draw: questions in the file, candidates and supporting titles per question, eligibility, exclusions, positions read in the draw, group sizes, types |
| `supporting_text_check` | supporting candidates whose text equals the distractor file's gold paragraph (322), equals it except for no-break spaces (18), or differs (0) |
| `bm25_idf` | paragraphs over which BM25's IDF is computed (73,642), query tokens (1,947), tokens with a document frequency (1,915), and `df_sha256`, the SHA-256 of the document frequencies as JSON with sorted keys and no spaces |
| `confirm` | id, group and `supporting_in_pool` of the 300 confirmatory questions, in drawing order |
| `smoke` | the same for the 10 smoke questions. They were drawn after the 300, were used only by the smoke run (development data) and are not otherwise exported |
| `ineligible_skipped_ids` | ineligible ids met during the draw (none) |

### `rankings.jsonl`

Every row has `kind` (`local` or `rankgpt`), `ranker`, `item`, `order`, `top_k` and `scores`.
`order` is the complete ranking as candidate indices, best first, and `top_k` is its first K = 2,
the selection of the ranker's answer condition. `ranker` is one of `bm25`, `mmr`, `bge`, `e5`,
`minilm` or `rankgpt`.

**Local rankers** (`kind` = `local`, 1,500 rows). Each row is a complete ordering of the ten
candidates by package 2's `harness/package2/rank_local.py`, run unchanged: BM25 (k1 = 1.5,
b = 0.75), MMR on BGE embeddings (lambda = 0.5), BGE-small, E5-small, or the MiniLM cross-encoder.
BM25's IDF is taken over every paragraph of the fullwiki file. `scores` are the ranker's scores per
candidate index: the BM25 score, the cosine similarity for `bge` and `e5`, the cross-encoder score
for `minilm`, and `null` for `mmr`, a greedy selection that has no single score. Ties go to the
lower index. The checkpoints' revisions and file digests are in `provenance.json`
(`local_models`).

**RankGPT** (`kind` = `rankgpt`, 600 rows). Each row is one listwise ranking request:

| Field | Meaning |
|---|---|
| `id` | `rank\|Haiku-4.5\|<item>\|o0` or `...\|o1` |
| `model` | `Haiku-4.5` |
| `order_idx` | 0: the file's order, used for answering. 1: a seeded shuffle (seed 20261005 and the question id), used for stability only |
| `used_for_answers` | true for the order-0 row when a response was received |
| `size` | 10 |
| `pool` | the input order: the candidate indices presented as passages [1] to [10] |
| `order`, `top_k` | the parsed ranking as candidate indices (`run_qa.parse_ranking`, below) |
| `parse.returned` | distinct in-range identifiers in the reply |
| `parse.duplicates` | repeated identifiers, dropped |
| `parse.out_of_range` | identifiers outside 1..10, dropped |
| `parse.appended` | identifiers missing from the reply, appended in input order (10 minus returned) |
| `parse.complete` | the reply ranked every passage |
| `parse.repaired` | the repair rule changed the reply: an identifier was dropped or appended |

Each row also has the request fields described below.

`run_qa.parse_ranking` reads the bracketed identifiers in reply order. It drops duplicates and
out-of-range identifiers and appends any missing ones in input order, as RankGPT specifies. A
parsed response is never retried, whatever it contains.

### `answers.jsonl`

| Field | Meaning |
|---|---|
| `id` | `ans\|<model>\|<item>\|<cond>` |
| `item`, `group`, `model` | the question, its group and the answering model |
| `cond` | the condition (see below) |
| `context` | the candidate indices presented, in order, as passages [1] to [k]; `null` for `none` (no context block) |
| `em`, `f1` | official HotpotQA exact match and F1 of the answer read from the reply (`run_qa.score`); `null` without a response |
| `contains` | 1.0 if the normalized gold answer occurs anywhere in the normalized reply. A diagnostic only; the analysis does not use it |
| `has_answer_line` | the reply contains an `Answer:` line (the answer-line compliance count) |

The conditions are:

- `none`: no context.
- `full`: all ten candidates, in the file's order.
- `bm25`, `mmr`, `bge`, `e5`, `minilm`, `rankgpt`: the ranker's top 2 candidates in rank order.
  RankGPT's are those of its order-0 ranking.

`run_qa.score` reads the answer from the reply's last `Answer:` line, or the last line when there
is none.

Each row also has the request fields described below.

### Request fields

These fields appear in the RankGPT rows of `rankings.jsonl` and in every row of `answers.jsonl`.

| Field | Meaning |
|---|---|
| `issued_utc` | when the request was issued (ISO 8601, UTC) |
| `wall_s` | wall-clock seconds for the request, every attempt and back-off included |
| `returned_model` | the model id the endpoint reported; `null` without a response |
| `response_id` | the provider's response id; `null` without a response |
| `stop_reason` | as reported (see below); `null` without a response |
| `incomplete_reason` | GPT-5.5 `incomplete_details.reason`: `max_output_tokens` or `content_filter` |
| `filtered_categories` | categories the provider's content filter marked as filtered in a received response, as `source:category` |
| `transport_failed` | every attempt failed, so the request is missing |
| `missing_reason` | `content_filter` when every attempt was refused by the provider's content filter, else `transport_error`; `null` when received |
| `attempts` | attempts made: up to three, 2 s and 4 s apart, on any exception |
| `attempt_log` | per attempt, when there was more than one or an error (see below); `null` when the first attempt returned HTTP 200 |
| `input_tokens`, `output_tokens` | as reported. These are `input_tokens` and `output_tokens`, or `prompt_tokens` and `completion_tokens` for chat completions, as `run_qa.toks` reads them |
| `reasoning_tokens` | GPT-5.5 `output_tokens_details.reasoning_tokens` |
| `cached_input_tokens` | GPT-5.5 `input_tokens_details.cached_tokens`; DeepSeek `prompt_tokens_details.cached_tokens` where reported; Haiku `cache_read_input_tokens` |
| `total_tokens` | as reported by GPT-5.5 and DeepSeek |
| `status` | `received`, or for a missing request `failed_http400` when every attempt ended in HTTP 400 (where content-filter refusals fall) and `failed_other` otherwise: the classes of the analysis's request accounting |
| `http_status` | the HTTP status of the last attempt: 200 when received |
| `error_class` | for a missing request, the provider's error code at its last attempt; `null` when received |
| `prompt_sha256` | digest of the exact prompt sent |
| `prompt_chars` | its length in characters |

The reported stop reasons are `end_turn` (Anthropic Messages), `completed` or `incomplete`
(OpenAI Responses), and `stop` or `length` (chat completions).

Each `attempt_log` entry gives `attempt`, `start_utc`, `end_utc`, `http_status`, `error_class`,
`filter_source`, `filter_label` and `prompt_tokens`:

- `error_class` is the provider's error code, or the exception type when there was no HTTP
  response.
- `filter_source` is `prompt` or `completion`.
- `filter_label` is the provider's label, where the stored error names one.
- `prompt_tokens` is the input tokens the error body reports.

The usage fields that are not exported held a single value in every record, and the export asserts
this:

- Haiku: `cache_creation_input_tokens` and `cache_creation.ephemeral_{5m,1h}_input_tokens` are 0,
  `service_tier` is `standard` and `inference_geo` is `not_available`.
- GPT-5.5: `input_tokens_details.cache_write_tokens` is 0.
- DeepSeek: `audio_prompt_tokens` is 0.

## Missingness and transport

- 7,800 requests were issued and 7,800 receipts were written: 600 RankGPT and 7,200 answer
  requests. No request was interrupted, and every question received both RankGPT rankings, so all
  7,200 planned answer requests were made.
- **13 requests are missing.** All are answer requests, on four questions. Each was refused by the
  provider's content filter with HTTP 400 at all three attempts:
  - 9 GPT-5.5 requests, where Azure OpenAI blocked the prompt (`filter_source` = `prompt`);
  - 4 DeepSeek requests, where the reply was blocked (`filter_source` = `completion`, label
    `MultiSeverity_SexualScore`).

  They are missing from their cells, and every paired contrast uses the questions that are
  complete in both arms. The worst-case analysis counts every missing outcome against RankGPT. The
  filter acts on the presented paragraphs, so this missingness can depend on the ranker.
- **Received and scored as received:**
  - 4 GPT-5.5 replies are `incomplete`. In 2, `max_output_tokens` was reached (8,000 output
    tokens, all reasoning) and the reply is empty. In the other 2, `content_filter` cut the output;
    their response reported 0 tokens and the category `completion:protected_material_text`. None of
    the 4 has an answer line, and each scores 0.
  - Five GPT-5.5 answers succeeded after HTTP 500 (`server_error`): four at the second attempt, one
    at the third.
  - One DeepSeek answer succeeded at its second attempt after a content-filter refusal (label
    `MultiSeverity_HateSpeechScore`).
- No ranking request failed or needed a retry. 588 of the 600 RankGPT replies ranked every passage:
  291 of 300 in order 0 and 297 of 300 in order 1. Of the other 12, 9 named no passage and 3 named
  two to four; the missing ones were appended in input order. Another 16 replies were complete but
  repeated identifiers, which were dropped.

## Rebuilding the inputs from the public release

1. **Obtain the source file** and check its SHA-256: HotpotQA's fullwiki validation split as
   parquet, from the Hugging Face dataset `hotpotqa/hotpot_qa`, config `fullwiki`, split
   `validation` (the URL is in `sample.json`). Save it as
   `natural_data/hotpot_dev_fullwiki.parquet`. It has 28,041,820 bytes and SHA-256
   `78933c0a31a5f7b420d4effdf4cd4eed573b28c6a3da6179dcf7a02b39e51d03`.
2. **Rebuild and check:** `python harness/package3/verify_fullwiki_textfree.py --rebuilt` (needs
   PyArrow). It uses the released code (`harness/package3/fullwiki_data.py`):
   - it draws the sample again (seed 20261007, without the 520 ids in `sample.json`) and must obtain
     the 300 confirmatory questions in order and the 10 smoke questions;
   - it rebuilds their items with `fullwiki_data.convert` and `annotate`, and compares every
     question, title, text and supporting-title digest, the supporting indices and the group with
     `items.jsonl`;
   - it recomputes BM25's document frequencies over every paragraph of the file;
   - it checks the SHA-256 of the rebuilt `items_confirm.jsonl`, `items_smoke.jsonl` and
     `idf_fullwiki.json` against the digests frozen before any request, as `provenance.json`
     records them (`freeze.frozen_sha256`);
   - it rebuilds all 7,800 prompts from the exported pools and context indices and compares each
     with `prompt_sha256`.

   Add `--write` to save the three rebuilt files to `natural_data/package3/`. Each is written only
   if it is absent and only if its digest matches.
3. **Rank locally (optional).** This needs sentence-transformers and the checkpoints
   `BAAI/bge-small-en-v1.5`, `intfloat/e5-small-v2` and `cross-encoder/ms-marco-MiniLM-L-6-v2` at
   the revisions in `provenance.json`; download them first, since the script loads them with
   network access disabled. Then run
   `<venv>/python harness/package3/run_fullwiki.py --phase local`, which reads the rebuilt items
   and IDF table and writes `rankings_local_confirm.jsonl`, `rankings_local_smoke.jsonl` and
   `local_models.json`. The
   phase refuses to run where the freeze exists, so that the authors' frozen rankings are never
   recomputed in place; a clone of this repository has no freeze. The orders should equal
   `rankings.jsonl`, and `--rebuilt` compares them when the file is present. Scores can differ in
   their last digits across library versions and hardware. The frozen file's SHA-256 is in
   `provenance.json` (`freeze.frozen_sha256`).

The model replies themselves cannot be rebuilt: provider-default sampling is not deterministic
and endpoints change. With the rebuilt prompts and the request settings in
`harness/replication/transport.py`, the requests can be sent again; the stored replies are
available from the authors on request.
