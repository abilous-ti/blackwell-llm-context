# A Blackwell-Informativeness Theory of Context Selection for LLMs

> **Note.** Working record from June–September 2026, revised on 7 October 2026 to remove superseded claims;
> measured counts, run identifiers, file paths and dates of historical runs are unchanged. The manuscript
> and the README on branch `replication-2026-10` are the authoritative account.

The framework: **Blackwell's comparison of experiments (1953)** + **Le Cam's deficiency (1964)**,
applied to *which context to supply an LLM*. Theory + a measurable estimator + a buildable
empirical demo. **No priority is claimed for this application:** Alpila (Zenodo, public 25 June
2026), the closest prior work, already applies Blackwell/Le Cam ideas to inference-time context
selection for a fixed decoder; **V-usable information** (Ethayarajh et al. 2022; LLM use
2504.15630) is the closest *scalar* neighbour. The contribution is the distinction between the
structural (Blackwell) relation and fixed-model PASS relations, the hidden-state label experiment
that bounds Le Cam deficiency under proved guessing caps, and controlled, replicated verification
(manuscript Section 2.1). *(The June version opened with "the one theorem that survived 6 angled
novelty searches" and claimed the partial order, the incomparability theorem and the deficiency
estimator as the contribution; that framing is withdrawn.)*

Status (2026-06-19, after due diligence; superseded): the June record concluded "bridge confirmed
open, ~85%" from an 8-angle adversarial novelty workflow (0/8 angles reporting the machinery applied
to LLM context selection) and full-text reads of the two binding threats. That novelty conclusion,
and the per-contribution verdicts built on it, are withdrawn: Alpila's preprint, public on 25 June
2026 (after this search), applies the apparatus to inference-time context selection for a fixed
decoder. §9 keeps the due-diligence record; its verdicts and related-work paragraph are superseded
by manuscript Section 2.1.

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
→ **Corollary:** if `W₁ ⪰_B W₂`, supplying `W₁` is at-least-as-good *for all tasks* for an
optimal decision-maker — a guarantee no scalar relevance/MI/V-info score provides (those are
task-specific). It is not a guarantee for a fixed model: a fixed LLM's PASS can fall when a
dominating source is supplied (the measured superset collapse, §10.4; manuscript Theorem 3).

**Proposition 2 (the moat is a shadow).** `I(S;W|θ)` and V-usable information are
Blackwell-*monotone* (V-usable information only under a closure hypothesis on the predictor
family; manuscript Proposition 5): they respect `⪰_B` but collapse it to a scalar. The measured moat
(+100% on idiosyncratic, +0% generic) is a 1-D projection of the partial order.

## 3. The incomparability theorem (manuscript Theorem 2; no priority claimed)
**Theorem 3 (no scalar ranks incomparable sources).** If `W₁` and `W₂` are
Blackwell-*incomparable* (neither garbles the other), then for *any* query-independent scalar
context-utility score `φ` (one number per source: relevance to a fixed corpus, MI, V-info,
perplexity-gap) there exist tasks `T_a, T_b` such that `φ` is unfaithful to the optimal-value
order on at least one of them. *(Revised 7 October 2026; this is manuscript Theorem 2. The June
statement said "realized PASS ranks them the opposite way", which conflated the optimal-value
order with a fixed model's PASS: the conclusion carries over to realized PASS only if the model
realizes a cross-advantage on that same task pair, an extra hypothesis (manuscript Assumption 1).
Query-conditioned scores are not covered; for them only the restricted manuscript Proposition 1
holds.)*

*Proof.* Incomparability ⟺ neither is a garbling of the other ⟺ (Blackwell, contrapositive)
there is a decision problem on which `W₁` strictly beats `W₂` and another on which `W₂`
strictly beats `W₁`. Instantiate those two decision problems as tasks `T_a,T_b`; any total
order `φ` fixes one ranking and is therefore violated on one of them. ∎

