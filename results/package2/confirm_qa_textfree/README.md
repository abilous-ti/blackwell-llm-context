# Natural-data benchmarks: text-free records

These files are the public record of the natural-data benchmarks in Sections 4.7 and 5.9 of the
manuscript (Table 12, `tab:natural`; Table 13, `tab:overhead`). They cover the 420 confirmatory
questions and all 9,240 requests collected on 5 October 2026, 08:57 to 13:27 UTC. The 420
questions are 200 HotpotQA ranking questions, 100 HotpotQA augmentation questions, 100 MuSiQue
ranking questions and 20 MuSiQue overhead questions.

Every published number can be recomputed from this directory alone:

```bash
python harness/package2/verify_qa_textfree.py
```

The script recomputes all of `analysis_qa.json` with the analysis code (`analyze_qa.py`,
`run_qa.py`). That covers 807 numbers, bootstrap intervals included, and every one comes out
identical. It then checks the printed values of Tables 12 and 13 and the figures quoted in the
text.

## What is released and what is not

**Released:** question and request identifiers; dataset, role and condition labels; split and pool
membership; paragraph **indices**; every ranking as a list of indices; exact match and F1 for every
answer; parse, missingness and transport status; resource use; and SHA-256 digests. The digests
cover every prompt sent and every question, paragraph title and paragraph text used, so a rebuild
from the public datasets can be checked byte for byte.

**Not released:** question text, gold answers, paragraph titles and texts, the models' replies and
the answers read from them, the providers' response envelopes, and the providers' error messages.
These records reproduce benchmark text or reply text. They are kept by the authors and are
available on request. `provenance.json` gives the SHA-256 of the record file they are in.

**Licences of the source data.** HotpotQA (Yang et al., 2018) is released under CC BY-SA 4.0 and
MuSiQue (Trivedi et al., 2022) under CC BY 4.0. TAT-QA (Zhu et al., 2021; CC BY 4.0) is used only
by the 2 October pilot, whose records are in `../../natural_pilot_textfree/`. The identifiers,
supporting-paragraph indices and digests in this directory are derived from those releases, with
attribution to them. No benchmark text is redistributed here; it stays under its own licence and is
obtained from the original releases.

## Files

| File | Rows | Content |
|---|---|---|
| `items.jsonl` | 420 | one row per confirmatory question |
| `splits.json` | - | seeds, source digests, and development, excluded, pilot and confirmatory membership |
| `confirmation_hotpotqa.txt`, `confirmation_musique.txt` | 7,185 and 2,317 lines | the confirmation pools, one question id per line, in drawing order |
| `rankings.jsonl` | 2,700 | 2,100 local rankings (5 rankers x 420 questions) and the 600 RankGPT ranking requests |
| `answers.jsonl` | 8,400 | one row per answer request |
| `overhead.jsonl` | 240 | one row per ranking request of the overhead study |
| `augmentation.jsonl` | 100 | the design of the augmentation diagnostic, per question |
| `analysis_qa.json`, `analysis_qa.md` | - | the analysis output (`harness/package2/analyze_qa.py`), numbers only |
| `summary.txt` | - | the runner's summary (`harness/package2/run_qa.py --summary`), numbers only |
| `provenance.json` | - | SHA-256 of the local inputs and of the code at export time; counts |

The export is written by `harness/package2/export_qa_textfree.py`, which is deterministic and
reads only the local records. Before writing anything, it rebuilds every one of the 9,240 prompts
from the exported indices and checks it against the recorded SHA-256. So the exported selections
are exactly what was sent. `harness/package2/check_textfree_leaks.py` checks that no exported file
shares 30 or more characters with any question, answer, paragraph or reply in the records.

## Conventions

- **Paragraph index:** the 0-based position of a paragraph in its question's candidate pool, in
  the dataset's own order. For HotpotQA (distractor setting) this is the 10 entries of `context`;
  for MuSiQue, the 20 entries of `paragraphs`.
- **Supporting paragraphs** come from the datasets' annotations. For HotpotQA they are the
  paragraphs whose title appears in `supporting_facts`; for MuSiQue, those with `is_supporting`.
