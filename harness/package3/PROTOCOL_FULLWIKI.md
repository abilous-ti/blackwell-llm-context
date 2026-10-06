# Package 3: listwise reranking on HotpotQA's retrieved candidates (fullwiki setting)

Status: written 6 October 2026, before any request of this package and before any ranker output
on its questions was seen. It is frozen with the code, the items, the local rankings and the seeds
(SHA-256 in `results/package3/FREEZE_fullwiki.json`) before the first request; `run_fullwiki.py`
refuses the confirmatory run unless the freeze verifies. Nothing below changes after the freeze;
any departure is reported as a deviation.

## 1. Question

Package 2 (PROTOCOL.md, Section 2) compared RankGPT with five local rankers at a matched budget on
HotpotQA's distractor pools, where both supporting paragraphs are always among the ten candidates.
Here the ten candidates are the paragraphs HotpotQA's own retrieval system returned (fullwiki
setting), so a supporting paragraph may be missing from the pool. The test asks whether the
advantage seen on supplied pools carries over to retrieved pools.

## 2. Data

- Source: `natural_data/hotpot_dev_fullwiki.parquet`, downloaded 6 October 2026 from
  https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/fullwiki/validation-00000-of-00001.parquet
  (28,041,820 bytes; SHA-256 78933c0a31a5f7b420d4effdf4cd4eed573b28c6a3da6179dcf7a02b39e51d03, equal to
  the server's own hash and appended to `natural_data/SHA256SUMS.txt`; CC BY-SA 4.0, the same source
  as the distractor file; not redistributed, as `natural_data/` is not tracked).
- 7,405 questions, the same ids as the distractor file. Conversion as package 2's
  `qa_data.load_hotpot`: a paragraph's text is its sentences joined; the answer list is the answer.
- Candidates are used exactly as released. No gold paragraph is ever inserted, and nothing is
  reordered before ranking; the file order is input order o0, as in package 2. A candidate counts as
  supporting when its title is one of the question's `supporting_facts` titles. In the sample, every
  supporting candidate's text equals the distractor file's gold paragraph (18 of 340 differ only by
  no-break spaces, kept as released).

## 3. Sample and subgroup

- Exclusion by `_id` of every HotpotQA question used before, 520 in all: package 2's confirmatory
  items (300: ranking and augmentation), its pilot items (50), its development pool (200, which
  contains the pilot items) and its excluded list (20 = the stage-1 sample), the stage-1 sample and
  the stage-2 items built from it (H00-H19 = the same 20 questions). A byte scan of every repository
  file except the dataset files and package 2's list of its never-read confirmation pool (or any
  copy of that list) found 520 validation ids, none beyond these sources.
- Eligibility, from the annotation and the pool size only (never from retrieval success or any
  model output): exactly 10 released candidates and 2 distinct supporting titles. In the file, 7,342
  of 7,405 questions are eligible (63 have fewer than 10 candidates; every question has two
  supporting titles); among the 6,885 not excluded, 6,824.
- Draw: the 6,885 non-excluded ids in file order, shuffled once with `random.Random(20261007)`; the
  first 300 eligible ids form the confirmatory sample, the next 10 eligible ids the smoke items, so
  the smoke run never touches a confirmatory question. No ineligible id came up among the 310
  positions read. The draw is deterministic and was fixed before any request.
  `fullwiki_data.py --verify-draw` recomputes it without writing anything and reproduced the items
  and the IDF table exactly. Ids, candidate titles and groups are recorded in
  `natural_data/package3/sample.json` and in the freeze.
- Subgroup "sufficient candidate evidence": both supporting titles are among the 10 released
  candidates; complement: at least one is missing. It is decided from the `supporting_facts` titles
  alone and recorded in every item (`group`). Sample: 90 sufficient, 210 complement (150 with one
  supporting paragraph among the candidates, 60 with none). In the whole file, 2,089 of the 7,342
  eligible questions are sufficient.

## 4. Rankers, budget, conditions and requests

