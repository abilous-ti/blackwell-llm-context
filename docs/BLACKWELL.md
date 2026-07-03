# A Blackwell-Informativeness Theory of Context Selection for LLMs

The one theorem that survived 6 angled novelty searches: **Blackwell's comparison of
experiments (1953)** + **Le Cam's deficiency (1964)**, applied to *which context to
supply an LLM*. Theory + a measurable estimator + a buildable empirical demo. The only
close neighbor is **V-usable information** (Ethayarajh et al. 2022; LLM use 2504.15630) —
the *scalar* cousin; our contribution is the **partial order, the incomparability
theorem, and the deficiency estimator** that no scalar can express.

Status (updated 2026-06-19, after deep due diligence): **bridge confirmed open, ~85%.**
8-angle adversarial novelty workflow + full-text reads of the two binding threats. 0/8
angles report the machinery applied to LLM context selection. C2 (incomparability) and C3
(certified PASS estimator) are clean; C1 (the order) is a tool-level port — cite & diff.
See §9 for the completed due-diligence record and the ready related-work paragraph.

---

## 1. Formalization
- Task `T` has a latent requirement `S` (the object the verifier checks against).
- A **context source** `W` is an *experiment* on `S`: a channel `κ_W : S → 𝒲` emitting a
  signal `w` correlated with `S` (a retrieved doc, a convention snippet, a repo file).
- The model is a decision rule `δ : (T, w) ↦ Ŝ`. Utility `u(Ŝ,S)=𝟙[d(Ŝ,S)≤ε]` (PASS),
  optionally minus `λ·tokens`.

## 2. The order (Blackwell, instantiated)
`W₁ ⪰_B W₂` (W₁ Blackwell-dominates W₂) iff `κ_{W₂} = G∘κ_{W₁}` for some garbling
(Markov kernel) `G` — W₂'s signal is a noised version of W₁'s.