- **Row order** follows the source records: the order in which the receipts were written for
  requests, and the items file's order for questions. The bootstrap in `analyze_qa.py` resamples in
  that order, so keep it to reproduce the intervals exactly.
- `null` means not applicable or not available, for example the scores of a request that received
  no response.
- **Digests** are SHA-256, hex, of the UTF-8 bytes of the string.
- **Requested model ids** are constant per label, so they are not repeated per row: Haiku-4.5 is
  `claude-haiku-4-5`, GPT-5.5 is `gpt-5.5` and DeepSeek-V4-Pro is `DeepSeek-V4-Pro`. RankGPT and
  every ranking request of the main benchmarks ran on Haiku-4.5. The overhead study used Haiku-4.5
  and GPT-5.5.

## Fields

### `items.jsonl`

| Field | Meaning |
|---|---|
| `id` | the dataset's question id: HotpotQA `id` (24 hex digits) or MuSiQue `id` |
| `dataset` | `hotpotqa` or `musique` |
| `role` | `hotpot_rank` (ranker comparison, K = 2), `hotpot_aug` (augmentation diagnostic), `musique_rank` (ranker comparison, K = 4), `musique_overhead` (overhead study) |
| `split` | `confirmation`: every confirmatory question comes from a confirmation pool |
| `type` | HotpotQA question type (`bridge`, `comparison`); for MuSiQue, the hop pattern in the id prefix (`2hop`, `3hop1`, ...) |
| `n_paragraphs` | pool size: 10 (HotpotQA) or 20 (MuSiQue) |
| `supporting` | the supporting paragraph indices |
| `n_gold_answers` | number of gold strings the scorer maximizes over: HotpotQA's answer, or MuSiQue's answer plus its aliases |
| `question_sha256` | digest of the question string |
| `title_sha256`, `text_sha256` | one digest per paragraph, in index order, of its title and of its text. The HotpotQA text is the paragraph's sentences concatenated with no separator, as `harness/package2/qa_data.py` builds it; the MuSiQue text is `paragraph_text` |
| `augment_distractors` | `hotpot_aug` only: the two added distractor indices |

### `splits.json`

| Field | Meaning |
|---|---|
| `seed` | 20261005, the seeded shuffle that splits each dataset into a development and a confirmation pool (`qa_data.py`) |
| `confirm_draw_seed` | 20261006, the shuffle of the confirmation pool from which the confirmatory questions are taken in order, subject to the eligibility rules in `qa_data.py` |
| `dev_size` | development pool sizes |
| `sources_sha256` | SHA-256 of the two source files |
| `datasets.<d>.excluded` | ids excluded before splitting: the 20 HotpotQA questions of the 2 October pilot |
| `datasets.<d>.dev` | the development pool in shuffled order. Only pilots and tuning drew from it |
| `datasets.<d>.confirmation_size`, `confirmation_sha256`, `confirmation_file` | the confirmation pool. The digest is of its ids joined by a line feed, which is the file without its final newline |
| `datasets.<d>.pilot_items` | id and role of the items of the 5 October development pilot. Its records are development data and are not exported |
| `datasets.<d>.confirm_items` | id and role of the confirmatory questions, in drawing order |

### `rankings.jsonl`

Every row has `kind` (`local` or `rankgpt`), `ranker`, `item`, `dataset`, `role`, `order` and
`scores`. `order` is the ranking as paragraph indices, best first. `ranker` is one of `bm25`,
`mmr`, `bge`, `e5`, `minilm` or `rankgpt`.

**Local rankers** (`kind` = `local`, 2,100 rows). Each row is a complete ordering of the pool by
`harness/package2/rank_local.py`: BM25, MMR on BGE embeddings, BGE-small, E5-small, or the MiniLM
cross-encoder. `scores` are the ranker's scores per paragraph index: the BM25 score, the cosine
similarity for `bge` and `e5`, the cross-encoder score for `minilm`, and `null` for `mmr`, a greedy
selection that has no single score. Ties go to the lower index. Rankings exist for all 420
questions; the answer conditions use those of the ranking questions.

**RankGPT** (`kind` = `rankgpt`, 600 rows). Each row is one listwise ranking request:

