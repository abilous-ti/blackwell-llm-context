# Package 2 pilot: what it is for, and the rules fixed before any pilot output

Written 5 October 2026, before any pilot request. The pilot produces development data. It checks
that each experiment runs and can measure what it is meant to measure; it is not evidence for or
against any claim, and the confirmatory runs use fresh draws and untouched questions.

## Components and size

| Runner | Cells | Models | Requests |
|---|---|---|---|
| `run_pairs.py --n 5` | 3 source pairs (cache, inventory, audit) x 2 tasks x {none, A, B, AB, BA}; ledger controls: 2 API tasks x {W1, W1plus, W1plus_rev, W1pad} | all six | 1,140 |
| `run_qa.py` | HotpotQA: 30 questions x 8 conditions (none, full, BM25, MMR, BGE, E5, MiniLM, RankGPT at K = 2); MuSiQue: 20 x 8 (K = 4); augmentation: 20 x {none, gold, gold+dist, dist+gold}; RankGPT rankings (2 input orders); overhead: 10 MuSiQue questions x {5, 10, 20} candidates x 2 orders | answers: Haiku-4.5, GPT-5.5, DeepSeek-V4-Pro; ranking: Haiku-4.5; overhead: Haiku-4.5, GPT-5.5 | 1,660 |

All questions come from the development pools in `natural_data/package2/splits.json`; the
confirmation pools (HotpotQA 7,185, MuSiQue 2,317 questions) are not read by any pilot step.

## Fixed now

1. **The three source pairs and their four new tasks are final.** Their structural certificates
   pass (`certify_pairs.py`, `results/package2/certificates.json`). Every pair goes into the
   confirmatory run whatever the pilot shows; no pair or task is dropped or replaced because of
   its pilot pass rates. The pilot may only reveal a defect (a verifier, stub or prompt bug, or a
   transport problem), found by reading the replies; any fix is logged with its reason, and the
   fixed task is then re-certified.
2. **What the pairs pilot checks:** transport and grading run for every model; no-context
   baselines are reported per task and model (a high one marks convention leakage for that model
   and is reported, not used to drop anything); replies are read for packaging failures.
3. **What the QA pilot checks:** answer-format compliance (short answers that the official
   exact-match and F1 can score), RankGPT parse completeness, transport failures, latency and token
   use per condition, and whether the full-context reference and the no-context baseline leave
   room between them for the rankers to differ.
4. **What the pilot may set before the confirmatory protocol is frozen:** the matched budget K per
   dataset, the answer prompt's wording, and the confirmatory sample sizes, from the pilot's
   variances. These choices are recorded with the pilot data that informed them.
5. **Reporting:** the pilot is reported as development data, with its size and dates.