→ **Interpretation:** for a score held fixed across tasks, cross-task *non-transfer is not a
modeling failure — it is a theorem.* The structural order is partial; any task-independent scalar
imposes a total preorder that must violate it somewhere. *(The June claim that this "formally
explains the field's 'relevance doesn't transfer' folklore" is withdrawn: the theorem does not
cover the query-conditioned relevance used in retrieval; manuscript Theorem 2, Scope.)*

## 4. Le Cam deficiency (graded relaxation) and a decision-restricted surrogate
Exact garblings over text are uncomputable, and `⪰_B` is partial. **Le Cam's deficiency**
`δ(W₁,W₂)` = the minimal worst-case utility shortfall of `W₁` vs `W₂` after the best
garbling; `δ=0 ⟺` Blackwell dominance, `δ>0` grades approximate dominance. *(The June heading
called it "the measurable relaxation"; what is estimated below is a surrogate, not Le Cam
deficiency.)*

**Decision-restricted, estimable surrogate.** Fix the decision rule to *the LLM* and a finite task
set `𝒟`:
$$\hat\delta_{\mathcal D}(W_1,W_2)=\max\Big(0,\ \sup_{T\in\mathcal D}\big[\mathrm{PASS}(W_2,T)-\mathrm{PASS}(W_1,T)\big]\Big).$$
- Population `δ_{\mathcal D}=0` ⟺ `W₁` has PASS at least that of `W₂` on every task in `𝒟` for
  this model (the `δ_M`-restricted order). This is a fixed-model relation, not Blackwell
  dominance, and it transfers nothing to the Blackwell order, which concerns the optimal user
  (manuscript Remark 5). A plug-in `\hat\delta_{\mathcal D}=0` at finite `n` certifies nothing by
  itself. *(The June text called this "empirical Blackwell dominance for this model".)*
- **Finite-sample verification:** exact Clopper–Pearson intervals on every cell with Bonferroni
  correction over the `2|𝒟|` proportions, at family level `1−η` (§10.2; manuscript Proposition 2,
  where `η = 0.05`). *(The June text proposed a conformal/DKW guarantee over `n` sampled tasks and
  called it "the measurable version of Theorem 1". DKW does not apply (§10.2), the battery is a
  fixed task set rather than a task sample, and the guarantee concerns PASS, not Theorem 1.)*

(Honest weakening: this is PASS dominance *for this model on this fixed task set*. It is a
different relation from the universal order, not a weaker form of it: neither implies the other
unconditionally (manuscript Lemma 2). It is decision-restricted (one fixed rule) but still a
for-all-tasks-in-𝒟 statement, not a scalar. The surrogate is not Le Cam deficiency (manuscript
Remark 5); measured lower bounds on Le Cam deficiency come only from the hidden-state label
experiment under proved caps (manuscript Proposition 4).)

## 5. Contributions (paper)
*Revised 7 October 2026.* The June list claimed (1) a decision-independent partial order on LLM
context sources with for-all-tasks dominance guarantees, (2) the incomparability theorem as a
formal account of cross-task relevance non-transfer, (3) Le Cam deficiency as the measurable
relaxation, with the estimator `\hat\delta_{\mathcal D}` and a conformal certificate, and (4) the
moat `I(S;W|θ)` as one Blackwell-monotone scalar. That list is superseded. Current position
(manuscript Sections 1, 2.1 and 7): no priority is claimed for applying the Blackwell/Le Cam
apparatus to context selection, and the classical order is instantiated, not proposed. The
contribution is
1. the **distinction between the structural (Blackwell) relation and fixed-model PASS
   relations**: structurally incomparable pairs by construction (manuscript Lemma 1), the
   impossibility for query-independent scores (manuscript Theorem 2) and the restricted result for
   query-conditioned scores (manuscript Proposition 1);
2. the **hidden-state label experiment**, which lower-bounds Le Cam deficiency under proved
   guessing caps (manuscript Proposition 4, Section 5.7);
3. **controlled, replicated verification** of fixed-model PASS incomparability and superset harm,
   using a decision-restricted value-deficiency surrogate (not Le Cam deficiency; manuscript
   Remark 5), exact Clopper–Pearson bounds with Bonferroni correction for the original measurements
   and block-based Hoeffding bounds for the randomized replication and further pairs (manuscript
   Sections 3.4, 4.4, 5.1, 5.3, 5.4, 5.6).

