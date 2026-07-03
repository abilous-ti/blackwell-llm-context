# A Blackwell-Informativeness Theory of Context Selection for Language Models: Incomparability, Deficiency, and the Model-Relative Moat

**Draft v1 (2026-06-21).** Theory companion paper. Status: complete first draft; all empirical
claims are backed by certified, real measurements across 6 models / 4 vendors (see §7, and
`EXPERIMENT-BLACKWELL.md` for the run logs). Target venue: TMLR / COLM / NeurIPS.

---

## Abstract

Selecting which context to supply a language model — a retrieved document, a private convention,
a repository file, a demonstration — is universally treated as a *scalar* ranking problem:
score each candidate by relevance, mutual information, V-usable information, or an information-gain
proxy, and take the top-k. We argue this is the wrong primitive. Modeling each context source as a
statistical *experiment* on the task's latent requirement, we apply Blackwell's comparison of
experiments (1953) and Le Cam's deficiency (1964) to context selection. Our central result is an
**incomparability theorem**: when two context sources are Blackwell-incomparable (neither is a
garbling of the other), *no* scalar score can rank them correctly across all tasks. This gives the
first formal account of the field's "relevance does not transfer across tasks" folklore: the true
order over context sources is *partial*, and any scalar imposes a total order that must be violated
somewhere. We make the theory measurable via a decision-restricted Le Cam deficiency estimator with
a distribution-free uniform certificate, and we instantiate the theory on six language models across
four vendors (Anthropic, OpenAI, DeepSeek, Moonshot). On every model we certify (≥90% confidence)
that two private context sources are empirically incomparable, and we show a real query-conditioned
relevance score mis-ranks them. We further report two findings the framework predicts and our
estimator detects: (i) **anti-monotonicity** — supplying a *superset* of a sufficient source can
sharply degrade performance (a certified collapse from ~100% to as low as 0% pass rate), falsifying
the monotonicity that scalar context-value scores silently assume; and (ii) a **model-relative
moat** — the value of private context I(S;W|θ) varies continuously across models (the "guessability"
of a fixed convention spans 0%–75% across vendors), tracking a vendor's training rather than raw
capability. We argue context selection should be framed as a partial-order problem, and that the
deficiency estimator — not a scalar — is the right operational object.

---

## 1. Introduction

Practical LLM systems spend much of their budget deciding *what context to put in the prompt*:
retrieval-augmented generation ranks passages, in-context learning selects demonstrations, and
agentic coding tools choose which files and conventions to surface. Across all of these, the
operative tool is a **scalar score** — lexical/embedding relevance, mutual information, V-usable
information (Ethayarajh et al., 2022), expected information gain — used to impose a total order and
take the top candidates.

A persistent, informal observation undercuts this paradigm: *relevance does not transfer across
tasks*. A source that helps one task hurts another; "the best context" is task-dependent. This is
usually treated as a modeling nuisance to be engineered around. We show it is a **theorem**.

We model a context source `W` as a statistical experiment on the task's latent requirement `S`
(§3), which lets us import two classical tools. Blackwell's order ranks experiments by garbling:
`W₁ ⪰ W₂` iff `W₂`'s signal is a noised version of `W₁`'s, and this holds *iff* `W₁` is at least as
good as `W₂` for every decision problem (Blackwell, 1953). The order is **partial** — many pairs are
incomparable. Our contributions:

1. **(C1) A decision-independent partial order over context sources** with a for-all-tasks dominance
   guarantee (§4), strictly stronger than any scalar relevance score.
2. **(C2) The incomparability theorem** (§5, the lead result): Blackwell-incomparable sources cannot
   be ranked by *any* scalar score for all tasks. Formal account of cross-task non-transfer of
   relevance.
3. **(C3) A measurable deficiency estimator** (§6): a decision-restricted Le Cam deficiency surrogate
   `δ̂_D` with a distribution-free **uniform certificate** (exact Clopper–Pearson intervals +
   Bonferroni over the task sample), turning the partial order into something one can test on a real
   model with a real verifier.
4. **(Empirical) Anti-monotonicity and the model-relative moat** (§7), measured and certified across
   6 models / 4 vendors.