- Local rankers, package 2's `rank_local.py` run unchanged: BM25 (k1 = 1.5, b = 0.75), MMR
  (lambda = 0.5 on the BGE embeddings), BGE-small, E5-small and the MiniLM cross-encoder, from the
  local model cache with network access disabled. These are the same cached checkpoints as in
  package 2; their revisions and file hashes are in `natural_data/package3/local_models.json`,
  which is frozen. BM25's IDF is taken over every paragraph of the
  fullwiki file (73,642 paragraphs, each counted once per question it appears in, as
  `rank_local.idf_table` counts), mirroring package 2's "IDF over every paragraph of the source
  dataset". It is stored for the query vocabulary only, which is exact because BM25 reads no other
  IDF. The local rankings are computed once, before the freeze, and frozen.
- RankGPT: Haiku-4.5 with `run_qa.RANK_PROMPT` (the listwise prompt of Sun et al., 2023) over the
  10 candidates in two input orders, o0 = file order (used for answering) and o1 = `run_qa`'s seeded
  shuffle (seed 20261005 and the question id; for stability only). Package 2's repair and retry rule:
  identifiers are read in reply order, out-of-range or repeated ones are ignored, and missing ones
  are appended in input order (`run_qa.parse_ranking`). The transport makes up to three attempts,
  2 s and 4 s apart, on any exception; a parsed response is never retried, whatever it contains.
- Budget K = 2: each ranker's top two paragraphs, in rank order.
- Answer models: Haiku-4.5, GPT-5.5, DeepSeek-V4-Pro, with package 2's answer prompts (reasoning
  allowed, a required final line `Answer: <answer>`; the scorer reads the last such line, or the last
  line if none).
- Conditions per question and model: none; full (all 10 candidates, file order); bm25, mmr, bge, e5,
  minilm and rankgpt (top 2 of each).
- Requests: 300 x 2 = 600 ranking requests, then 300 x 8 x 3 = 7,200 answer requests, 7,800 in all.
  A question whose o0 ranking fails in transport gets no RankGPT answers: 3 fewer requests per such
  question, recorded and not imputed. Smoke: N smoke questions x 26 requests (RUNBOOK: N = 2, so 52).
  Four concurrent lanes per model, as in package 2's confirmatory run.
- Records: `issued` before and `receipt` after each request, each written and synced before that
  lane's next request. A request is issued at most once. One issued without a receipt (a crash in
  flight) is "interrupted": a missing observation, never requested again. Rerunning the command
  resumes. Three consecutive transport failures halt a lane. One run per record directory (lock
  file). The disk guard refuses to start a live run with less than 300 MB free on the records'
  drive, and with less than 100 MB free every lane stops before its next request, so the run
  resumes later and no saved reply is lost. Ctrl+C stops the same way.

## 5. Endpoints

- Evidence coverage at K = 2:
  - Support recall: the question's supporting paragraphs in the top 2, divided by its 2 supporting
    paragraphs, so a paragraph the retrieval missed counts as not retrieved. Reported over all 300
    questions and per subgroup.
  - All supporting paragraphs in the top 2: reported within the sufficient subgroup (the only
    questions where it is possible) and over all questions.
  - Retrieval coverage: supporting paragraphs among the 10 candidates, the ceiling for every ranker.
- Answer quality: official HotpotQA exact match and F1 (`run_qa.score`).
- RankGPT resource use: latency, input and output tokens, extra attempts, complete parses, and
  top-2 agreement and Kendall tau between o0 and o1.

## 6. Analysis

- Primary family (15 statements): RankGPT minus each of the five local rankers on F1, for each of
  the three answer models. It covers all 300 questions; those whose evidence was never retrieved
  stay in. Intervals are paired percentile bootstrap over questions (`analyze_qa.boot_mean`: 4,000
  resamples, seed 20261005), simultaneous 95% by Bonferroni over the 15 (level 1 - 0.05/15), with
  approximate coverage, exactly as in `analyze_qa.py`. A contrast is verified positive if its lower
  bound is above 0, and verified negative if its upper bound is below 0.