## 6. The empirical demo (buildable now, existing harness)
- Construct two context sources `W₁,W₂` designed to be **incomparable** (e.g. `W₁` carries
  the API signature, `W₂` carries the usage convention; each wins on a different task).
- On a task set, measure `PASS(W₁,T)`, `PASS(W₂,T)`. **Show:** (i) a scalar relevance/MI
  score ranks `W₁>W₂` globally, yet (ii) `\hat\delta_{\mathcal D}(W₁,W₂)>0` *and*
  `\hat\delta_{\mathcal D}(W₂,W₁)>0` (mutual positive surrogate gaps = PASS incomparability for
  this model), with a constructed task pair where the scalar mis-ranks. *(Revised: the June text
  called this "empirical incomparability" that "instantiates Theorem 3 on a real model — the
  empirical anchor". It does not. Structural incomparability of `W₁, W₂` follows from the
  projection construction (manuscript Lemma 1). PASS incomparability is a fixed-model relation at
  a realized state and does not establish the structural relation: even the structurally
  comparable pair `W₁, W₁₊` crosses in PASS (manuscript Remark 3). Only the hidden-state label
  experiment links measurement to the structural relation, by lower-bounding Le Cam deficiency
  under proved caps (manuscript Proposition 4).)*
- Then a **dominance** case: `W₁ = W₂ + the convention` ⟹ `\hat\delta(W₂,W₁)>0`,
  `\hat\delta(W₁,W₂)=0` (here `W₁` PASS-dominates `W₂` for this model). *(The June text read this
  as "the for-all-tasks guarantee realized"; a fixed model's PASS dominance is a separate relation
  from the Blackwell guarantee, which concerns the optimal user.)*

## 7. Honest caveats
- **Partial order:** incomparable pairs exist (constructed here; how often real source pairs are
  incomparable is unmeasured — existence, not prevalence, manuscript Section 6.4) → practical
  selection still needs a tiebreaker; `\hat\delta` provides a graded one, but there is no free total order (that is
  the *point* of Thm 3, and also its practical limitation).
- **Restricted guarantee:** the verified surrogate certifies PASS dominance for *this model on
  this `𝒟`*, not universally. It is a different relation from the Blackwell order, not a weaker
  form of it: neither implies the other unconditionally (manuscript Lemma 2).
- **Positioning (revised 7 October 2026):** the closest prior work is Alpila (Zenodo, public
  25 June 2026), which already applies Blackwell/Le Cam ideas to inference-time context selection
  for a fixed decoder; no priority is claimed for the general application. The delta is the
  structural/fixed-model distinction, the hidden-state label experiment and controlled, replicated
  verification (manuscript Section 2.1). V-usable information (scalar) and "sufficient context"
  RAG (binary classifier) remain neighbours to differentiate from.
- **Novelty (revised):** the June estimate "~85%", with residual risk "mostly *internal* ... not
  external (prior art)", is withdrawn; see the positioning caveat above.

## 8. Venue
Theory-leaning empirical: **COLM**, **NeurIPS**, or **TMLR** (which welcomes a clean
theory+demo with honest scope). Pairs naturally as the *theory companion* to the empirical
papers (production-reality measurement; the workload moat).

## 9. Due diligence (completed 2026-06-19)

*Superseded as a novelty assessment (7 October 2026).* This search predates Alpila's preprint
(Zenodo, public 25 June 2026), which applies Blackwell/Le Cam ideas to inference-time context
selection for a fixed decoder. The record of what was searched and read is kept; its "open"
verdicts, the go/no-go and the related-work paragraph are superseded by manuscript Section 2.1.

**Method.** 8 parallel adversarial novelty-hunt agents (Blackwell×ICL, Le Cam×NLP, V-info
landscape, Blackwell-in-ML, EIG context selection, incomparability-in-IR, data-valuation,
channel-degradation) + synthesis; then full-text reads of the two binding threats. Result:
**0/8 angles report the comparison-of-experiments machinery applied to LLM context
selection.** The June conclusion "0 contributions pre-empted" is superseded (see the note above).