**Theorem 1 (universal context dominance).** `W₁ ⪰_B W₂` ⟺ for *every* prior over `S`,
*every* utility `u`, and *every* decision rule, the best achievable expected utility with
`W₁` is ≥ that with `W₂`. (Direct instantiation of Blackwell's theorem.)
→ **Corollary:** if `W₁ ⪰_B W₂`, supplying `W₁` is at-least-as-good *for all tasks* — a
guarantee no scalar relevance/MI/V-info score provides (those are task-specific).

**Proposition 2 (the moat is a shadow).** `I(S;W|θ)` and V-usable information are
Blackwell-*monotone*: they respect `⪰_B` but collapse it to a scalar. The measured moat
(+100% on idiosyncratic, +0% generic) is a 1-D projection of the partial order.

## 3. The incomparability theorem (the new structural result)
**Theorem 3 (no scalar ranks incomparable sources).** If `W₁` and `W₂` are
Blackwell-*incomparable* (neither garbles the other), then for *any* scalar context-utility
score `φ` (relevance, MI, V-info, perplexity-gap) there exist tasks `T_a, T_b` such that
`φ` ranks them one way but realized PASS ranks them the opposite way on at least one task.

*Proof.* Incomparability ⟺ neither is a garbling of the other ⟺ (Blackwell, contrapositive)
there is a decision problem on which `W₁` strictly beats `W₂` and another on which `W₂`
strictly beats `W₁`. Instantiate those two decision problems as tasks `T_a,T_b`; any total
order `φ` fixes one ranking and is therefore violated on one of them. ∎

→ **Interpretation:** cross-task *non-transfer of relevance scores is not a modeling
failure — it is a theorem.* The true order is partial; any scalar imposes a total order
that must violate it somewhere. This formally explains the field's "relevance doesn't
transfer" folklore.

## 4. Le Cam deficiency — the measurable relaxation
Exact garblings over text are uncomputable, and `⪰_B` is partial. **Le Cam's deficiency**
`δ(W₁,W₂)` = the minimal worst-case utility shortfall of `W₁` vs `W₂` after the best
garbling; `δ=0 ⟺` Blackwell dominance, `δ>0` grades approximate dominance.

**Decision-restricted, estimable surrogate.** Fix the decision rule to *the LLM* and a task
distribution `𝒟`:
$$\hat\delta_{\mathcal D}(W_1,W_2)=\max\Big(0,\ \sup_{T\in\mathcal D}\big[\mathrm{PASS}(W_2,T)-\mathrm{PASS}(W_1,T)\big]\Big).$$
- `\hat\delta_{\mathcal D}=0` over a held-out task sample ⟹ **empirical Blackwell
  dominance for this model on `𝒟`** (the worst sampled task where `W₂` beats `W₁` is none).
- **Conformal/DKW guarantee:** from `n` sampled tasks, certify `δ_{\mathcal D} ≤ α` with
  probability `≥ 1−η` (distribution-free). This is the *measurable* version of Theorem 1.

(Honest weakening: this is dominance *for this model on this distribution*, not the full
universal order — but that restriction is exactly what makes it computable, and it is still
a real, decision-independent-within-𝒟 guarantee.)

## 5. Contributions (paper)
1. A **decision-independent partial order** on LLM context sources with for-all-tasks
   dominance guarantees (Thm 1) — strictly stronger than scalar relevance.
2. The **incomparability theorem** (Thm 3): no scalar score ranks incomparable sources for
   all tasks → formal account of cross-task relevance non-transfer.
3. **Le Cam deficiency** as the measurable, decision-restricted relaxation, with an
   estimator `\hat\delta_{\mathcal D}` and a conformal certificate.
4. The moat `I(S;W|θ)` recovered as one Blackwell-monotone scalar — unifying the empirical
   results with the order.

## 6. The empirical demo (buildable now, existing harness)
- Construct two context sources `W₁,W₂` designed to be **incomparable** (e.g. `W₁` carries
  the API signature, `W₂` carries the usage convention; each wins on a different task).
- On a task set, measure `PASS(W₁,T)`, `PASS(W₂,T)`. **Show:** (i) a scalar relevance/MI
  score ranks `W₁>W₂` globally, yet (ii) `\hat\delta_{\mathcal D}(W₁,W₂)>0` *and*
  `\hat\delta_{\mathcal D}(W₂,W₁)>0` (mutual positive deficiency = empirical incomparability),
  with a constructed task pair where the scalar mis-ranks. This *instantiates Theorem 3 on a
  real model* — the empirical anchor.
- Then a **dominance** case: `W₁ = W₂ + the convention` ⟹ `\hat\delta(W₂,W₁)>0`,
  `\hat\delta(W₁,W₂)=0` (W₁ empirically dominates) → the for-all-tasks guarantee realized.

## 7. Honest caveats
- **Partial order:** many real pairs are incomparable → practical selection still needs a
  tiebreaker; `\hat\delta` provides a graded one, but there is no free total order (that is
  the *point* of Thm 3, and also its practical limitation).
- **Restricted guarantee:** `\hat\delta_{\mathcal D}` certifies dominance for *this model on
  this `𝒟`*, not universally — weaker than the full Blackwell order, but measurable.
- **Positioning is make-or-break:** must differentiate hard from V-usable information
  (scalar) and from "sufficient context" RAG (binary classifier). The delta is *order +
  incomparability + deficiency*, none of which is scalar/binary.
- **Novelty ~85%:** due diligence complete (§9); residual risk is now mostly *internal*
  (correctness/non-vacuousness, §9) not external (prior art).

## 8. Venue
Theory-leaning empirical: **COLM**, **NeurIPS**, or **TMLR** (which welcomes a clean
theory+demo with honest scope). Pairs naturally as the *theory companion* to the empirical
papers (production-reality measurement; the workload moat).

## 9. Due diligence (completed 2026-06-19)

**Method.** 8 parallel adversarial novelty-hunt agents (Blackwell×ICL, Le Cam×NLP, V-info
landscape, Blackwell-in-ML, EIG context selection, incomparability-in-IR, data-valuation,
channel-degradation) + synthesis; then full-text reads of the two binding threats. Result:
**0/8 angles report the comparison-of-experiments machinery applied to LLM context
selection.** 0 contributions pre-empted.

**Per-contribution verdict.**
- **C1 (order): ADJACENT (lean open).** The deficiency/garbling *tool* is classical and now
  ported into ML (transfer learning). No one applies it to LLM context *sources*. The
  construction is derivative; the application is open. **Most exposed — cite prior art up front.**
- **C2 (incomparability theorem): OPEN — the genuine novelty.** The math is classical (the
  Blackwell order is a non-lattice partial order, arXiv:1401.3146), but no one has stated it
  as a theorem about LLM context selection or used it to explain why relevance doesn't
  transfer across tasks. Novelty is the *application + framing*, not the math.
- **C3 (certified PASS-rate deficiency estimator): OPEN.** No PASS-rate decision-restricted
  deficiency surrogate with a distribution-free certificate exists for context selection.

**The two binding threats — read in full, both cleared.**
1. **Akdemir, "Le Cam Distortion" (arXiv:2512.23617, Dec 2025).** A workflow agent claimed
   it contained a "No-Free-Transfer inequality" + incomparability + a certified empirical
   estimator — that was an **agent over-read (hallucination)**. Full-text read: NO
   No-Free-Transfer, NO incomparability, NO formal partial order (only a directional
   distance δ(ℰ₁,ℰ₂)), NO certificate (MMD proxy only; Remark 3.3 disclaims guarantees), and
   ZERO LLM/prompt/retrieval content (domains: HLA genomics, CIFAR-10, RL control). It has a
   Transfer Theorem (4.1: δ≤ε ⇒ risk bound) and "Experiment Dominance" (4.5) — the C1 *tool*,
   for domain transfer. **Verdict: pre-empts nothing; cite as the deficiency-in-ML lineage
   for C1.** (Lesson: trust the manual full-text read over parallel-agent summaries.)
2. **Fosse et al., "Statistical Deficiency for Task Inclusion Estimation" (arXiv:2503.05491,
   ACL 2025).** Uses statistical deficiency but orders **tasks** (training-time; "reconstructs
   the classic NLP pipeline"), not inference-time context sources; no incomparability; no
   context/demonstration selection. **Verdict: pre-empts nothing; cite & differentiate on
   object (tasks vs context sources) + the PASS/conformal certificate.**

**Biggest threat is NOT V-usable information.** V-info is a scalar (Ethayarajh 2022; CaLE
2504.15630) → it is a *corollary victim* of C2, not a competitor. Disarm in one sentence:
V-info / MI / perplexity-gap / EIG are instances of the scalar class C2 rules out.
Secondary threat: Bayesian experimental design / EIG (BED-LLM; arXiv:2604.00414;
Conformal Information Pursuit 2507.03279) — scalar, decision-*dependent*; the clean
separating axis is decision-*independent* (for-all-tasks) dominance.

**Supporting signal.** arXiv:2604.06621 applies the Blackwell order to LLM *internal
representations* and explicitly names the empirical Blackwell-dominance test as an OPEN
problem — the gap is real and recognized.

**Ready-to-use related-work paragraph.**
> Information-theoretic context and demonstration selection for LLMs is dominated by *scalar*
> criteria — relevance and learned rankers (RankRAG, arXiv:2407.02485), V-usable / predictive-V
> information (Ethayarajh et al., 2022; CaLE, 2504.15630), mutual information and expected
> information gain (BED-LLM; Conformal Information Pursuit, 2507.03279), Shapley and influence
> valuations (DemoShapley, 2410.07523; InfICL, 2402.11750), and binary "sufficient-context"
> classifiers (2411.06037) — each inducing a *total* order over sources. A parallel line
> establishes that context utility is task-dependent, but only empirically (relevance transfers
> across domains yet not across tasks, 2510.24652) or informally (relevance ≠ utility, 2504.07104;
> SURE-RAG, 2605.03534); the multi-objective Pareto-incomparability of prompts (ICLR 2025)
> concerns competing metrics within a single task, not incomparable sources across tasks. The
> comparison-of-experiments apparatus — Blackwell's garbling order and Le Cam's deficiency — has
> recently entered ML for representation learning (Le Cam meets LeCun, 1402.4884), task-inclusion
> estimation (Fosse et al., 2503.05491), and transfer learning, where Le Cam Distortion
> (2512.23617) builds a deficiency-induced directional dominance and a finite-sample proxy — but
> exclusively for domain transfer in vision/genomics/RL, never for LLM context. We close this gap
> by treating each context source as an *experiment on the latent solution* and (i) ranking
> sources by the Blackwell garbling order with a decision-independent, for-all-tasks dominance
> guarantee; (ii) proving an *incomparability theorem* — Blackwell-incomparable sources cannot be
> ranked by **any** scalar score (relevance, MI, V-usable information, perplexity-gap, EIG) across
> all tasks, the first formal account of why relevance does not transfer; and (iii) supplying a
> decision-restricted *empirical* deficiency estimator δ̂_D = max(0, sup_T[PASS(W₂,T)−PASS(W₁,T)])
> with a distribution-free conformal/DKW certificate — an LLM-measurable surrogate that prior
> transfer-learning deficiency work does not provide.

**Go/no-go: GO.** Lead with **C2 + C3**; present C1 as scaffold and cite 2512.23617 up front.

**Remaining checks (now mostly INTERNAL — correctness/non-vacuousness, not prior art):**
1. **Certificate math:** the sup_T in δ̂_D needs a *uniform* concentration bound over the task
   sample (union bound / empirical-process control), NOT naive pointwise DKW. Get this right.
2. **Well-posed latent-S model:** define each "experiment's" sample space and what is observed,
   or a referee calls the partial order a metaphor.
3. **C2 non-vacuousness:** BUILT + mock-verified (2026-06-19) — `tokenbench/measure_blackwell.py`
   extends the moat harness: 2 incomparable private context sources W1 (ledger API contract) /
   W2 (wire-encoding invariant) on the SAME module, 7 tasks (4 W1-fam, 2 W2-fam, 1 relevance-trap),
   4 arms (none/W1/W2/W1plus), real `claude -p` Haiku. Computes δ̂ both directions + the corrected
   uniform Clopper-Pearson+Bonferroni certificate (stdlib). **The fatal confound found in design
   ("query-conditioned relevance solves it") is fixed by the relevance-trap task**: a task
   lexically saturated with encoding vocab (so query-conditioned lexical relevance ranks W2>W1)
   whose graded requirement is the W1 post-contract (so PASS ranks W1>W2) → defeats the scalar
   practitioners actually use. Mock shows: (A) certified incomparable ≥90%, (B2) the trap fires,
   (C) dominance control. REAL RUN PENDING: `python tokenbench/measure_blackwell.py --runs 10`
   (~280 calls, ~$6); start n=10 (clean crossover certifies at n≥9), raise if the real split is
   noisy. The real run adjudicates the open empirical question: does Haiku actually produce the
   stark crossover (and does the trap mis-rank hold) on a live model?
4. **Pre-submission:** one fresh search for any 2026 follow-on porting 2512.23617 to LLMs (the
   most likely convergent pre-emptor), and a line-by-line PDF (not summarized) read of both
   threat papers.

## 10. Theory hardening for submission (addresses §9 checks 1–3)

**10.1 Well-posed latent-S experiment model (check 2).** A task `T` fixes a latent requirement
`S` (the object the verifier `v_T` checks). A context source `W` is an experiment: a Markov
kernel `κ_W : S → 𝒲` that emits a signal `w` (the source's text). The decision rule is the LLM
`δ_M : (T, w) ↦ Ŝ` (the generated solution). Utility is the binary verifier
`u(Ŝ,S)=v_T(Ŝ)∈{0,1}` (PASS). `PASS(W,T) := E[v_T(δ_M(T,w))]`, `w∼κ_W(·|S_T)`. This is well-
posed: the sample space of each experiment is the source's signal alphabet; what's observed is
the supplied text; the order is over these kernels. The estimator restricts the decision rule to
*this* `δ_M` and the task distribution to a finite sample `D` — a decision-restricted relaxation
of the universal Blackwell order, which is exactly what makes it computable.

**10.2 Uniform certificate (check 1) — Proposition (incomparability).** For each cell `(W,T)`
draw `n` i.i.d. PASS Bernoulli outcomes; let `[L_{W,T},U_{W,T}]` be the exact Clopper–Pearson
interval at level `α=η/(2|D|)`. By the union bound over the `2|D|` proportions
`{p_{W₁,T},p_{W₂,T}}_{T∈D}`, ALL hold simultaneously w.p. `≥1−η`. On that event,
`L_D(W₁,W₂):=max_{T}[L_{W₂,T}−U_{W₁,T}]` is a `(1−η)` lower confidence bound on
`sup_T[p_{W₂,T}−p_{W₁,T}]`; hence `L_D(W₁,W₂)>0` **certifies** `δ_D(W₁,W₂)>0`. Both directions
read off the *same* `2|D|` intervals, so the joint incomparability claim
`δ_D(W₁,W₂)>0 ∧ δ_D(W₂,W₁)>0` holds at `≥1−η` with no extra correction. *Why DKW fails:* DKW
bounds one ECDF's sup-deviation from its own CDF over a single i.i.d. sample; here the object is a
max over `|D|` *differences of two binomial means across distinct cells*, so the multiplicity must
be paid via the union bound, not absorbed by a single-sample sup inequality. (Implemented:
`certify_incomparable` / `clopper_pearson` in `tokenbench/measure_blackwell.py`.)

**10.3 Interference certificate (the anti-monotonicity contribution).** Define the per-task
interaction `I_T = PASS(W₁₊,T) − PASS(W₁,T) − PASS(W₂,T) + PASS(none,T)` (W₁₊ a superset of W₁'s
signal). Certify harmful non-monotonicity `I_T ≤ −τ` via the upper bound
`CPhi(p_{W₁₊}) − CPlo(p_{W₁}) − CPlo(p_{W₂}) + CPhi(p_{none})` at Bonferroni `α=η/4`. A certified
`I_T<0` is the algebraic object **no monotone-submodular scalar (relevance/MI/V-info/the moat)
can carry** — it is the formal statement of "more correct context can hurt," localized per task.

**10.4 Non-vacuousness — CERTIFIED, cross-model (check 3, closed).** The full anchor is measured
on real `claude -p` spend (~$123) across **two models** (Haiku 4.5, Sonnet 4.6; Opus 4.8 pending):
- Incomparability **certified ≥90%** (Haiku L_D +0.88/+0.83; Sonnet +0.76/+0.76).
- Confound-proof relevance mis-rank **confirmed** on both (trap: relevance W2>W1, PASS W1≫W2).
- Anti-monotonicity is **large and robust across the capability ladder** (Haiku→Sonnet→Opus):
  the superset W₁₊ collapses the contract's effect by 75–100 points on the API cells in every
  model (Haiku 100→24/1%, Sonnet 100→0/0%, Opus 100→25/5%). Certified on 2 cells × 2 models
  (Haiku, Sonnet); on Opus the point estimates are equally strong (I_T −0.75/−0.80) but n=20 is
  too few to certify. **HONEST CORRECTION:** an earlier 2-point read suggested the harm
  "intensifies with model strength" — the 3rd point (Opus) FALSIFIES monotonicity: Sonnet (middle)
  is the *starkest*, Opus (strongest) less so. The defensible claim is robustness across the ladder,
  NOT a capability trend. New cross-model contribution: the harm of supplying more correct context
  does not wash out with capability — but its severity is not ordered by capability either.
- `none` baselines floor at 0% on both models → the private conventions are unguessable even for
  the stronger model (the moat survives the capability ladder).
- Dominance positive control certifies on both; runtime output-token inflation (+87…+252%) is a
  consistent mechanism fingerprint. See `EXPERIMENT-BLACKWELL.md` §10–12.

**10.5 Generality (next strengthening, designed/ready).** The anchor uses ONE incomparable pair
(API-contract `W1` vs wire-encoding `W2`). To establish the partial order is *general* (not a
one-off), author ≥2 more private-convention pairs in distinct domains (e.g., ID-format vs
state-transition contract; date-encoding vs validation rule) and show each is also empirically
incomparable. Cheap on Haiku (~$10–20). This is the top remaining *content* strengthener; the
cross-vendor model run (non-Anthropic) is the top remaining *external-validity* strengthener
(needs a non-Anthropic API key — none on the current machine).
