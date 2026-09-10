# Context selection as a partial order — artifacts

Measurement harness, executable verifiers, and complete run records for
**"Context selection as a partial order: A Blackwell framework and verified LLM evidence"**
(Andriy Bilous, Vasyl Lytvyn, Petro Pukach, Zoriana Rybchak — Lviv Polytechnic National University).

Every number in the paper is an empirical PASS rate from live model calls graded by executable
verifiers. This repository holds the code that produced them and the raw per-run records from
which every verification can be recomputed.

## Verify the paper without spending anything

Every published table, bound and figure is recomputed from the released counts by the scripts
below. None of these makes a model call, and they need nothing but the Python standard
library. All five run clean from a fresh clone of this repository.

```bash
python harness/diag/recompute.py            # every per-cell rate, harm bound and verdict
python harness/diag/check_printed_bounds.py # each printed bound is implied by the computed one
python harness/diag/check_regimes.py        # each cited run's transport, derived from its log
python harness/diag/retained_text_checks.py # the textual screens, each rule beside its result
python harness/diag/make_manifest.py api    # regenerate the SHA-256 manifest
```

`recompute.py` reads the published HTTP record by default; pass `cli` for the superseded
command-line grid, which the manuscript discusses only as history.

The manuscript itself is submitted to the journal rather than published here: this
repository is the artifact record -- measurement code, executable verifiers, every run
record, the manifest that pins them, and these instructions. `check_printed_bounds.py`
additionally checks the manuscript against the data when a local copy is present, and says
so and skips when it is not.

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
| `harness/diag/` | retention re-measurement, packaging audit, certificate recomputation, and the verification guards |
| `results/` | raw result JSONs and run logs |
| `results/audit/` | re-measurement with raw completions retained |
| `docs/` | `EXPERIMENT-BLACKWELL.md` (per-cell record), `BLACKWELL.md` (formalization and proof sketches) |
All six models are queried the same way: one HTTP request per draw, one turn, no tools. The
harness has no command-line launcher.

### Harness

- `measure_blackwell.py` — pair-1 (`ledger`) harness: the surrogate, the uniform incomparability
  verification, dominance and harm verification, the lexical-relevance scalar, the HTTP launchers
  (Anthropic Messages, Azure Responses, OpenAI-compatible chat), and the ablation arms
  (`W1pad`, `W1plus_instr`, `W1plus_xml`).
- `measure_blackwell_pair2.py` — pair-2 (`cache` module) sources over the same machinery.
- `measure_reranker_trap.py` — LLM listwise (RankGPT-style) reranker probe.
- `measure_dense_trap.py` — dense bi-encoder / cross-encoder probe (open weights, local, no API).
- `diag/audit_any.py` — re-runs any cell keeping every raw completion, scoring each draw under both
  the published and an import-neutralized verifier, and recording the packaging signals.
  `--import-instruction` removes the import confound at source instead of post hoc.
- `diag/recompute.py` — recomputes every published per-cell rate, harm contrast and verdict from
  the released counts using the harness's own `certify_harm` and `clopper_pearson`. Aborts rather
  than fall back to a different record if a declared source file is missing.
- `diag/retained_text_checks.py` — the textual screens over retained completions, each rule
  printed beside its result.
- `diag/check_regimes.py` — derives each cited run's transport from its log and fails if a
  run's recorded regime disagrees.
- `diag/check_printed_bounds.py` — verifies every confidence bound printed in the manuscript is
  implied by the one computed from the released counts.
- `diag/make_manifest.py` — regenerates `results/MANIFEST.md` from the tracked files; refuses to
  write if it names a file that is not present.

Historical diagnostics, kept because the manuscript's provenance appendix refers to the record
they produced, not because they feed a published number: `diag/recompute_LD.py` (prints values
from the superseded command-line grid), `diag/recompute_delta.py`, `diag/cell_rerun.py`.

## File → paper mapping

| Paper object | Files |
|---|---|
| Six-model record (per-cell, anti-monotonicity, policies, forest plot) | `blackwell_{haiku,sonnet,opus}_api_n40.*`, `blackwell_{gpt55,deepseek,kimi}_n40.*` |
| GPT-5.5 trap cell (both arms, transport-clean source) | `audit/audit_gpt55_trap_store_wire_*` |
| Behavioural controls (padding, order reversal, routing note, XML) | `blackwell_controls_api_n40.*` |
| Second source pair | `blackwell_pair2_api_n40.*` |
| Ranker spectrum | `reranker_trap_api_n100.*` (LLM listwise), `dense_trap.json` (BGE, E5, cross-encoder) |
| Retained completions behind the audit | `retain_api/{haiku,sonnet,opus}/` |
| Explicit-import condition | `audit/audit_impctl-*.json` |
| Command-line record (superseded, retained as history) | `blackwell_*_ss_n40.*`, `blackwell_pair2_n{40,80}.*`, `blackwell_{pad,instr,xml}_*` |

`results/MANIFEST.md` is authoritative: it pins every file by SHA-256 and maps each table and
figure to the files it is computed from. It is generated by `harness/diag/make_manifest.py`,
which refuses to write if it names a file that is not present.

## Reproducing

```bash
# pair-1 over HTTP, core arms (endpoint and key are read from the environment)
python harness/measure_blackwell.py --runs 40 --retain results/retain_api/haiku \
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
level over the battery, τ = 0.30 for harm. A transport failure is not a model answer: failed draws
are retried, and any that still fail are excluded from the sample rather than scored as PASS = 0,
with the harness refusing to certify a cell left below the requested n. Every published run records
zero transport errors. The one cell that resisted re-measurement for a while, GPT-5.5's
`trap_store_wire`, was re-run after a GPT-5.5 deployment became available; both its `W1` and `W2`
conditions are read from that clean re-measurement, which reproduces the published grid exactly
(`results/audit/audit_gpt55_*`).

The verifier runs model-generated code in a subprocess with a minimal environment carrying no
provider credentials, and grades on a sentinel printed after the last assertion rather than on the
exit status alone, so code that exits early cannot pass unchecked.

The intervals carry sampling error only. The re-measurement in `results/audit/` shows between-run
shifts wider than the nominal intervals, and the raw-failure audit shows prompt wording moving one
cell further still. Every verified quantity is an inference about a (model snapshot, prompt, default
decoder) triple, not a property of a vendor's model line.