**Per-contribution verdict (June 2026; superseded).**
- **C1 (order): June verdict ADJACENT (lean open), withdrawn.** The deficiency/garbling *tool* is
  classical and already ported into ML (transfer learning), and its inference-time application to
  context selection for a fixed decoder is prior work (Alpila, 2026). The manuscript instantiates
  the classical order and cites this lineage.
- **C2 (incomparability theorem): June verdict OPEN, "the genuine novelty", withdrawn as a
  priority claim.** The math is classical (the Blackwell order is a non-lattice partial order,
  arXiv:1401.3146). The manuscript states it as Theorem 2 for query-independent scores and does
  not present it as explaining why relevance does not transfer across tasks.
- **C3 (certified PASS-rate surrogate): June verdict OPEN, withdrawn as a priority claim.** Alpila
  also describes fixed-rule performance gaps as deficiencies (manuscript Section 2.1). What the
  manuscript adds is the verification: simultaneous finite-sample bounds on a fixed model's PASS
  comparisons on a declared battery, replicated (manuscript Sections 2.3, 5.4).

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
   object (tasks vs context sources) + the PASS certificate** (exact Clopper–Pearson with
   Bonferroni, §10.2; the June text said "PASS/conformal").

**Biggest threat is NOT V-usable information** (June view; the closest prior work later proved to
be Alpila, 2026, see the note above). V-info is a scalar (Ethayarajh 2022; CaLE 2504.15630) →
used as one number per source, it is a *corollary victim* of C2, not a competitor. Disarm in one
sentence: V-info / MI / perplexity-gap / EIG, each used as one number per source held fixed across
tasks, are instances of the scalar class C2 rules out (C2 does not cover their task-conditioned
uses). Secondary threat: Bayesian experimental design / EIG (BED-LLM, arXiv:2508.21184 — the id
2604.00414 given here earlier belongs to a different paper; Conformal Information Pursuit
2507.03279) — scalar, decision-*dependent*; the clean separating axis is decision-*independent*
(for-all-tasks) dominance.

**Supporting signal (withdrawn).** The June note read arXiv:2604.06621 as applying the Blackwell
order to LLM internal representations and naming the empirical Blackwell-dominance test as an
open problem ("the gap is real and recognized"). The manuscript cites it only as a survey of
Blackwell's theorems for AI (Section 2.1) and draws no open-gap signal from it.

**Related-work paragraph (June draft; withdrawn 7 October 2026).** The "ready-to-use" draft that
stood here must not be reused. It claimed that the comparison-of-experiments apparatus had been
applied "never for LLM context" ("We close this gap"), that the incomparability theorem was "the
first formal account of why relevance does not transfer", and that `δ̂_D` came with a
"distribution-free conformal/DKW certificate" that prior deficiency work does not provide; it also
cited 2510.24652 for cross-task non-transfer of relevance, a citation the manuscript dropped.
Current account: Alpila (Zenodo, public 25 June 2026) already applies Blackwell/Le Cam ideas to
inference-time context selection for a fixed decoder; the impossibility covers only scores held
fixed across tasks (manuscript Theorem 2); the verification uses exact Clopper–Pearson intervals
with Bonferroni correction, not DKW (§10.2). The related work is manuscript Section 2, which cites
the draft's other references with its own characterizations: RankRAG (arXiv:2407.02485), Ethayarajh
et al., 2022, CaLE (2504.15630), BED-LLM (2508.21184), Conformal Information Pursuit (2507.03279),
DemoShapley (2410.07523), InfICL (2402.11750), sufficient context (2411.06037), 2504.07104, SURE-RAG
(2605.03534), Pareto prompt optimization (ICLR 2025), Le Cam meets LeCun (1402.4884), Fosse et al.
(2503.05491) and Le Cam Distortion (2512.23617).

