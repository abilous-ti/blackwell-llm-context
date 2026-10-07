# Context selection as a partial order — code and records

Measurement code, executable verifiers and released records for the manuscript
**"Context Selection as a Partial Order: A Blackwell Framework and Verified LLM Evidence"**
(Andriy Bilous, Vasyl Lytvyn, Petro Pukach, Zoriana Rybchak — Lviv Polytechnic National University),
revised in October 2026 for *Machine Learning and Knowledge Extraction* (MDPI). The manuscript itself is
submitted to the journal and is not published here.

The branches `main` and `replication-2026-10` hold the revised version. The manuscript's Data Availability
Statement pins the exact commit;
`results/MANIFEST.md` pins every released record by SHA-256.

## What the paper establishes, and which numbers are which

The paper keeps three kinds of statement apart:

1. **Structural incomparability** of the declared source families is a property of the construction
   (the projection sources of Lemma 1), not a measurement.
2. **Fixed-model PASS relations** — PASS incomparability and superset harm — are measured for one fixed
   model rule at a realized state. They do not establish the structural relation: even a structurally
   comparable pair can cross in PASS.
3. **Le Cam deficiency** is bounded from measurement only in the label experiment, where hidden states are
   drawn from the task prior and the guessing caps are proved.

Not every number is a PASS rate. The coding experiments report PASS (the share of completions that pass
executable checks); the label experiment reports label accuracy and deficiency lower bounds; the
natural-data benchmarks report answer F1 and exact match, support recall, latency and token use.

## Experiments, code and records

| Experiment (manuscript section) | Code | Records |
|---|---|---|
| Original coding battery: six models, four tasks, n = 40 per cell (4.1–4.3, 5.1–5.3, 5.5) | `harness/measure_blackwell.py`, `harness/diag/` | `results/blackwell_*_n40.*`, `results/audit/`, `results/retain_api/` |
| Randomized replication: six collection windows, 1–4 October 2026 (4.4, 5.4) | `harness/replication/` | `results/replication/` |
| Further constructed pairs and the clarified-contract run (4.5, 5.6) | `harness/package2/` | `results/package2/confirm_pairs/`, `results/package2/confirm_clarify/` |
| Label decisions over hidden states (4.6, 5.7) | `harness/package2/` | `results/package2/confirm_labels/` |
| Natural data, supplied pools: HotpotQA, MuSiQue, reranking overhead (4.7, 5.8) | `harness/package2/` | `results/package2/confirm_qa_textfree/` (text-free) |
| Natural data, retrieved candidates: HotpotQA fullwiki (4.7, 5.8) | `harness/package3/` | `results/package3/` (text-free) |
| Exploratory natural-data pilot, 2 October 2026 (development data; 6.4) | `harness/natural/` | `results/natural_pilot_textfree/` |

Each experiment added in the revision has a protocol fixed and hashed before its first confirmatory request
(`harness/replication/PROTOCOL.md`, `harness/package2/PROTOCOL*.md`, `harness/package3/PROTOCOL_FULLWIKI.md`)
and a freeze record in `results/`. Deviations are recorded, not edited away: see
`results/replication/DEVIATIONS.md`, the label-analysis amendment and `harness/package3/PROTOCOL_FULLWIKI_ERRATA.md`.

## Verify the paper's numbers without model calls

None of these makes a model call; all of them run on the Python standard library from a fresh clone.

```bash
python harness/diag/recompute.py                 # original grid: every per-cell rate, harm bound and verdict
python harness/diag/check_regimes.py             # each cited original run's transport, read from its log
python harness/diag/retained_text_checks.py      # the textual screens over retained completions
python harness/replication/analyze.py            # randomized replication -> results/replication/analysis.json
python harness/package2/analyze_pairs.py         # further pairs (default: results/package2/confirm_pairs)
python harness/package2/analyze_clarify.py       # clarified contracts
python harness/package2/analyze_labels.py        # label experiment (analysis frozen before collection)
python harness/package2/analyze_labels_amended.py   # label experiment, drift-robust amendment
python harness/package2/verify_qa_textfree.py    # supplied-pool natural data: recomputes all 807 outputs
python harness/package3/verify_fullwiki_textfree.py # fullwiki: recomputes its outputs from the exports
python harness/diag/make_manifest.py api         # regenerate the SHA-256 manifest
```

The analyses rewrite their output files. The rewritten files reproduce the committed ones; on Windows they are
written with CRLF line endings, which `git diff --ignore-cr-at-eol` shows as no change but which alter their
SHA-256, so regenerate the manifest from a fresh checkout rather than after re-running the analyses.

`harness/diag/check_printed_bounds.py` additionally compares the manuscript's printed bounds with the computed
ones when a local copy of the manuscript is present, and says so and skips when it is not. The fullwiki
verifier skips the checks that need the frozen input file, which is not public (see below).

## Statistical conventions of the current analysis

- **Family level.** Every verified claim is reported at η = 0.05, a 95% family level, and names its coverage
  family. The original measurements use exact Clopper–Pearson intervals; the replication and the further pairs
  use one-sided Hoeffding bounds on independent block differences, which allow success probabilities to vary
  across blocks and windows; the label experiment uses Clopper–Pearson and drift-robust Hoeffding bounds over
  hidden states. Natural-data comparisons use approximate bootstrap intervals, reported as intervals, not as
  verification.
