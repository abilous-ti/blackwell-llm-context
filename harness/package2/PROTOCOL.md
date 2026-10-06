# Package 2: confirmatory protocol (independent pairs, natural-data benchmarks, overhead)

Status: DRAFT, 5 October 2026, before any confirmatory request. It is frozen (hashes of code,
items, rankings and this file in `results/package2/FREEZE.json`) after the pilot is read for
defects under the rules of `PILOT.md`; only the items PILOT.md lets the pilot set (the matched
budget K, the answer prompt's wording, the sizes below) may change before the freeze, and any change
is listed here with the pilot evidence behind it.

## 1. Independent source pairs across six models (R1.3, R2.5)

- Pairs: cache (published pair 2, unchanged texts and verifiers), inventory and audit (new, strict
  verifiers). Structural incomparability of each pair is proved by its certificate
  (`certify_pairs.py`, Lemma 1 premises checked over the declared family); nothing below measures it.
- Cells per pair: the A-decisive task and the B-decisive task under none, A, B, AB and BA.
  Original-task controls on the same run: the ledger pair's two API tasks under W1, W1plus,
  W1plus_rev and W1pad.
- Design: randomized blocks (one request per arm of one task, random order), blocks interleaved
  at random per model, one collection session; all six models; n = 40 blocks per task and model
  (1,520 requests per model, 9,120 in all); seed 20261006; four lanes per model.
- Primary family (36 one-sided statements): for each pair and model, A - B on the A-task > 0 and
  B - A on the B-task > 0 (PASS incomparability needs both). Bound: the block-difference Hoeffding
  bound of the replication with one window, h = sqrt(2 log(1/alpha) / B), alpha = 0.05 / 36.
- Secondary (reported with their own Bonferroni level, not part of the primary claim): augmentation
  contrasts AB - A and BA - A on the A-task, AB - B and BA - B on the B-task (72 statements; any
  harm only); the controls W1plus_rev - W1, W1pad - W1 and W1plus - W1 on the two ledger tasks
  (36 statements); pooled Clopper-Pearson comparisons for comparability with the paper's original
  analysis; no-context baselines per task and model (leakage, descriptive).
- Missing outcomes: complete blocks only; worst-case imputation as a sensitivity analysis.
- Grading (amended 5 October, after the pilot and before any confirmatory request): the pilot found
  that GPT-5.5, when its context lacked the decisive convention, sometimes gamed equality-based
  checks, returning a str subclass equal to every string or reading the expected value from the
  test's own code; 5 of its pilot replies passed that way. Every check is therefore hardened:
  returned values must have the exact built-in type, and expected strings appear only as SHA-256
  digests. The certificate runs both kinds of gaming program against every hardened check (they
  fail) and correct programs (they pass). Re-grading the 1,140 pilot replies with the hardened
  checks changes exactly those 5. The hardened checks are primary for every task; the published
  checks of the cache pair and the two ledger tasks are recorded as well, for comparability with
  the paper's records. Replies with gaming patterns are also counted and reported.

## 2. HotpotQA rankers at a matched budget (R1.3, R2.4, R2.10, R4.4)

- Items: 200 questions drawn (seed 20261006) from the confirmation pool (7,185 questions never read
  by a pilot), each with its own 10-paragraph distractor pool.
- Conditions: none; full (the whole pool, a reference); BM25, MMR, BGE, E5, MiniLM and RankGPT, each
  its top K = 2 paragraphs in rank order. RankGPT: Haiku-4.5, listwise prompt of Sun et al. (2023),
  dataset order (a second, shuffled order only for stability).
- Answer models: Haiku-4.5, GPT-5.5, DeepSeek-V4-Pro (three vendor families).
- Answer prompt (amended after the pilot, before any confirmatory request): reasoning is allowed and
  the reply must end with a line 'Answer: <answer>'; the scorer reads the last such line (without
  one, the last line). In the pilot, whose prompt asked for the answer only, Haiku reasoned step by
  step on multi-hop questions and the first-line scorer misread those replies.
- RankGPT parsing (fixed after the pilot): identifiers missing from a reply are appended in input
  order, as in RankGPT; a bookkeeping error had appended a wrong index after complete rankings,
  which did not affect any pilot answer context (top K is read before the appended part).
- Endpoints, reported separately: evidence retrieval (support recall and all-supporting-retrieved at
  K) and answer quality (official HotpotQA exact match and F1).
- Primary contrasts: RankGPT minus each of the five other rankers on F1, per answer model
  (15 paired differences), with simultaneous 95% intervals (paired bootstrap over questions,
  Bonferroni over the 15). Everything else descriptive with 95% intervals.

## 3. MuSiQue transfer (frozen settings)

- Items: 100 questions from the MuSiQue confirmation pool, 20-paragraph pools; the same rankers,
  prompts and answer models as Section 2, frozen before this evaluation; K = 4.
- Endpoints: exact match and F1 against the answer and its aliases (primary), support retention
  (secondary, never a substitute for answer accuracy). Same contrasts and intervals as Section 2.

## 4. Augmentation diagnostic (HotpotQA)

- Items: 100 confirmation-pool questions with at least two checked distractors (non-supporting,
  containing no gold answer string). Selected with the supporting-fact annotations, so a diagnostic
  sample, not a natural-frequency estimate.
- Conditions: none; gold (the two supporting paragraphs); gold+dist and dist+gold (two checked
  distractors appended or prepended; the gold block unchanged).
- Contrasts per answer model: (gold+dist) - gold and (dist+gold) - gold on F1 and exact match, with
  simultaneous 95% intervals over the six; the no-context baseline reported.

## 5. Listwise overhead and scaling (R2.11)

- Items: 20 MuSiQue confirmation-pool questions; 5, 10 and 20 candidates (all supporting paragraphs
  plus seeded distractors); two input orders; ranking models Haiku-4.5 and GPT-5.5.
- Endpoints (descriptive, 95% intervals): wall-clock latency, input and output tokens, extra
  attempts, complete parses, top-K agreement and Kendall tau across the two orders, support recall
  at K. Financial cost only where a price is published for the deployment; otherwise tokens.

## 6. Reporting

Whatever these runs show is reported, including null or unfavourable results; the pilot is
reported as development data. Local-ranker evidence figures on the confirmatory items were printed
once by a mock test of the runner (5 October, before the freeze); no setting depends on them.