**Go/no-go (June): GO.** Lead with C2 + C3; present C1 as scaffold and cite 2512.23617 up front.
*(Superseded: the manuscript claims no priority for the general application; its contribution is
stated in §5.)*

**Remaining checks (June list; status as of 7 October 2026 added to each):**
1. **Certificate math:** the sup_T in δ̂_D needs a *uniform* concentration bound over the task
   sample (union bound / empirical-process control), NOT naive pointwise DKW. **Done:** §10.2
   (exact Clopper–Pearson with Bonferroni; manuscript Proposition 2).
2. **Well-posed latent-S model:** define each "experiment's" sample space and what is observed,
   or a referee calls the partial order a metaphor. **Done:** §10.1; manuscript Section 3.1
   (Definitions 1–3, fixed strings read as projection experiments).
3. **C2 non-vacuousness:** closed by the construction, not by measurement: structural
   incomparability of W1, W2 follows from the projection construction (manuscript Lemma 1), so C2
   has non-vacuous instances. The harness below measures fixed-model PASS behaviour instead (§10.4).
   BUILT + mock-verified (2026-06-19) — `tokenbench/measure_blackwell.py`
   extends the moat harness: 2 incomparable private context sources W1 (ledger API contract) /
   W2 (wire-encoding invariant) on the SAME module, 7 tasks (4 W1-fam, 2 W2-fam, 1 relevance-trap),
   4 arms (none/W1/W2/W1plus), Haiku through the `claude -p` command-line client. Computes δ̂ both directions + the corrected
   uniform Clopper-Pearson+Bonferroni certificate (stdlib). **The fatal confound found in design
   ("query-conditioned relevance solves it") is fixed by the relevance-trap task**: a task
   lexically saturated with encoding vocab (so query-conditioned lexical relevance ranks W2>W1)
   whose graded requirement is the W1 post-contract (so PASS ranks W1>W2) → defeats
   query-conditioned lexical relevance (the case manuscript Proposition 1(b) covers; other
   query-conditioned rankers are an empirical question, manuscript Section 5.2). Mock shows:
   (A) certified PASS-incomparable at η = 0.10 (≥90%), (B2) the trap fires,
   (C) dominance control. Real run (planned as `python tokenbench/measure_blackwell.py --runs 10`,
   ~280 calls, ~$6; start n=10 (clean crossover certifies at n≥9), raise if the real split is
   noisy): **completed** 2026-06-19, see EXPERIMENT-BLACKWELL.md §9. Haiku produced the stark
   crossover and, after a stub fix and a same-day re-run, the trap mis-rank. Later runs are in
   EXPERIMENT-BLACKWELL.md §§10–15; the manuscript reads the HTTP-API record listed in
   `results/MANIFEST.md`.
4. **Pre-submission:** one fresh search for any 2026 follow-on porting 2512.23617 to LLMs (the
   most likely convergent pre-emptor), and a line-by-line PDF (not summarized) read of both
   threat papers. **Superseded by the revised analysis:** the closest prior work identified later
   is Alpila (Zenodo, public 25 June 2026), which applies Blackwell/Le Cam ideas to inference-time
   context selection for a fixed decoder; the manuscript positions the paper relative to it and
   cites both threat papers (Section 2.1).

## 10. Theory hardening for submission (addresses §9 checks 1–3)