- **Harm** is the direct contrast Δ = PASS(W1+) − PASS(W1). The materiality margin τ = 0.30 applies only to
  harm contrasts; PASS incomparability requires positive lower bounds on both gaps.
- **Ψ is an interaction, not harm.** The four-term second difference
  Ψ = PASS(W1+) − PASS(W1) − PASS(W2) + PASS(none) satisfies Ψ ≤ 0 exactly when the pair is submodular, so it
  never evidenced harm. The harm criterion changed from Ψ to Δ on 7–8 September 2026; `certify_harm` computes
  Δ, and `certify_interference` still computes Ψ as a descriptive quantity.
- **The confidence budget is per endpoint.** Only two endpoints enter Δ's bound — an upper on the superset arm
  and a lower on W1 — so each carries noncoverage η/2.
- **Inputs of the original-grid numbers.** Every number of the original grid is computed by
  `harness/diag/recompute.py` from the `counts` field of the run files named in the manifest, with one declared
  substitution (both GPT-5.5 `trap_store_wire` conditions come from
  `results/audit/audit_gpt55_trap_store_wire_summary.json`, because the base run logged an HTTP 500 there).
  Other fields written at measurement time (`interference`, `estimator`, `dominance`,
  `certificate_incomparable`) are historical harness outputs, some using Ψ or an earlier budget; they are not
  inputs to the manuscript.

## What is released, what is withheld, what was never kept

- **Released** (every file listed in `results/MANIFEST.md`): the original run logs and result files; the raw
  completions of the original Anthropic runs (`results/retain_api/`); every request, response and grade of the
  randomized replication, the further pairs, the clarified-contract run and the label experiment, with their
  schedules (including the hidden states of the label experiment) and freeze records; and text-free records of
  the natural-data benchmarks — identifiers, splits, the indices each ranker selected, every ranking, answer
  scores, missingness, resource use and SHA-256 digests of every input — from which every natural-data figure
  is recomputed.
- **Withheld, available on request:** records that reproduce benchmark text — natural-data questions,
  paragraphs, gold answers and the model replies that quote them — and the frozen input file of the fullwiki
  benchmark, which lists the candidate paragraph titles. The source datasets are licensed by their creators
  (HotpotQA, CC BY-SA 4.0; MuSiQue and TAT-QA, CC BY 4.0); the released code rebuilds the inputs from the public
  releases and the digests verify them. For the revision, these records are also provided to the journal's
  reviewers as a confidential archive, so that the grading of individual answers can be checked.
- **Never retained:** the raw completions of the June base runs of GPT-5.5, DeepSeek-V4-Pro and Kimi-K2.6
  (only per-cell counts and logs were kept), and some metadata of the original runs: request times, the worker
  count, the order of draws within a cell and any model identifier returned by the provider. No sampling seed
  was set. `results/replication/provenance_original.md` records what is known about each original record.
  The randomized replication records all of these for every request.

## Layout

| Path | Contents |
|---|---|
| `harness/` | measurement code; the API harness uses only the Python standard library, reads API keys from the environment and never writes them to disk |
| `harness/diag/` | recomputation of the original grid, the verification guards, the retention re-measurement and audits |
| `harness/replication/`, `harness/package2/`, `harness/package3/`, `harness/natural/` | protocols, runners and analyses of the experiments added in the revision |
| `results/` | released records (see `results/MANIFEST.md`) |
| `docs/` | working records from June–September 2026 (`BLACKWELL.md`, `EXPERIMENT-BLACKWELL.md`), revised to remove superseded claims; the manuscript is the authoritative account |

## Rerunning measurements

New measurements need API access; endpoints and keys are read from the environment.

```bash
# original pair over HTTP, core arms
python harness/measure_blackwell.py --runs 40 --retain results/retain_api/haiku \
  --tasks api_post_ok,api_argorder --arms none,W1,W2,W1plus --workers 2 --out out.json

# re-measure a cell, keeping every raw completion
python harness/diag/audit_any.py --kind azure --model DeepSeek-V4-Pro \
  --task api_post_ok --arms W1,W1plus --n 40 --out results/audit
```

The experiments added in the revision have their own runners and protocols in `harness/replication/`,
`harness/package2/` and `harness/package3/` (see `harness/package3/RUNBOOK.md`). Rebuilding the natural-data
inputs and running the local rankers need the packages in `requirements-natural.txt`; the rebuild steps are in
`results/package2/confirm_qa_textfree/README.md` and `results/package3/confirm_fullwiki_textfree/README.md`.

A transport failure is not a model answer: the HTTP client makes up to three attempts (a 180-second timeout per
attempt, delays of 2 s and 4 s) when the request or response parsing raises, and a draw whose attempts are
exhausted is excluded rather than scored as a failure. A returned payload is never retried on content.

## The verifier is not a sandbox

The verifier runs model-generated code in a subprocess with a minimal environment that carries no provider
credentials, and signals completion by writing a per-run random token to a file the parent names, so code that
exits before the checks fails. The subprocess still has the filesystem and the network, so this harness is not
a safe place to run untrusted code; ruling out deliberate interference needs OS-level isolation, which it does
not provide.

## Scope

The intervals carry sampling error only. Re-measurements show between-run shifts wider than the nominal
intervals, which is why the revision added the randomized replication. Every verified quantity is an inference
about a (model snapshot, prompt, default decoder, run) tuple, not a property of a vendor's model line, and the
experiments establish existence on constructed tasks, not prevalence.

## Citation

See `CITATION.cff`.