The mathematical machinery (Blackwell order, Le Cam deficiency) is classical; our novelty is its
application to LLM context selection, the incomparability theorem as an account of non-transfer, the
certified PASS-rate estimator, and the cross-vendor empirical program. To our knowledge no prior
work applies comparison-of-experiments to selecting context for language models (§2).

---

## 2. Related Work

Information-theoretic context and demonstration selection for LLMs is dominated by *scalar* criteria
— relevance and learned rankers (RankRAG, Yu et al.), V-usable / predictive-V information (Ethayarajh
et al., 2022; CaLE), mutual information and expected information gain (BED-LLM; Conformal Information
Pursuit), Shapley and influence valuations (DemoShapley; InfICL), and binary "sufficient-context"
classifiers (Joren et al., 2025) — each inducing a *total* order over sources. A parallel line
establishes that context utility is task-dependent, but only empirically (learned relevance transfers
across domains yet not across tasks) or informally (relevance ≠ utility), and the multi-objective
Pareto-incomparability of prompts concerns competing metrics within one task, not incomparable
sources across tasks. The comparison-of-experiments apparatus — Blackwell's garbling order and Le
Cam's deficiency — has recently entered ML for representation learning (van Rooyen & Williamson,
2014), task-inclusion estimation (Fosse et al., 2025), and transfer learning (Akdemir, 2025, builds
a deficiency-induced directional dominance and a finite-sample proxy) — but exclusively for domain
transfer in vision/genomics/RL, never for LLM context. A 2026 survey applies the Blackwell order to
LLM *internal representations* and explicitly names the empirical Blackwell-dominance test as an open
problem. We close this gap: we treat each context source as an experiment on the latent solution and
(i) rank sources by the Blackwell order with a for-all-tasks guarantee; (ii) prove an incomparability
theorem ruling out any scalar; and (iii) supply a decision-restricted empirical deficiency estimator
with a distribution-free certificate, which prior transfer-learning deficiency work does not provide.

(Citations are author-date placeholders; arXiv ids are tracked in `BLACKWELL.md §9`.)

---

## 3. Formalization