**10.1 Well-posed latent-S experiment model (check 2).** A task `T` fixes a latent requirement
`S` (the object the verifier `v_T` checks). A context source `W` is an experiment: a Markov
kernel `κ_W : S → 𝒲` that emits a signal `w` (the source's text). The decision rule is the LLM
`δ_M : (T, w) ↦ Ŝ` (the generated solution). Utility is the binary verifier
`u(Ŝ,S)=v_T(Ŝ)∈{0,1}` (PASS). `PASS(W,T) := E[v_T(δ_M(T,w))]`, `w∼κ_W(·|S_T)`. This is well-
posed: the sample space of each experiment is the source's signal alphabet; what's observed is
the supplied text; the order is over these kernels. The estimator restricts the decision rule to
*this* `δ_M` and the tasks to a fixed finite set `D` (in the experiments a fixed adversarial
battery, not a sample from a task distribution; manuscript Section 5.1). That restriction is what
makes it computable, but the result is a different relation, not a relaxation of the universal
Blackwell order: neither implies the other unconditionally (manuscript Lemma 2). *(The June text
called it "a decision-restricted relaxation of the universal Blackwell order".)*

**10.2 Uniform certificate (check 1) — Proposition (PASS incomparability).** For each cell `(W,T)`
draw `n` i.i.d. PASS Bernoulli outcomes; let `[L_{W,T},U_{W,T}]` be the exact Clopper–Pearson
interval at level `α=η/(2|D|)`. By the union bound over the `2|D|` proportions
`{p_{W₁,T},p_{W₂,T}}_{T∈D}`, ALL hold simultaneously w.p. `≥1−η`. On that event,
`L_D(W₁,W₂):=max_{T}[L_{W₂,T}−U_{W₁,T}]` is a `(1−η)` lower confidence bound on
`sup_T[p_{W₂,T}−p_{W₁,T}]`; hence `L_D(W₁,W₂)>0` **certifies** `δ_D(W₁,W₂)>0`. Both directions
read off the *same* `2|D|` intervals, so the joint PASS-incomparability claim
`δ_D(W₁,W₂)>0 ∧ δ_D(W₂,W₁)>0` holds at `≥1−η` with no extra correction. *Why DKW fails:* DKW
bounds one ECDF's sup-deviation from its own CDF over a single i.i.d. sample; here the object is a
max over `|D|` *differences of two binomial means across distinct cells*, so the multiplicity must
be paid via the union bound, not absorbed by a single-sample sup inequality. (Implemented:
`certify_incomparable` / `clopper_pearson` in `tokenbench/measure_blackwell.py`.)

**10.3 Interference certificate (earlier harm criterion; superseded 7–8 September 2026).** The
June analysis defined the per-task interaction `I_T = PASS(W₁₊,T) − PASS(W₁,T) − PASS(W₂,T) +
PASS(none,T)` (W₁₊ a superset of W₁'s signal; the manuscript's `Ψ_T`) and certified "harmful
non-monotonicity" `I_T ≤ −τ` via the upper bound
`CPhi(p_{W₁₊}) − CPlo(p_{W₁}) − CPlo(p_{W₂}) + CPhi(p_{none})` at Bonferroni `α=η/4`. It also
claimed that a certified `I_T<0` is an object no monotone-submodular scalar can carry. Both
readings are wrong: `I_T ≤ 0` *is* the submodularity (diminishing-returns) condition for the pair,
so a negative `I_T` does not show that adding `W₂` to `W₁` hurt, and the two quantities can differ
even in sign (manuscript Remark 6). **Current criterion:** harm is the direct contrast
`Δ_T = PASS(W₁₊,T) − PASS(W₁,T)`, verified when its upper bound `U_{η/2}(W₁₊) − L_{η/2}(W₁)` (one
endpoint per arm, noncoverage `η/2` each) is at most `−τ`, with `τ = 0.30` used only for harm
contrasts and `η = 0.05` (manuscript Proposition 3, Section 4.3). A verified `Δ_T < 0` is what no
scalar monotone under `⪰_B` can represent: it shows that the fixed model rule is not
Blackwell-coherent on that task (manuscript Theorem 3), a statement about the rule, not the
sources.

**10.4 Check 3 closed by the construction; fixed-model PASS evidence, cross-model.** C2's
non-vacuousness does not rest on these runs: structural incomparability of `W₁, W₂` follows from
the projection construction (manuscript Lemma 1). The runs below measure fixed-model PASS
relations at the realized convention, which do not establish the structural relation (even the
structurally comparable pair `W₁, W₁₊` crosses in PASS; manuscript Remark 3). The measurement that
links to the structural relation is the hidden-state label experiment, which lower-bounds Le Cam
deficiency under proved caps (manuscript Proposition 4, Section 5.7). *(The June heading read
"Non-vacuousness — CERTIFIED" and called these runs "the full anchor".)* Measured with real model calls
across **six models** (Haiku 4.5, Sonnet 4.6, Opus 4.8, GPT-5.5, DeepSeek-V4-Pro, Kimi-K2.6); the
Haiku, Sonnet and Opus figures below come from the June command-line runs, which the manuscript
replaces with an HTTP-API record (EXPERIMENT-BLACKWELL.md, reading note before §9):
- PASS incomparability **certified ≥90%** (η = 0.10, the harness default then; the manuscript
  reports η = 0.05) (Haiku L_D +0.88/+0.83; Sonnet +0.76/+0.76).
- Confound-proof relevance mis-rank **confirmed** on both (Haiku, Sonnet; trap: relevance W2>W1,
  PASS W1≫W2).
- Anti-monotonicity is **large and robust across the capability ladder** (Haiku→Sonnet→Opus):
  the superset W₁₊ collapses the contract's effect by 75–100 points on the API cells in every
  model (Haiku 100→24/1%, Sonnet 100→0/0%, Opus 100→25/5%). Certified on 2 cells × 2 models
  (Haiku, Sonnet) under the earlier `I_T` criterion (§10.3); on Opus the point estimates are
  equally strong (I_T −0.75/−0.80) but n=20 was too few to certify. *(Superseded: in the HTTP-API
  record, under the direct contrast `Δ_T`, harm beyond the 0.30 margin is verified on both API cells
  of all six models marginally and on eleven of twelve under joint control; manuscript Section 5.3,
  Table 6.)* **HONEST CORRECTION:** an earlier 2-point read suggested the harm
  "intensifies with model strength" — the 3rd point (Opus) FALSIFIES monotonicity: Sonnet (middle)
  is the *starkest*, Opus (strongest) less so. The defensible claim is robustness across the ladder,
  NOT a capability trend. *(The June follow-on "new cross-model contribution" — that the harm "does
  not wash out with capability" — is withdrawn: no independent capability scale was measured, so the
  record supports no statement about capability either way; manuscript Section 5.3.)*
- `none` baselines floored at 0% on both Haiku and Sonnet. *(The June inference "the private
  conventions are unguessable even for the stronger model (the moat survives the capability
  ladder)" is withdrawn: observed zeros do not establish a zero population pass probability, and
  across the six models no-context PASS on `api_argorder` ranges from 0% to 100% (manuscript
  Sections 5.2–5.3); the value of the private source is model- and task-relative.)*
- Dominance positive control (`W₁₊` PASS-dominating `W₂`) certifies on both (Haiku, Sonnet); runtime output-token
  inflation (+87…+252%) is a consistent correlate of the collapse, not a mechanism (manuscript
  Sections 5.5, 6.2). See `EXPERIMENT-BLACKWELL.md` §10–12.

**10.5 Generality (June plan; completed).** The June record used ONE constructed pair
(API-contract `W1` vs wire-encoding `W2`) and planned ≥2 more private-convention pairs in distinct
domains (e.g., ID-format vs state-transition contract; date-encoding vs validation rule), each to be
shown PASS-incomparable (cheap on Haiku, ~$10–20), plus a cross-vendor (non-Anthropic) model run,
which then needed a non-Anthropic API key. *(The June text framed the pairs as establishing that
"the partial order is general" by showing each "empirically incomparable"; a constructed pair's
structural incomparability follows from its construction, and what further runs generalize is the
fixed-model PASS crossing.)* **Both were completed.** The cross-vendor runs (GPT-5.5,
DeepSeek-V4-Pro, Kimi-K2.6) are in §10.4 and EXPERIMENT-BLACKWELL.md §§12b–12d. A second pair
(`cache`) is EXPERIMENT-BLACKWELL.md §15. Three further pairs (`cache`, `inventory`, `audit`) were
run on all six models on 5 October 2026, with structural incomparability checked by enumeration and
PASS incomparability verified in 16 of 18 pair–model combinations (manuscript Sections 4.5 and 5.6;
`results/package2/confirm_pairs/`).