| Field | Meaning |
|---|---|
| `id` | `rank\|Haiku-4.5\|<item>\|o0` or `...\|o1` |
| `model` | `Haiku-4.5` |
| `order_idx` | 0: the dataset's order, used for answering. 1: a seeded shuffle, used for stability only |
| `used_for_answers` | true for the order-0 row when a response was received |
| `size` | pool size |
| `pool` | the input order: the paragraph indices presented as passages [1] to [n] |
| `order` | the parsed ranking as paragraph indices (`run_qa.parse_ranking`, below) |
| `parse.returned` | distinct in-range identifiers in the reply |
| `parse.duplicates` | repeated identifiers, dropped |
| `parse.out_of_range` | identifiers outside 1..n, dropped |
| `parse.appended` | identifiers missing from the reply, appended in input order (size minus returned) |
| `parse.complete` | the reply ranked every passage |

Each row also has the request fields described below.

`run_qa.parse_ranking` reads the bracketed identifiers in reply order. It drops duplicates and
out-of-range identifiers and appends any missing ones in input order, as RankGPT specifies.

### `answers.jsonl`

| Field | Meaning |
|---|---|
| `id` | `ans\|<model>\|<item>\|<cond>` |
| `item`, `dataset`, `role`, `model` | the question and the answering model |
| `cond` | the condition (see below) |
| `context` | the paragraph indices presented, in order, as passages [1] to [k]; `null` for `none` (no context block) |
| `em`, `f1` | official HotpotQA exact match and F1 of the answer read from the reply, maximized over the gold strings (`run_qa.score`); `null` without a response |
| `contains` | 1.0 if a normalized gold string occurs anywhere in the normalized reply. A diagnostic only; the analysis does not use it |
| `has_answer_line` | the reply contains an `Answer:` line (the format-compliance count in `analyze_qa.py`) |

The conditions are:

- `none`: no context.
- `full`: the whole pool.
- `bm25`, `mmr`, `bge`, `e5`, `minilm`, `rankgpt`: the ranker's top K paragraphs in rank order,
  with K = 2 for HotpotQA and 4 for MuSiQue.
- `gold`, `gold+dist`, `dist+gold`: the augmentation conditions.

`run_qa.score` reads the answer from the reply's last `Answer:` line, or the last line when there
is none.

Each row also has the request fields described below.

### `overhead.jsonl`

| Field | Meaning |
|---|---|
| `id` | `over\|<model>\|<item>\|<size>\|o0` or `...\|o1` |
| `model` | `Haiku-4.5` or `GPT-5.5` |
| `size` | 5, 10 or 20 candidates |
| `order_idx` | 0 or 1 (a seeded shuffle of the same candidates) |
| `pool` | the candidates in input order: every supporting paragraph plus seeded distractors (`run_qa.subset_pool`). Size 20 is the whole pool |
| `order`, `parse` | as for RankGPT |
| `k` | number of supporting paragraphs, the K of top-K agreement and recall |
| `recall_at_k` | share of the supporting paragraphs among the first `k` of `order` |

Each row also has the request fields described below. Top-K agreement and Kendall's tau between
the two input orders are computed from the `order` lists of each order-0 and order-1 pair;
`verify_qa_textfree.py` shows how.

### `augmentation.jsonl`

| Field | Meaning |
|---|---|
| `item`, `dataset`, `role` | the question |
| `supporting` | the two supporting paragraph indices: the gold block, in dataset order |
| `eligible_distractors` | the checked distractors: non-supporting paragraphs whose normalized title and text contain no normalized gold answer string (`qa_data.checked_distractors`) |
| `added` | the two distractors added, which are the first two eligible ones |
| `contexts` | the indices each condition presented: `none` (`null`), `gold`, `gold+dist` (appended) and `dist+gold` (prepended) |

### Request fields

These fields appear in the RankGPT rows of `rankings.jsonl` and in every row of `answers.jsonl`
and `overhead.jsonl`.

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

- 9,240 requests were issued and 9,240 receipts were written: 600 RankGPT, 240 overhead and 8,400
  answer requests.