A task `T` fixes a latent requirement `S` — the object a verifier `v_T` checks (e.g., the intended
program behavior). A **context source** `W` is an experiment on `S`: a Markov kernel `κ_W : S → 𝒲`
emitting a signal `w` (the source's text) correlated with `S`. A model is a decision rule
`δ_M : (T, w) ↦ Ŝ` (the generated solution). Utility is the **binary verifier**
`u(Ŝ,S) = v_T(Ŝ) ∈ {0,1}` (PASS), and we write `PASS(W,T) = E[v_T(δ_M(T,w))]`, `w ∼ κ_W(·∣S_T)`. The
sample space of each experiment is the source's signal alphabet; what is observed is the supplied
text; the order is over these kernels. This is well-posed (it is not a metaphor): each `W` is a
genuine experiment and the comparison below is the standard comparison of experiments.

---

## 4. The Blackwell order over context sources (C1)

**Definition.** `W₁ ⪰_B W₂` iff `κ_{W₂} = G ∘ κ_{W₁}` for some garbling (Markov kernel) `G` — `W₂`'s
signal is a noised version of `W₁`'s.

**Theorem 1 (universal context dominance).** `W₁ ⪰_B W₂` iff for every prior over `S`, every bounded
utility, and every decision rule, the best achievable expected utility under `W₁` is ≥ that under
`W₂`. *(Direct instantiation of Blackwell's theorem.)*

**Corollary.** If `W₁ ⪰_B W₂`, supplying `W₁` is at-least-as-good *for all tasks* — a guarantee no
scalar relevance/MI/V-information score provides, since those are task-specific. The order is partial:
genuinely incomparable pairs exist (the Blackwell relation forms no lattice).

---

## 5. The incomparability theorem (C2) — the lead result

**Theorem 2 (no scalar ranks incomparable sources).** Let `W₁, W₂` be Blackwell-incomparable (neither
garbles the other). Then for *any* scalar context-utility score `φ` (relevance, mutual information,
V-usable information, perplexity-gap, expected information gain), there exist tasks `T_a, T_b` such
that `φ` ranks `W₁, W₂` one way but realized PASS ranks them the opposite way on at least one task.

*Proof.* Incomparability ⟺ neither is a garbling of the other ⟺ (Blackwell, contrapositive) there is
a decision problem on which `W₁` strictly beats `W₂` and another on which `W₂` strictly beats `W₁`.
Instantiate these as tasks `T_a, T_b`. Any total order induced by a scalar `φ` fixes one ranking of
`{W₁, W₂}` and is therefore violated on one of `T_a, T_b`. ∎

**Interpretation.** Cross-task non-transfer of relevance is *not* a modeling failure — it is a
theorem. The true order is partial; any scalar imposes a total order that must violate it somewhere.
This formalizes the field's "relevance doesn't transfer" folklore. V-usable information, MI,
perplexity-gap, and EIG are all instances of the scalar class Theorem 2 rules out — they are
corollary victims, not competitors.

---

## 6. The deficiency estimator and its uniform certificate (C3)

Exact garblings over text are uncomputable and `⪰_B` is partial. We use a **decision-restricted Le
Cam deficiency**: fix the decision rule to a specific model `δ_M` and a finite task sample `D`, and
define
> `δ̂_D(W₁,W₂) = max(0, sup_{T∈D} [PASS(W₂,T) − PASS(W₁,T)])`.

`δ̂_D(W₁,W₂)=0` over `D` ⟹ empirical dominance of `W₁` over `W₂` on `D` for this model; mutual
positivity `δ̂_D(W₁,W₂)>0 ∧ δ̂_D(W₂,W₁)>0` ⟹ **empirical incomparability**.

**Proposition (uniform certificate).** Draw `n` i.i.d. PASS Bernoulli outcomes per cell `(W,T)`; let
`[L_{W,T}, U_{W,T}]` be the exact Clopper–Pearson interval at level `α = η/(2|D|)`. By the union
bound, all `2|D|` per-task proportions hold simultaneously with probability `≥ 1−η`. On that event,
`L_D(W₁,W₂) := max_T [L_{W₂,T} − U_{W₁,T}]` is a `(1−η)` lower confidence bound on
`sup_T[PASS(W₂,T) − PASS(W₁,T)]`; hence `L_D(W₁,W₂) > 0` **certifies** `δ_D(W₁,W₂) > 0`. Both
directions read off the *same* `2|D|` intervals, so the joint incomparability claim holds at `≥1−η`.

*Why a naive DKW bound fails.* DKW bounds one empirical CDF's sup-deviation from its own CDF over a
single i.i.d. sample; here the object is a max over `|D|` *differences of two binomial means across
distinct cells*. The selection (argmax-gap task) inflates Type-I error with `|D|`; the multiplicity
must be paid via the union bound, not absorbed by a single-sample sup inequality.

**Interference certificate (anti-monotonicity).** For a source `W₁₊` that is a superset of `W₁`'s
signal, define the per-task interaction
`I_T = PASS(W₁₊,T) − PASS(W₁,T) − PASS(W₂,T) + PASS(none,T)`. Certify harmful non-monotonicity
`I_T ≤ −τ` via the upper bound `CPhi(p_{W₁₊}) − CPlo(p_{W₁}) − CPlo(p_{W₂}) + CPhi(p_{none})` at
Bonferroni `α = η/4`. A certified `I_T < 0` is the object no monotone-submodular scalar can carry.

---

## 7. Experiments

### 7.1 Design

We instantiate two **private, unguessable** context sources on the *same* module `ledger` (so any
relevance score treats them as equally on-topic candidates — the precondition for Theorem 2 to bite):

- **W₁ — API call contract:** `ledger.post(account, amount, *, memo)` — account first, amount second
  positional, `memo` a required keyword-only argument; returns an int entry id; raises
  `ledger.PostError` on failure.
- **W₂ — wire-encoding invariant:** amounts serialize to `<sign><minor-unit-digits>#<check>`,
  `check = (sum of digits) mod 10` (`$12.30 → "+1230#6"`).
- **W₁₊ = W₂ ++ W₁** (a literal superset of W₂'s signal; the dominance/anti-monotonicity probe).

**Why incomparable (garbling argument).** From the wire format one cannot manufacture the private
arg-order / required-kw / exception type; from the call contract one cannot manufacture the
cents-scale / `#` / mod-10 check. These are logically independent coordinates of `S`, so neither
signal's σ-algebra refines the other's: `W₁, W₂` are Blackwell-incomparable.

**Tasks (D).** Four cells with stub-`ledger` verifiers (returncode 0 = PASS): two W₁-decisive API
tasks (`api_post_ok`, `api_argorder` — the latter hardened so `memo` arrives via a parameter, forcing
reliance on the kw-only fact), one W₂-decisive task (`enc_amount`), and a **relevance-trap**
(`trap_store_wire`): a prompt lexically saturated with encoding vocabulary (so a query-conditioned
relevance score ranks W₂>W₁) whose graded requirement is the W₁ contract (so PASS ranks W₁>W₂). The
trap is the confound-proof form of Theorem 2: it defeats the relevance score practitioners actually
use, not just a query-independent ranking.

**Arms.** `{none, W₁, W₂, W₁₊}` (+ `W₁₊_rev = W₁ ++ W₂` for an order control). PASS is measured over
`n` i.i.d. completions per cell; the certificate uses `η = 0.10`.

**Models / harness.** Six models across four vendors: Anthropic Haiku 4.5, Sonnet 4.6, Opus 4.8;
OpenAI GPT-5.5; DeepSeek-V4-Pro; Moonshot Kimi-K2.6. The Anthropic models run agentically
(`claude -p`, up to 6 turns); the others run as single-shot completion + code extraction via an
OpenAI-style API. We flag this as a methodological difference; the single-shot setting is arguably a
*cleaner* probe of whether the model uses the supplied context (no agentic-exploration confound). All
PASS rates are real (no modeled numbers); the harness is Python-stdlib only.

### 7.2 Results

**Incomparability (certified on all 6 models).** Mutual positive deficiency with the uniform
certificate clearing `≥90%` on every model. Lower bounds `L_D` (both directions): Haiku +0.88/+0.83
(n=80), Sonnet +0.76 (n=40), Opus +0.55 (n=20), GPT-5.5 +0.76 (n=40), DeepSeek +0.35/+0.72 (n=40),
Kimi +0.675/+0.762 (n=40). The crossover is stark: W₁ solves the API+trap cells and fails encoding;
W₂ solves encoding and fails API+trap.

**Relevance mis-rank (confirmed on all 6).** On `trap_store_wire`, query-conditioned lexical
relevance ranks `φ(W₁)=0.36 < φ(W₂)=0.44` (→ W₂), yet realized PASS ranks W₁ ≫ W₂ (e.g., 96–100% vs
0%). On the honest tasks relevance agrees with PASS (API: W₁>W₂; encoding: W₂>W₁) — relevance fails
*only* where utility diverges from topicality, exactly as Theorem 2 predicts.

**Anti-monotonicity (certified, cross-vendor).** The superset `W₁₊` — which strictly *contains* W₁'s
signal — sharply degrades the API cells: e.g. Sonnet and Kimi collapse `100% → 0%` (`I_T = −1.00`,
certified upper bound ≤ −0.69); Haiku `100% → 24/1%`; GPT-5.5 and DeepSeek certify
`I_T ≤ −0.36..−0.60` on `api_post_ok`. The interference certificate clears on ≥1 cell for 5 of 6
models (Opus reproduces, `I_T = −0.75/−0.80`, but n=20 is too few to certify). An order control
(`W₁₊_rev`) shows the harm does **not** recover under reordering — it is not a lost-in-the-middle
artifact. A runtime fingerprint accompanies the collapse: the harmful arm emits +87% to +252% more
output tokens (verbose thrashing). This is a **certified empirical falsification of Blackwell
superset-dominance on real models**: more strictly-more-informative context can hurt, and the
deficiency estimator detects it where every monotone scalar must miss it.

Honest note: the harm is large and robust across the capability ladder but is **not monotone in
capability** (Sonnet, the middle Anthropic model, shows the starkest collapse; Opus, the strongest,
less so). We do not claim a capability trend.

**The model-relative moat (continuous, cross-vendor).** The "private" conventions are genuinely
unguessable for some vendors and partially known to others. The `none`-arm baseline on `api_argorder`
forms a clean spectrum across models: Claude ~0% · DeepSeek 2% · Opus 15% · Kimi 45% · GPT-5.5 75%.
Thus `I(S;W|θ)` — the value of the private context — varies *continuously* across models and tracks a
vendor's training rather than raw capability (DeepSeek, with a tight prior like Claude, is the
clearest evidence this is not a "stronger-model-knows-more" effect). The certified claims rest on
cells unguessable for the model under test. This is a direct empirical confirmation of the theory's
θ-dependence: the partial order, and the moat, are *model-relative* objects.

| Claim | Haiku | Sonnet | Opus | GPT-5.5 | DeepSeek | Kimi-K2.6 |
|---|---|---|---|---|---|---|
| vendor | Anthropic | Anthropic | Anthropic | OpenAI | DeepSeek | Moonshot |
| Incomparability certified (≥90%) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Relevance mis-rank | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Anti-monotonicity certified | ✓ (2) | ✓ (2) | reproduces (n=20) | ✓ (1) | ✓ (1) | ✓ (1) |
| `none` argorder baseline | ~0% | 0% | 15% | 75% | 2% | 45% |

---

## 8. Limitations and honest scope

- **Single source pair.** The certified results use one incomparable pair (API-contract vs encoding).
  Establishing the partial order's *generality* requires additional private-convention pairs in
  distinct domains (designed; in progress). The theorem is general; the empirical instantiation is one
  (well-certified, cross-model) pair.
- **Model-relativity caps universality.** The conventions are unguessable for Anthropic/DeepSeek but
  partially known to GPT-5.5/Kimi. We therefore frame the moat explicitly as *model-relative* (the
  stronger framing); a vendor-universal demo would require more exotic conventions so every baseline
  floors at 0%.
- **Methodology.** Anthropic models run agentically; the others single-shot. We report this; it does
  not affect the certified within-model claims but should be normalized for a strict cross-model
  comparison of magnitudes.
- **Decision-restricted guarantee.** `δ̂_D` certifies dominance/incomparability *for this model on
  this task distribution*, not the full universal Blackwell order — but that restriction is exactly
  what makes it computable, and it is still a real, decision-independent-within-`D` guarantee.
- **Synergy (positive interference) untested.** By construction W₁, W₂ are task-disjoint, so we
  measure negative interference only; a complementary pair (two facts a task needs jointly) would
  test whether interference is sign-indefinite.

---

## 9. Conclusion

Context selection for language models is a **partial-order** problem, not a scalar one. We proved
that no scalar score can rank Blackwell-incomparable context sources for all tasks, gave a
measurable, certified deficiency estimator that realizes the partial order on real models, and
verified the theory across six models and four vendors — including a certified, cross-vendor
falsification of superset-dominance (anti-monotonicity) and a continuous map of the model-relative
moat `I(S;W|θ)`. The practical upshot: replace top-k-by-relevance with deficiency-aware selection,
and expect "the best context" to be model-relative and only partially ordered.

---

### Reproducibility

All numbers are from real model calls verified by executable tests; the harness
(`tokenbench/measure_blackwell.py`, Python stdlib only) implements the estimator, the uniform
certificate, the interference certificate, and launchers for the Anthropic CLI, the Azure Responses
API, and OpenAI-compatible chat completions. Per-model run logs and result JSONs are in the
repository (`blackwell_*_n*.{log,json}`); the experimental record with exact figures is in
`EXPERIMENT-BLACKWELL.md` (§10–13), and the theory hardening (proofs, formalization) in
`BLACKWELL.md` (§10). Total measured spend ≈ $170 (Anthropic) plus Azure quota (OpenAI/DeepSeek/
Moonshot).
