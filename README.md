# Context Selection Is a Partial Order — artifacts

Measurement harness, executable verifiers, and complete run records for the paper
**"Context Selection Is a Partial Order: A Blackwell Framework and Certified LLM Evidence"**
(Andriy Bilous, Oleksandr Reminnyi — Lviv Polytechnic National University).

Every number in the paper is an empirical PASS rate from live model calls checked by executable
verifiers; this repository contains the code that produced them and the raw per-run records from
which every certificate can be reconstructed.

## Core results (paper contributions)

- **Theory** — context sources, modeled as statistical experiments on a task's latent requirement,
  form a Blackwell partial order; Blackwell-incomparable sources cannot be ranked by any
  query-independent scalar for all tasks, and topical query-conditioned scores fail on a
  constructed trap.
- **Certificate** — a Le Cam-inspired, decision-restricted value-deficiency surrogate with a
  distribution-free finite-sample certificate (exact Clopper–Pearson intervals, Bonferroni over
  the task battery, η = 0.10).
- **Evidence** — certified empirical incomparability on 6 models across 4 vendors (Anthropic,
  OpenAI/Azure, DeepSeek, Moonshot); the trap mis-rank realized by representative lexical, dense
  bi-encoder (BGE, E5), and cross-encoder rankers while an LLM listwise reranker escapes; and
  certified anti-monotonicity (a strict superset of a sufficient source collapsing PASS) with
  order, length-padding, routing-instruction, and structured-context controls.

The constructive selection rule the partial order implies (Probe-Select) is developed in a
companion paper.

## Layout

- `harness/` — measurement code (Python standard library only; API keys are read from the
  environment and never written to files):
  - `measure_blackwell.py` — pair-1 (ledger) harness: surrogate, uniform certificate, dominance
    and interference certificates, lexical-relevance scalar, launchers (Claude CLI agentic and
    single-shot, Azure Responses, OpenAI-compatible chat), and the ablation arms
    (`W1pad`, `W1plus_instr`, `W1plus_xml`).
  - `measure_blackwell_pair2.py` — pair-2 (cache module) sources over the same machinery.
  - `measure_reranker_trap.py` — LLM listwise (RankGPT-style) reranker probe.
  - `measure_dense_trap.py` — dense bi-encoder / cross-encoder probe (open weights, local, no API).
- `results/` — raw result JSONs and run logs, named as cited in the paper's Appendix C.
- `docs/` — `EXPERIMENT-BLACKWELL.md` (full experimental record, exact per-cell figures) and
  `BLACKWELL.md` (theory hardening: formalization and proof sketches).
- `paper/` — the manuscript source (`.tex`, `.bib`, `.bbl`) and compiled PDF.

## File → paper mapping

| Paper object | Files in `results/` |
|---|---|
| Tables 1–2 (six-model incomparability) | `blackwell_n80_run.log` + `blackwell_n80_results.json` (Haiku n=80), `blackwell_sonnet_n40.*`, `blackwell_opus_n20.*`, `blackwell_gpt55_n40.*`, `blackwell_deepseek_n40.*`, `blackwell_kimi_n40.*` |
| Table 3 (interference) + hardened cell | six-model files above + `blackwell_argorder_n80.*` |
| Per-cell record (Appendix B) | same files; order control `blackwell_orderC_*`; trap run `blackwell_trap_*` |
| Ranker-spectrum table | `reranker_trap_n30.*` (LLM listwise), `dense_trap.json` (BGE, E5, cross-encoder) |
| Control: second pair (cache domain) | `blackwell_pair2_n40.*`, `blackwell_pair2_n80.*` (contract cell at n=80) |
| Control: single-shot replication | `blackwell_haiku_singleshot_n40.*` |
| Control: length-matched padding | `blackwell_pad_n40b.*` |
| Control: routing instruction | `blackwell_instr_n40.*` |
| Control: structured context (XML) | `blackwell_xml_arm_only.*` (clean arm-only re-run); `blackwell_xml_n40.*` (first run — its `W1plus_xml` arm was invalidated by a transport-failure window and is superseded by the re-run; its other four arms are valid) |

## Reproducing

```bash
# pair-1, single-shot, core arms (requires the claude CLI on PATH and an API key in the env)
python harness/measure_blackwell.py --runs 40 --singleshot \
  --tasks api_post_ok,api_argorder --arms none,W1,W2,W1plus --workers 2 --out out.json

# dense/cross-encoder probe (local, no API)
pip install sentence-transformers
python harness/measure_dense_trap.py
```

PASS is defined by executable verifiers embedded in the harness (return code 0 = PASS). Certificate
parameters match the paper's Appendix C: η = 0.10, exact Clopper–Pearson intervals at Bonferroni
level over the battery; transport-level failures are retried and never scored as passes.