- **13 requests are missing.** All are answer requests, on five questions. Each was refused by the
  provider's content filter at all three attempts:
  - 8 GPT-5.5 requests, where Azure OpenAI blocked the prompt (`filter_source` = `prompt`);
  - 5 DeepSeek requests, where the reply was blocked (`filter_source` = `completion`, with labels
    `MultiSeverity_ViolenceScore`, `MultiSeverity_SexualScore` and
    `MultiSeverity_HateSpeechScore`).

  They are missing from their cells, and every paired contrast uses the questions that are
  complete in both arms. The filter acts on the selected paragraphs, so this missingness can depend
  on the ranker.
- **Received and scored as received:**
  - 7 GPT-5.5 replies are `incomplete`: 4 with `max_output_tokens` and an empty reply, and 3 with
    `content_filter`, where the output was cut by the filter (see `filtered_categories`).
  - 2 DeepSeek replies stopped with `length`.
  - One GPT-5.5 answer succeeded at its second attempt after an HTTP 500 (`server_error`).
  - One GPT-5.5 response reported 0 input tokens.
- No ranking request failed. 591 of the 600 RankGPT replies ranked every passage; the other 9 were
  completed in input order. All 240 overhead rankings parsed completely at the first attempt.

## Rebuilding the full records from the public releases

1. **Obtain the source files** into `natural_data/` and check their SHA-256 (the HotpotQA and
   MuSiQue digests are also in `splits.json`):
   - HotpotQA dev, distractor setting, as parquet: Hugging Face dataset `hotpotqa/hotpot_qa`,
     config `distractor`, split `validation`. Save it as `hotpot_dev_distractor.parquet`,
     SHA-256 `c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6`.
   - MuSiQue v1.0 answerable dev, `musique_ans_v1.0_dev.jsonl` from the MuSiQue release, SHA-256
     `15fa63794d18a94ce12411aca6e2327e65b6e83b0b1490efab3f1962e48abf3b`.
   - TAT-QA dev, `tatqa_dataset_dev.json` from the TAT-QA release, SHA-256
     `8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5`. It is needed only for
     the next step, because the 2 October sample draws its HotpotQA questions after its TAT-QA
     documents.
2. **Draw the pilot sample:** `python harness/natural/stage1_sample.py` (pandas, PyArrow) writes
   `natural_data/stage1/sample.json`. Its 20 HotpotQA ids are `datasets.hotpotqa.excluded` in
   `splits.json`.
3. **Split the datasets:** `python harness/package2/qa_data.py` (PyArrow) writes `splits.json`,
   the confirmation lists and the pilot items. The development lists, pool sizes and confirmation
   digests must equal those here. Compare `splits.json` by content: its line endings follow the
   platform.
4. **Draw the confirmatory questions:** `python harness/package2/qa_data.py --confirm` writes
   `natural_data/package2/items_confirm.jsonl`. The whole file's SHA-256 must be
   `27f7b1dbcdc3dbcc2790495b0175e24f7081ba687dba184f0821b4f5b21054ae`, the digest frozen in
   `results/package2/FREEZE.json` before any confirmatory request. Item by item, the digests in
   `items.jsonl` locate any difference.
5. **Rank locally (optional):**
   `<venv>/python harness/package2/rank_local.py natural_data/package2/items_confirm.jsonl natural_data/package2/rankings_local_confirm.jsonl`.
   This needs sentence-transformers and the checkpoints `BAAI/bge-small-en-v1.5`,
   `intfloat/e5-small-v2` and `cross-encoder/ms-marco-MiniLM-L-6-v2`. The script loads them with
   network access disabled, so download them first. The orders should equal `rankings.jsonl`;
   scores can differ in their last digits across library versions and hardware. The frozen file's
   SHA-256 is `7707ca3046838a642391c9755da0aadcc3b3802c27a1c1b705b5a0ec31253d21`.
6. **Check the rebuild:** `python harness/package2/verify_qa_textfree.py --rebuilt`. It compares
   every question and paragraph digest and the supporting indices, rebuilds all 9,240 prompts from
   the exported pools and context indices, and compares each with `prompt_sha256`. If step 5 was
   run, it also compares the local rankers' orders.

The model replies themselves cannot be rebuilt: provider-default sampling is not deterministic
and endpoints change. With the rebuilt prompts and the request settings in
`harness/replication/transport.py`, the requests can be sent again; the stored replies are
available from the authors.