- Secondary family (30 statements, its own Bonferroni level 1 - 0.05/30): the same 15 contrasts
  within the sufficient subgroup and the same 15 within the complement.
- Evidence criterion (5 statements, level 1 - 0.05/5): RankGPT minus each local ranker on support
  recall at K = 2 over all 300 questions. It holds when all five are verified positive.
- Descriptive, with 95% intervals: the coverage table per ranker and subgroup; the full-pool and
  no-context references; exact match and F1 per model, condition and subgroup; RankGPT resource use;
  answer-line compliance.
- Missing outcomes:
  - Reported by kind: transport failures with HTTP 400 on every attempt (where content-filter
    refusals fall, as in package 2) apart from other transport failures; interrupted requests;
    RankGPT answers not requested because the o0 ranking failed.
  - Each contrast uses the questions where both arms have an outcome (package 2's rule). A reply
    that arrives is scored as it is, refusals included.
  - Worst-case sensitivity for the primary family: all 300 questions, every missing outcome counted
    against RankGPT (a missing RankGPT answer scores F1 0, a missing comparator answer F1 1).
- The analysis verifies the freeze and reports the result.

## 7. Pre-declared interpretation

| Result | Reading |
|---|---|
| Improvement in evidence and answers | The practical advantage extends to these retrieved pools. |
| Improvement mainly in the sufficient subgroup | Candidate retrieval coverage limits the benefit of reranking. |
| Little or no improvement | The advantage has narrower scope than the supplied-pool benchmark suggested. |
| Decrease | The tested reranking configuration needs qualification in this setting. |

Reading rules, applied mechanically by `analyze_fullwiki.py`; the first rule that matches decides.
Notation: P+ and P- are the primary contrasts verified positive and negative (of 15); S+ and C+ the
sufficient-subgroup and complement contrasts verified positive in the secondary family (of 15 each);
E means the evidence criterion holds.

1. Decrease: P- >= 8.
2. Improvement in evidence and answers: E and P+ >= 8.
3. Improvement mainly in the sufficient subgroup: S+ >= 8 and C+ < 8.
4. Little or no improvement: P+ < 8 and S+ < 8.
5. Otherwise the pattern is not covered by the table: it is reported with all bounds, and no row is
   claimed.

Always reported with the row:
- every verified-negative primary contrast, as a qualification for that model and ranker;
- under rule 2, whether S+ >= 8 and C+ < 8 (the improvement is concentrated where retrieval found
  both paragraphs);
- whether the evidence criterion holds;
- whether the worst-case analysis would change the row (the rules re-applied with the worst-case
  primary family, everything else unchanged).

## 8. Reporting and deviations

- Whatever the run shows is reported, including null or unfavourable results. The smoke run is
  development data and enters no analysis.
- Local-ranker evidence figures on the confirmatory items were printed by the mock tests of the
  pipeline before the freeze (as in package 2); no setting depends on them.
- Provenance of the local rankings: the first computation (6 October) started before the offline
  setting took effect, so the Hugging Face hub was contacted. The hub returned a new revision label
  for the cross-encoder repository, but its six files are byte-identical to the cached checkpoint
  (BGE and E5 were unchanged). The cache was restored and the setting fixed in `run_fullwiki.py`. A
  rerun with network access disabled then reproduced both ranking files byte for byte. After the
  mock test, this protocol changed only by this note and by the wording on the draw check and the
  id scan.
- Deviations from package 2's conventions:
  - the candidate pools are the retrieval system's own, so a pool may lack a supporting paragraph;
  - BM25's IDF comes from the fullwiki file;
  - the sample is drawn from the whole validation file minus every question used before (seed
    20261007), not from package 2's confirmation pool;
  - the secondary family, the evidence criterion, the worst-case rule and the reading rules are new;
  - the runner adds an explicit `--confirm` mode with a freeze guard, the disk guard, a graceful
    stop and a lock file, and deterministic but varied mock replies;
  - analysis outputs go to `results/package3/`, while records stay in `natural_data/package3/`.
