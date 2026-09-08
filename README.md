# Context selection as a partial order — artifacts

Measurement harness, executable verifiers, and complete run records for
**"Context selection as a partial order: A Blackwell framework and verified LLM evidence"**
(Andriy Bilous, Petro Pukach, Vasyl Lytvyn, Zoriana Rybchak — Lviv Polytechnic National University).

Every number in the paper is an empirical PASS rate from live model calls graded by executable
verifiers (return code 0 = PASS). This repository holds the code that produced them and the raw
per-run records from which every verification can be recomputed.

## What the paper claims

- **Theory.** Context sources, modelled as statistical experiments on a task's latent requirement,
  form a Blackwell *partial* order. Blackwell-incomparable sources cannot be ranked by any
  query-independent scalar for all tasks, and topical query-conditioned scores fail on a
  constructed trap.
- **Verification.** A decision-restricted value-deficiency *surrogate* (deliberately not called a
  Le Cam deficiency) with a distribution-free finite-sample verification: exact Clopper–Pearson
  intervals, union bound over the task battery, η = 0.10.
- **Evidence.** Verified incomparability on 6 models across 4 vendors; the trap mis-rank realized
  by lexical, dense bi-encoder (BGE, E5) and cross-encoder rankers while an LLM listwise reranker
  escapes; and verified anti-monotonicity — a strict superset of a sufficient source collapsing
  PASS — with order, length-padding, routing-instruction and structured-context controls.

## Two corrections worth knowing before reading the code

**Ψ is an interaction, not harm.** The four-term second difference
Ψ = PASS(W1+) − PASS(W1) − PASS(W2) + PASS(none) satisfies Ψ ≤ 0 *exactly* when the pair is
submodular, so it never evidenced harm (take none = 0 and W1 = W2 = W1+ = 1: Ψ = −1 with zero
degradation). Harm is the direct contrast Δ = PASS(W1+) − PASS(W1). `certify_harm` computes Δ;
`certify_interference` still computes Ψ and is retained as a descriptive quantity.

**The confidence budget is per endpoint.** Only two endpoints enter Δ's bound — an upper on the
superset arm, a lower on W1 — so each carries noncoverage η/2 and the union bound delivers η. An
earlier version used two-sided intervals at η/2, left two endpoints unused, delivered 1 − η/2, and
widened every bound.

## Layout

| Path | Contents |
|---|---|
| `harness/` | measurement code, Python standard library only; API keys are read from the environment and never written to disk |
| `harness/diag/` | retention re-measurement, packaging audit, certificate recomputation, BigCodeBench pilot |
| `results/` | raw result JSONs and run logs |
| `results/audit/` | re-measurement with raw completions retained |
| `results/bcb/` | BigCodeBench pilot |
| `docs/` | `EXPERIMENT-BLACKWELL.md` (per-cell record), `BLACKWELL.md` (formalization and proof sketches) |
| `paper/` | manuscript source, compiled PDF, the MAKE submission build, and the two scripts that generate it |

### Harness

- `measure_blackwell.py` — pair-1 (`ledger`) harness: the surrogate, the uniform incomparability
  verification, dominance and harm verification, the lexical-relevance scalar, launchers (Claude
  CLI agentic and single-shot, Azure Responses, OpenAI-compatible chat), and the ablation arms
  (`W1pad`, `W1plus_instr`, `W1plus_xml`).
- `measure_blackwell_pair2.py` — pair-2 (`cache` module) sources over the same machinery.
- `measure_reranker_trap.py` — LLM listwise (RankGPT-style) reranker probe.
- `measure_dense_trap.py` — dense bi-encoder / cross-encoder probe (open weights, local, no API).
- `diag/audit_any.py` — re-runs any cell keeping every raw completion, scoring each draw under both
  the published and an import-neutralized verifier, and recording the packaging signals.
  `--import-instruction` removes the import confound at source instead of post hoc.
- `diag/recompute_LD.py` — recomputes the incomparability certificate from retained draws using the
  harness's own `certify_incomparable`, so the arithmetic cannot drift from the published path.
- `diag/bcb_pilot.py`, `diag/bcb_screen.py` — the BigCodeBench pilot and its ceiling screen.

## File → paper mapping

| Paper object | Files |
|---|---|
| Six-model incomparability | `results/blackwell_{haiku_ss,sonnet_ss,opus_ss,gpt55,deepseek,kimi}_n40.*` |
| Opus arm re-runs | `blackwell_opus_ss_W1plus.json`, `blackwell_opus_ss_W2_trap_rerun.json` |
| Haiku enc re-run | `blackwell_haiku_ss_W1_enc_rerun.json` |
| Anti-monotonicity table | the six-model files above |
| Raw-failure audit | `results/diag/` (12–40 retained draws per arm, both verifiers) |
| Re-measurement with retention | `results/audit/audit_*.json` |
| Explicit-import condition | `results/audit/audit_impctl-*.json` |
| Ranker spectrum | `reranker_trap_n30.*` (LLM listwise), `dense_trap.json` (BGE, E5, cross-encoder) |
| Second pair | `blackwell_pair2_n40.*`, `blackwell_pair2_n80.*` |
| Length-matched padding | `blackwell_pad_n40b.*` |
| Routing instruction | `blackwell_instr_n40.*` |
| Structured context (XML) | `blackwell_xml_arm_only.*` (clean arm-only re-run) and `blackwell_xml_n40.*` (first run; its `W1plus_xml` arm was lost to a transport-failure window and is superseded, the other four arms are valid) |
| BigCodeBench pilot | `results/bcb/` |

## Reproducing

```bash
# pair-1, single-shot, core arms (needs the claude CLI on PATH and a key in the env)
python harness/measure_blackwell.py --runs 40 --singleshot \
  --tasks api_post_ok,api_argorder --arms none,W1,W2,W1plus --workers 2 --out out.json
```

```bash
# re-measure a cell keeping every raw completion, both verifiers, packaging signals
python harness/diag/audit_any.py --kind azure --model DeepSeek-V4-Pro \
  --task api_post_ok --arms W1,W1plus --n 40 --out results/audit
```

```bash
# dense / cross-encoder probe (local, no API)
pip install sentence-transformers && python harness/measure_dense_trap.py
```


## Scope of the numbers

Verification parameters match the paper: η = 0.10, exact Clopper–Pearson intervals at union-bound
level over the battery, τ = 0.30 for harm. Transport-level failures are retried and never scored as
passes; where an outage hit a whole arm it was re-measured in isolation and only the clean
measurement is reported. The one cell that resisted re-measurement for a while, GPT-5.5's
`W2`/`trap_store_wire`, was re-run after a GPT-5.5 deployment became available: all four GPT-5.5
cells now have clean single-shot runs at n=40 that reproduce the published grid exactly
(`results/audit/audit_gpt55_*`).

The intervals carry sampling error only. The re-measurement in `results/audit/` shows between-run
shifts wider than the nominal intervals, and the raw-failure audit shows prompt wording moving one
cell further still. Every verified quantity is an inference about a (model snapshot, prompt, default
decoder) triple, not a property of a vendor's model line.
