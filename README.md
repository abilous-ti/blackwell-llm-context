# Context Selection Is a Partial Order

Research package for the paper **"Context Selection Is a Partial Order"** — a Blackwell/Le Cam
treatment of LLM context selection: which context source an agent should read is a *partial* order,
not a scalar ranking.

**Author:** Andriy Bilous, Lviv Polytechnic National University.

## Core results

- **C1 (garbling order):** context sources form a Blackwell-style partial order under garbling.
- **C2 (incomparability):** no query-independent scalar relevance score ranks incomparable sources
  correctly for all tasks — certified empirically, not just constructed.
- **C3 (deficiency surrogate):** a decision-restricted value-deficiency surrogate δ̂_D with a
  uniform Clopper–Pearson + Bonferroni certificate.
- **C4 (method):** Probe-Select — keep the certified non-dominated set and coverage-diversify;
  monotone-safety, top-k generalization, and (1−1/e) coverage propositions.
- **C5 (empirical anchor):** incomparability + relevance mis-ranking certified on **6 models across
  4 vendors** (Anthropic, OpenAI/Azure, DeepSeek, Moonshot); **anti-monotonicity** (a strict superset
  of a sufficient source *degrades* task success) certified cross-vendor; a model-relative
  private-context moat spectrum. Replicated in a **second task domain** and in a **non-agentic
  single-shot regime** (confound break).

## Repository layout

| Path | Contents |
|---|---|
| `paper/` | LaTeX source (`.tex`, `.bib`, `.bbl`), compiled `blackwell-paper.pdf`, Word and Markdown versions |
| `harness/` | `measure_blackwell.py` — the measurement harness (Claude CLI + Azure OpenAI Responses/chat launchers, multi-vendor `--model`, `--singleshot`, retry); `measure_blackwell_pair2.py` — second source-pair (generality) |
| `results/` | Raw per-run JSON results backing every number in the paper (see map below) |
| `docs/` | `BLACKWELL.md` — theory notes and due diligence; `EXPERIMENT-BLACKWELL.md` — the full experimental record, including negative results and retractions |

## Results-file map

| File | What it certifies |
|---|---|
| `blackwell_n80_results.json` | Main n=80 anchor: incomparability + dominance (Haiku, agentic) |
| `blackwell_argorder_n80.json` | Hardened api_argorder task (kw-only memo), n=80 |
| `blackwell_orderC_results.json` | Order-control arm (W1plus_rev): recovery-based anti-monotonicity verdict |
| `blackwell_trap_results.json` | Relevance-trap task: lexical-relevance mis-ranking |
| `blackwell_sonnet_n40.json`, `blackwell_opus_n20.json` | Cross-model within Anthropic (incl. the retraction of "intensifies with strength") |
| `blackwell_deepseek_n40.json`, `blackwell_kimi_n40.json`, `blackwell_gpt55_n40.json` | Cross-vendor replication (DeepSeek, Moonshot Kimi, GPT-5.5 via Azure) |
| `blackwell_haiku_singleshot_n40.json` | Non-agentic single-shot regime — harness-confound break |
| `blackwell_pair2_n40.json` | Second source pair (cache-module domain) — generality |
| `incomparability_results.json` | Early incomparability certification run |
| `moat_results.json` | Model-relative private-context moat spectrum |

## Reproducing

```bash
# Anthropic (agentic, via Claude CLI; requires an authenticated `claude`)
python harness/measure_blackwell.py --tasks all --arms all --out results/rerun.json

# other vendors (key via env var, never hardcoded)
set AZURE_OPENAI_KEY=...   # or export on POSIX
python harness/measure_blackwell.py --model gpt-5.5 --singleshot ...
```

The harness reads API keys **only** from environment variables; no credentials are stored in this
repository.

Compile the paper with `pdflatex → bibtex → pdflatex ×2` (needs a LaTeX distribution with
`lmodern`; tested with MiKTeX 25.12).

## Honesty notes

`docs/EXPERIMENT-BLACKWELL.md` records the full history, including bugs distinguished from findings
(a validator bug initially mimicked a null), one retracted claim ("effect intensifies with model
strength" — falsified by the Opus run and withdrawn), and null results reported as nulls (pair-2
trap mis-rank). Mock/smoke-test outputs are excluded from `results/`.
