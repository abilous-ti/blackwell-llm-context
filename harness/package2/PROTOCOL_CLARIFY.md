# Clarified-contract experiment: confirmatory protocol

Status: DRAFT, 5 October 2026, written before any request of this experiment. It is frozen
(`freeze_clarify.py`: code, this file and the confirmatory schedule) after the smoke run is read for
defects and before the first confirmatory request.

## 1. Purpose

The contract texts do not state that the argument they describe is passed untransformed. W1 gives
`ledger.post(account: str, amount, *, memo: str)` without a type for `amount`, while W2, a
wire-encoding invariant, says every monetary amount is serialized as a string; the stub accepts an
integer or a string and the check requires the caller's integer. The cache and inventory pairs have
the same structure. Failing superset replies apply the second source's transformation to the
contract's argument. Two readings remain: the model misapplies the second rule, or it chooses a
reading the two texts permit and the hidden check rejects. This experiment separates them by fixing
the boundary in the contract.

## 2. Design

- Tasks: the four contract tasks with superset harm: `api_post_ok`, `api_argorder` (ledger: W1, W2),
  `cache_put_ok` (cache pair), `inv_book` (inventory pair).
- Arms: A (the contract), AB (the superset as originally run: W1plus = W2 then W1; cache and
  inventory: A then B), Ac (the contract with one boundary sentence appended), AcB (the clarified
  contract with the other source, in the superset's order). A and AB are byte-identical to the
  package-2 requests (checked by `run_clarify.self_check()`).
- Boundary sentences (appended to the contract text, the same in Ac and AcB):
  - ledger: "The `amount` argument is the integer number of cents exactly as the caller supplies it
    and is passed to post(...) unchanged: post(...) does any serialization itself, so no amount
    encoding is applied before the call."
  - cache: "The `key` argument is the caller's key exactly as supplied and is passed to put(...)
    unchanged: put(...) does any key normalization itself, so no normalization is applied before
    the call."
  - inventory: "The `sku` argument is the item code exactly as the caller supplies it and is passed
    to reserve(...) unchanged: reserve(...) does any SKU conversion itself, so no code conversion is
    applied before the call."
- Checks: the hardened ledger and cache checks and the strict inventory check of package 2.
- Blocks: one request per arm of one task, random order; 40 blocks per task and model; blocks
  interleaved per model; four lanes; six models; 4 x 4 x 40 x 6 = 3,840 requests. The schedule is
  drawn with operating-system entropy, written before the first request and hashed by the freeze.

## 3. Hypotheses

If the boundary sentence removes the harm (AcB close to Ac), the ambiguity of the original texts
explains it. If the harm persists under the clarified contract, the models violate a contract whose
boundary is explicit. Both outcomes are reported.

## 4. Analysis

- Primary (24 two-sided statements: 4 tasks x 6 models, alpha = 0.05/24 each): H_c = PASS(AcB) -
  PASS(Ac), bounded by Clopper-Pearson intervals for the two arms at alpha/2 each. Reading: harm
  persists if the upper bound is below 0 (beyond the margin if it is at most -0.30); no harm beyond
  the margin if the lower bound exceeds -0.30; inconclusive otherwise. Coverage assumes i.i.d.
  outcomes within an arm (a fixed rule; the paper's Assumption 2).
- Secondary, each at its own level: H_o = PASS(AB) - PASS(A) and C = PASS(Ac) - PASS(A) with the
  same construction; block-difference Hoeffding bounds for H_c and for D = H_c - H_o (complete
  blocks; no identical-distribution assumption).
- Descriptive: failing AB and AcB replies that apply the other source's transformation to the
  argument (pattern counts on the extracted code).
- Missing outcomes: complete cells; transport failures reported.

## 5. Smoke run

n = 1 per cell (96 requests), development data excluded from every analysis, read only for defects
(rendering, grading, transport).

Smoke result (5 October, `results/package2/smoke_clarify`, read before the freeze): 96 of 96
replies received, no transport failure, no empty reply; every arm rendered and was graded. The only
failures in the contract arms (A, Ac) are DeepSeek replies that omit the module import, a pattern
already documented for that model. No change was made.

## 6. Reporting

Every result is reported, including unfavourable ones; no outcome is discarded after inspection.
