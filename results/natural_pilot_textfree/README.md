# 2 October exploratory pilot: text-free records

This is the public record of the exploratory natural-data pilot of 2 October 2026, 19:00 to 19:22
UTC. The manuscript reports it with the limitations (2,430 requests). It is **development data**:
it tested the measurement, and no confirmatory result uses it.

The pilot applied the source-pair design to two kinds of pair: a TAT-QA report's table and its
text, and a HotpotQA question's two gold paragraphs.

- **Items:** 81 (45 TAT-QA, 36 HotpotQA).
- **Conditions:** `none`, `A`, `B`, `AB` and `BA`, three draws each.
- **Models:** Haiku-4.5 and DeepSeek-V4-Pro.
- **Request:** the replication's one-message request, 8,000 output tokens, provider-default
  decoding.

The code is in `harness/natural/`. The text-free export is written by
`harness/package2/export_qa_textfree.py`.

```bash
python harness/package2/verify_qa_textfree.py     # recomputes the pilot's PASS tables from these files
```

## What is released and what is not

**Released:** item ids mapped to the public datasets' ids (TAT-QA document and question uids,
HotpotQA question ids and paragraph indices); task, source and condition labels; the Stage 1 audit
verdicts as labels; PASS and F1 for every reply; missingness and resource use; and SHA-256 digests
of every question, every source (A, B) and every prompt.

**Not released:**

- the questions and gold answers;
- the sources themselves: TAT-QA tables and texts, and HotpotQA paragraphs;
- the replies;
- the reasons and notes of the Stage 1 judgements, which are prose that names entities from the
  items;
- the sample-reply table of the generated report.

These records reproduce benchmark or reply text. They are kept by the authors and are available on
request. The report's PASS table is reproducible from `requests.jsonl`.

**Licences of the source data:** TAT-QA (Zhu et al., 2021), CC BY 4.0, and HotpotQA (Yang et al.,
2018), CC BY-SA 4.0. The ids, indices and digests here are derived from those releases, with
attribution to them. Their text stays under its own licence.

## Files

| File | Rows | Content |
|---|---|---|
| `stage1_audit.jsonl` | 40 | the Stage 1 sample (20 TAT-QA documents, 20 HotpotQA questions) and its audit verdicts |
| `items.jsonl` | 81 | the pilot items |
| `requests.jsonl` | 2,430 | one row per request, in the order the receipts were written |
| `provenance.json` | - | SHA-256 of the local inputs, the code and the two source files; counts |

## Fields

### `stage1_audit.jsonl`

**TAT-QA rows** (`T00` to `T19`):

| Field | Meaning |
|---|---|
| `item` | the document's position in the Stage 1 sample |
| `tatqa_doc_uid` | the document's table `uid` |
| `questions[]` | the sampled questions, one per kind present |
| `questions[].kind` | `table`, `text` or `table-text` |
| `questions[].tatqa_question_uid` | the question's `uid` |
| `questions[].answer_type` | TAT-QA's `answer_type` |
| `questions[].scale` | TAT-QA's `scale` |
| `questions[].evidence_in_table`, `evidence_in_text` | the automated evidence screen of `stage1_sample.py` |
| `questions[].verdict` | `keep`, `keep-f1` (keep; a long answer scored by token F1) or `exclude` |

**HotpotQA rows** (`H00` to `H19`):

| Field | Meaning |
|---|---|
| `item` | the question's position in the Stage 1 sample |
| `hotpotqa_id` | the question's `id` |
| `type` | `bridge` or `comparison` |
| `gold_paragraphs` | indices, in the question's 10-paragraph `context`, of the two gold paragraphs in `supporting_facts` order. These are sources A and B |
| `original_verdict` | verdict on the original two-paragraph question |
| `leak_noted` | the auditor noted that a model may know the answer without context |
| `subquestions[]` | the single-paragraph questions written for the design |
| `subquestions[].source` | `P1` or `P2` |
| `subquestions[].in_own`, `in_other` | an answer alias occurs, after normalization, in that question's own paragraph, or in the other one |
| `subquestions[].verdict` | `keep` or `exclude` |

### `items.jsonl`

