# Machine-checked proofs

Formalization in **Lean 4** of the two impossibility results of
*"Context selection as a partial order: A Blackwell framework and verified LLM evidence."*

| Paper | Lean |
|---|---|
| Theorem (no query-independent scalar ranks incomparable sources) | `no_faithful_query_independent_score` |
| Proposition (topicality boundary) | `topical_score_misranks_trap` |

## Checking it

The file depends only on the Lean 4 core library — **no Mathlib**, no network, no build step:

```sh
lean ContextSelection.lean
```

Success is silent, apart from the four `#print axioms` lines. Toolchain is pinned in
`lean-toolchain` (Lean 4.33.1); install with [`elan`](https://github.com/leanprover/elan).

## What the check reports

```
'ContextSelection.no_faithful_query_independent_score' does not depend on any axioms
'ContextSelection.topical_score_misranks_trap' does not depend on any axioms
'Demo.demo_no_scalar' depends on axioms: [propext]
'Demo.demo_topical_fails' depends on axioms: [propext]
```

Both central results are **axiom-free**: they use no classical logic, no choice, no
excluded middle. The two `Demo` instances use `propext` only because the demonstration
model defines `Beats` by pattern-matching into `Prop`.

## Design notes

**No Mathlib, by choice.** The order on the score codomain is passed explicitly as a
`TotalPre` structure rather than taken from a typeclass hierarchy. This keeps the artifact
checkable with a bare `lean` binary, and it makes the mathematical content visible: the
impossibility is driven by **totality of the induced ranking alone**, not by any property
of the reals. Every scalar in the excluded class — relevance, mutual information,
V-usable information, perplexity gap, fixed-prior expected information gain — maps into a
totally ordered codomain, so all are covered by the one theorem.

**Non-vacuity.** Universally quantified impossibility statements are worthless if their
hypotheses cannot be met, so `namespace Demo` builds the paper's actual configuration
(sources `W1`/`W2`, cells `api`/`enc`/`trap`, the measured double crossover) and applies
both theorems to it.

**Scope.** These are the two *impossibility* results. The Blackwell–Sherman–Stein theorem
is cited in the paper as a classical black box and is not formalized here; neither are the
statistical verification procedures, which are claims about measurements rather than
theorems.