| Field | Meaning |
|---|---|
| `id` | `T##-<kind>` (TAT-QA document and question kind) or `H##-sq1`, `H##-sq2`, `H##-orig` (HotpotQA sub-question or original question) |
| `dataset` | `tatqa` or `hotpotqa` |
| `task` | `table`, `text` or `table-text`; `single-` or `original-` followed by `bridge` or `comparison` |
| `own` | the source that answers the question: `A`, `B`, or `AB` (needs both) |
| `score_kind` | the scorer branch (see below) |
| `scale` | TAT-QA's scale label |
| `question_origin` | `dataset` (the benchmark's own question) or `project` (a single-paragraph question written for the pilot, in `harness/natural/stage1_annotate.py`) |
| `stage1_verdict` | the item's Stage 1 verdict |
| `exclusive` | TAT-QA single-source questions: `false` for the three that the other source also answers by arithmetic on its figures (`T09-table`, `T18-table` and `T17-text`, found when the replies were read), `true` otherwise; `null` where the check does not apply |
| `source` | where the item comes from (see below) |
| `question_sha256` | digest of the question string |
| `A_sha256`, `B_sha256` | digests of the two sources exactly as sent (see below) |

The values of `score_kind` are `number`, `span`, `multi`, `long` (token F1 against a threshold) and
`aliases`.

The `source` field holds:

- for TAT-QA: `tatqa_doc_uid`, `tatqa_question_uid` and `answer_type`;
- for HotpotQA: `hotpotqa_id`, `hotpotqa_type`, `A_paragraph` and `B_paragraph` (indices in the
  question's `context`), and `subquestion` (1, 2, or `null` for the original question).

The sources are digested exactly as sent:

- TAT-QA A is `Table:` and a newline, followed by the table rows, with each cell stripped of
  surrounding whitespace, cells joined by ` | ` and rows by newlines.
- TAT-QA B is `Text:` and a newline, followed by the paragraphs in order, joined by blank lines.
- HotpotQA A and B are the title, a newline and the paragraph.

### `requests.jsonl`

| Field | Meaning |
|---|---|
| `id` | the schedule id: `<model>\|<item>\|<condition>\|<draw>` |
| `item`, `model` | the item and the model |
| `condition` | `none`, `A`, `B`, `AB` (A then B) or `BA` |
| `draw` | 0, 1 or 2 |
| `window` | `pilot` |
| `seq`, `lane` | position in the model's shuffled schedule (seed 20261003) and its lane |
| `pass` | PASS under `harness/natural/scoring.py` (as in the repository; identical to the pilot report's scores for all 2,430 replies) |
| `f1` | token F1 for `long` items, `null` otherwise |
| `refusal` | the scorer's refusal pattern matched (such a reply fails) |
| `has_number` | `number` items: the reply contains a number; `null` otherwise |
| `issued_utc`, `end_utc` | when the request was issued and when its receipt was written (UTC) |
| `wall_s` | `end_utc` minus `issued_utc`, in seconds |
| other request fields | as in `../package2/confirm_qa_textfree/README.md`: `returned_model`, `response_id`, `stop_reason`, `incomplete_reason`, `filtered_categories`, `transport_failed`, `missing_reason`, `attempts`, `attempt_log`, the token fields and `prompt_sha256` |

The requested model ids are `claude-haiku-4-5` for Haiku-4.5 and `DeepSeek-V4-Pro` for
DeepSeek-V4-Pro.

## Missingness and transport

All 2,430 requests received a response; none failed. Three succeeded at their second attempt,
after an HTTP 500, a timeout and a connection error respectively; these are in `attempt_log`. The
stop reasons are `end_turn` (1,215, Haiku) and `stop` (1,215, DeepSeek).

## Rebuilding the full records from the public releases

1. Obtain TAT-QA dev (`tatqa_dataset_dev.json`, SHA-256
   `8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5`) and HotpotQA dev in the
   distractor setting as parquet (`hotpot_dev_distractor.parquet`, SHA-256
   `c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6`) into `natural_data/`.
2. Run `python harness/natural/stage1_sample.py` (seed 20261002; pandas, PyArrow), then
   `python harness/natural/stage1_annotate.py` (the audit and the single-paragraph questions),
   then `python harness/natural/stage2_pilot.py build` (items and schedule).
3. Run `python harness/package2/verify_qa_textfree.py --rebuilt`. It compares the question and
   source digests of all 81 items and rebuilds all 2,430 prompts, comparing each with its
   `prompt_sha256`.

The replies cannot be rebuilt. With the rebuilt prompts, the requests can be sent again.
