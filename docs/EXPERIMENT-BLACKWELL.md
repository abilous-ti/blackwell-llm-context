# Experiment: the §6 empirical anchor for Theorem C2 (incomparability)

Synthesis of the `incomparability-demo-design` workflow (seed → design → adversarial-verify),
hardened in the main loop after the verify pass returned **1 fatal + 3 flawed** and the
synthesis agent died on a session limit. This is the consolidated, runnable spec. The harness
is `tokenbench/measure_blackwell.py` (built, mock-verified; real run pending).

**Goal.** Make C2 non-vacuous on a *real* LLM: exhibit two Blackwell-incomparable context
sources and show, with measured HTTP-API PASS rates + a correct uniform certificate, that
(A) neither source dominates, (B) the scalar score practitioners actually use mis-ranks them,
and (C) the estimator also detects genuine dominance. No modeled numbers — the run adjudicates.

---

## 1. The two context sources (literal)

Both are *unguessable, house-private* facts about the **same** module `ledger`, so any
relevance / MI / embedding scalar treats them as equally on-topic candidates for a "ledger"
task — the precondition for C2 to bite.

- **W₁ — API call contract.** `ledger.post(account, amount, *, memo)` — `account` first,
  `amount` second positional, `memo` required keyword-only; returns an int entry id ≥ 1;
  raises `ledger.PostError` (not ValueError/KeyError) on failure.
- **W₂ — wire-encoding invariant.** amounts serialize to `<sign><minor-unit-digits>#<check>`,
  check = (sum of digits) mod 10. `$12.30 → "+1230#6"`, `-$0.07 → "-7#7"`. Decode rejects a
  wrong check digit.
- **W₁₊ — dominance control.** `W₂ ++ W₁` (literal superset of W₂'s signal ⇒ W₁₊ ⪰_B W₂).

**Why incomparable (garbling argument).** A garbling is a kernel on the *signal alone*. From
W₂'s wire format you cannot manufacture the private arg-order / required-kw / exception type;
from W₁'s contract you cannot manufacture the cents-scale / `#` / mod-10 check. The two facts
are logically independent coordinates of the solution S, so neither σ-algebra refines the
other → neither sufficiency direction holds → Blackwell-incomparable.

**Confound defense (the make-or-break).** W₁ and W₂ are matched on every nuisance axis (length,
~3 sentences, exactly one private convention each, same module, same task shape). The signature
is the **double crossover** measured against a `none` baseline: W₁ lifts API tasks *and not*
encode tasks; W₂ lifts encode tasks *and not* API tasks. If encode tasks were merely "harder,"
W₁ wouldn't lift them *and* W₂ wouldn't lift its own family from the same floor. The matched
`none` baselines should be statistically indistinguishable (both near floor) → equal intrinsic
hardness; divergence appears only when the matching private fact is supplied.

---

## 2. Task set D (7 tasks; full prompts + verifiers in the harness)

| id | family | decisive fact | verifier asserts | pred. PASS `none / W₁ / W₂ / W₁₊` |
|---|---|---|---|---|
| `api_post_ok` | api | W₁ | correct `post(acct,cents,memo=…)`, returns id | ~0 / **1** / ~0 / **1** |
| `api_argorder` | api | W₁ | exact `(acct,amount,memo)` call recorded | ~0 / **1** / ~0 / **1** |
| `api_error_type` | api | W₁ | catches `ledger.PostError` specifically | ~0 / **1** / ~0 / **1** |
| `api_memo_required` | api | W₁ | memo passed as required kw | ~0 / **1** / ~0 / **1** |
| `enc_amount` | enc | W₂ | exact wire strings incl. `+0#0` | ~0 / ~0 / **1** / **1** |
| `dec_amount` | enc | W₂ | round-trip + rejects bad check digit | ~0 / ~0 / **1** / **1** |
| `trap_store_wire` | **trap** | W₁ | posts an already-encoded wire string (pass-through) | ~0 / **1** / ~0 / **1** |

The verifiers stub a fake `ledger` module that accepts **only** the exact private contract
(rejects wrong arg order positionally, missing `memo=`, wrong exception type).

---

## 3. Scalar battery (B)

- **(B1) outcome-aggregate `φ = mean PASS-lift over D` — CONTRAST ONLY.** Circular (computed
  from the outcomes) and its global order depends on the task mix. Shown only to mark the weak
  case; *not* the claim.
- **(B2) query-conditioned lexical relevance `φ_lex(W,T)` — THE REAL TEST.** Bag-of-words
  cosine between a source and the task prompt, computed *before* running the model — what
  retrieval/RAG actually uses. **This is the fix for the fatal confound** ("just use relevance
  of W to this task"): the `trap_store_wire` prompt is saturated with encoding vocabulary, so
  `φ_lex(W₂,trap) > φ_lex(W₁,trap)`, yet the task needs the W₁ contract, so
  `PASS(W₁,trap) > PASS(W₂,trap)`. On the honest enc tasks relevance is *correct* (W₂>W₁ and
  PASS agrees) — so relevance fails **only** where utility diverges from topicality. ⇒ no
  query-conditioned relevance score can rank these sources correctly for all tasks (C2, strong
  form, confound-proof).

---

## 4. Estimator + uniform certificate

- **Estimator:** `δ̂_D(W₁,W₂) = max(0, sup_{T∈D}[PASS(W₂,T) − PASS(W₁,T)])`, per-task PASS = k/n.
- **Empirical incomparability:** `δ̂_D(W₁,W₂) > 0 AND δ̂_D(W₂,W₁) > 0`.
- **Certificate (the corrected part).** The sup selects the argmax-gap task, so a pointwise
  DKW/Hoeffding bound on that one task ignores the multiplicity (false-positive rate climbs with
  |D|). Fix: exact Clopper-Pearson CIs on all `2|D|` per-task proportions at Bonferroni level
  `α_pair = η/(2|D|)` (union bound ⇒ all hold jointly at ≥ 1−η). Then
  `L_D(W₁,W₂) = max_T [ CPlo(p_{W₂,T}) − CPhi(p_{W₁,T}) ]` is a 1−η lower bound on the sup;
  `L > 0` **certifies** δ̂ > 0. Both directions read off the same `2|D|` intervals, so the
  joint incomparability claim holds at ≥ 1−η. Dominance (C) splits the η budget across its two
  sub-claims. (Stdlib Clopper-Pearson via regularized incomplete beta — zero deps.)
- **Sample size:** worst case (p≈0.5) n≥83/cell; **stark crossover (clean ~0% vs ~100%, as
  designed) n≥9/cell** → start at n=10, raise only if the real split is noisy.

---

## 5. Code

`tokenbench/measure_blackwell.py` — complete, cross-OS, zero-dep, `--mock` + real modes;
extends `measure_moat.py` (claude_cmd / verify_in / temp-dir / cost parse / flattened prompts /
utf-8). Key functions: `hat_delta_D`, `incomparability_test`, `clopper_pearson`,
`certify_incomparable`, `certify_dominance`, `required_n` / `required_n_stark`,
`lexical_relevance`. Writes `blackwell_results.json`.

---

## 6. Expected results (real run, if C2 holds)

- **(A)** δ̂(W₁,W₂) ≈ +1.0 (sup on an enc task), δ̂(W₂,W₁) ≈ +1.0 (sup on an api task); both
  certificate lower bounds `L > 0` → **certified incomparable at ≥ 90%**.
- **(B2)** every api/enc task: relevance rank == PASS rank (relevance correct); **`trap_store_wire`:
  relevance W₂>W₁ but PASS W₁>W₂** → strong Thm-3 violation printed.
- **(C)** δ̂(W₁₊,W₂) ≈ 0 (U_D ≤ margin), δ̂(W₂,W₁₊) > 0 (certified) → one-directional dominance.

---

## 7. Falsification criteria (honest, up front)

The non-vacuousness claim is **disproved** if the real run shows any of:
1. **no crossover** — one source dominates (only a dominance demo, not incomparability);
2. **trap doesn't mis-rank** — relevance tracks utility on the trap (the strong C2 claim fails;
   the source-level incomparability in (A) would still hold for query-*independent* ranking);
3. **asymmetric baselines** — the two families' `none` PASS rates differ materially (a
   difficulty confound after all);
4. **underpowered** — `L` stays ≤ 0 at adequate n (the effect isn't certifiable).
The harness prints whichever way it lands; report it faithfully.

---

## 8. Run

```
python tokenbench/measure_blackwell.py --runs 10        # real: ~280 calls, ~$6
python tokenbench/measure_blackwell.py --mock --runs 10  # pipeline check, no API
```

**Watch on the real run:** (a) the `L_D` values in (A) — bump `--runs` if either is barely
positive; (b) `U_D` in (C) — W₁₊ must hit ~100% on enc tasks or dominance won't certify;
(c) the per-task `none` PASS rates — confirm both families floor near 0 (confound check).

---

## 9. REAL RUN RESULT (2026-06-19, n=10, 280 live claude -p Haiku calls, $9.09)

Mixed, honest outcome. `blackwell_run.log` / `blackwell_results.json`.

- **(A) INCOMPARABILITY — CERTIFIED ✓ (the core win).** δ̂(W₁,W₂)=δ̂(W₂,W₁)=+1.0;
  uniform certificate L_D=+0.138 both directions → **certified incomparable at ≥90%**. The two
  carrying cells are confound-clean: `api_post_ok` (none 0% / W₁ 100% / W₂ 0%) and `enc_amount`
  (none 0% / W₁ 0% / W₂ 100%). This is real, certified empirical Blackwell incomparability on a
  live model → **C2's non-vacuousness anchor holds.**
- **(B2) STRONG relevance mis-rank — CONFIRMED ✓ on a live model (re-test 2026-06-19, n=10,
  30 calls, $0.97, `blackwell_trap_results.json`).** After the stub fix (accept str amounts;
  trap stays W₁-decisive on arg-order/memo/return-id), `trap_store_wire`: none 0% / **W₁ 80%** /
  W₂ 0%. Query-conditioned lexical relevance φ_lex(W₁)=0.36 < φ_lex(W₂)=0.44 → relevance ranks
  **W₂>W₁**, yet realized PASS ranks **W₁>W₂** → the scalar practitioners actually use mis-ranks
  the sources. The `none=0%` floor confirms genuine unguessability; `W₂=0%` confirms encoding
  knowledge is useless here. **The "just use relevance-of-W-to-T" confound is defeated on a real
  model** — this is the strong, confound-proof form of Theorem 3 (C2).
  (Original full run's trap was 0% under W₁ due to the now-fixed stub bug.)
- **(C) DOMINANCE — FAILED, and the failure is a real result.** W₁₊ (=W₂++W₁, strictly more
  info) DEGRADED API PASS vs W₁ alone (100%→10–40%): real LLMs are **not context-monotone**, so
  the idealized "superset Blackwell-dominates" prediction breaks empirically. The estimator
  correctly flagged non-dominance (δ̂(W₁₊,W₂)=0.10>0). Honest negative worth reporting.
- **Confound nuance:** 3/4 API `none` baselines were 30–50% (partially guessable), not floor;
  only `api_post_ok` + both enc tasks floored at 0%. The certified result rests on the clean
  cells, so (A) is robust, but the API family is weaker than designed.

**Verdict:** the headline (empirical, certified, confound-clean incomparability) HOLDS and is the
non-vacuousness anchor for C2. The strong query-conditioned mis-rank (B2) is untested pending the
trap fix re-run. The dominance control (C) yielded a genuine anti-monotonicity finding instead.

---

## 10. ORDER CONTROL (lead C) — REAL RUN (2026-06-20, n=8, 160 calls, $5.18)

`blackwell_orderC_run.log` / `blackwell_orderC_results.json`. 4 API collapse cells, arms
none/W1/W2/W1plus/W1plus_rev (W1plus_rev = W1++W2, i.e. W1 FIRST).

- **Anti-monotonicity reproduced:** interference I_T = PASS(W1plus)−PASS(W1)−PASS(W2)+PASS(none) is
  **negative on all 4 API tasks (−0.38 to −0.50)** — adding W2 to W1 hurts.
- **Reordering does NOT recover it (ORDER-ROBUST HARM):** W1-alone = 62/100/88/88%, yet the *better*
  of {W1plus, W1plus_rev} reaches only 25/75/100/25%; on **3/4 tasks both orderings stay >0.20 below
  W1-alone**. So the harm is **not** a lost-in-the-middle / recency artifact → this **hardens** the
  anti-monotonicity result. (Caveat: per-task order gaps are noisy at n=8; the recovery-vs-W1 test —
  not the gap sign — is the decision-relevant one. The harness verdict was corrected to test recovery.)
- **Runtime fingerprint (lead D), cleanest signal:** the harmful W1plus arm emits **+54% to +116%
  more output tokens** than W1 on every task — verbose thrashing, a consistent mechanism tell.
- **Large run-to-run variance** (W1 api_post_ok 100%→62%; W2 api_error_type 40%→100% across runs)
  ⇒ n=8 is DIRECTIONAL only; I_T is not yet certified (upper bounds positive). **n≈80 still required.**

**Net:** anti-monotonicity now seen in 2 real runs, shown order-robust, with a clean output-token
fingerprint — but NOT publication-grade until the n≈80 bundled re-run (`--arms
none,W1,W2,W1plus,W1plus_rev`). The *phenomenon* "context hurts" is published (2510.05381, 2605.05716);
the novelty is its instantiation on certified-incomparable private sources under the deficiency framework.

---

## 11. n=80 BUNDLED CERTIFICATION — REAL RUN (2026-06-20, 1600 calls, 6-way concurrent, $51.40)

`blackwell_n80_run.log` / `blackwell_n80_results.json`. 4 cells (api_post_ok, api_argorder,
enc_amount, trap_store_wire) × 5 arms × n=80. **The publication-grade anchor. Four of five claims
certify; the fifth holds on the clean cell.**

- **(A) INCOMPARABILITY — CERTIFIED ≥90%, decisively.** δ̂(W1,W2)=+1.0, δ̂(W2,W1)=+0.97;
  certificate **L_D(W1,W2)=+0.877, L_D(W2,W1)=+0.831** (vs the marginal +0.138 at n=10 — now far
  clear of 0). Stark cells: api_post_ok none 0% / W1 98% / W2 0%; enc_amount none 0% / W1 0% / W2 100%.
- **(B2) RELEVANCE MIS-RANK — CONFIRMED, clean.** trap: relevance φ(W1)=0.36 < φ(W2)=0.44 → ranks
  **W2>W1**, yet PASS **W1 96% vs W2 0%** → W1>W2. On honest tasks relevance agrees with PASS
  (api: W1>W2 both; enc: W2>W1 both) — relevance fails ONLY where utility diverges from topicality.
- **(C) DOMINANCE positive control — NOW CERTIFIES.** W1plus ⪰ W2 (W1plus ≥ W2 on every task):
  U_D(W1plus,W2)=0.061 ≤ 0.15 and W1plus strictly beats W2 somewhere → one-directional dominance
  REALIZED. The deficiency estimator detects genuine dominance, not just incomparability.
- **(D) ANTI-MONOTONICITY (interference) — CERTIFIED on api_post_ok.** I_T = −0.74, **upper bound
  −0.49 ≤ −0.30 → CERTIFIED HARM**. (api_argorder I_T=−0.44 but upper −0.08 — NOT certified because
  its `none` baseline is 40%, the leaky-baseline problem; enc/trap I_T≈0 as expected.) So the
  superset W1plus performs FAR worse than its component W1 (24% vs 98%) — a certified falsification
  of Blackwell superset-dominance on a live model, on the clean cell.
- **(E) ORDER-ROBUST — confirmed at power.** On both API collapse cells, neither ordering recovers
  W1-alone: api_post_ok W1plus 24% / W1plus_rev 1% (vs W1 98%); api_argorder W1plus 24% /
  W1plus_rev 44% (vs W1 100%). Reordering does NOT cure the harm → not a lost-in-the-middle artifact.
- **(F) RUNTIME fingerprint — clean.** W1plus emits +106% / +87% / +252% / +12% more output tokens
  than W1 — the harmful (and even the still-passing enc) superset arm is consistently more verbose.

**Status: publication-grade anchor achieved for incomparability + relevance mis-rank + dominance +
order-robustness, and anti-monotonicity certified on 1 clean cell.** (Gap 1 closed below.)

### 11a. Anti-monotonicity 2nd cell — HARDENED api_argorder, n=80 (2026-06-20, 320 calls, $10.41)
`blackwell_argorder_n80.json/.log`. api_argorder was hardened so its memo comes from a PARAMETER
(mirroring api_post_ok), making it depend on the unguessable kw-only-memo fact; baseline dropped
40% → **1%** (W1 still 100% — not over-corrected). Result: none 1% / W1 100% / W2 0% / **W1plus 1%**
→ **I_T = −0.97, upper bound −0.79 ≤ −0.30 → CERTIFIED HARM.** A near-total collapse (100%→1%) —
starker than api_post_ok (100%→24%). Runtime tell +111%. **Anti-monotonicity is now certified on
TWO independent cells** (api_post_ok upper −0.49; api_argorder upper −0.79). Gap 1 closed.

**Remaining hardening (only one item left, and it is confirmation not discovery):** single model
(Haiku) — replicate incomparability + I_T on ≥1 more model (task 06, ~$40/model). Everything else
in the anchor is certified on real `claude -p` spend. **(Closed below — §12.)**

## 12. CROSS-MODEL REPLICATION — SONNET, n=40 (2026-06-20, 640 calls, $44.77) — ANCHOR COMPLETE

`blackwell_sonnet_n40.json/.log`, `--model claude-sonnet-4-6`, 4 cells × arms none/W1/W2/W1plus.
**Every core claim replicates on the stronger model — and the anti-monotonicity is STARKER.**

- **`none` baselines ALL floor at 0%** (api_post_ok / api_argorder / enc_amount / trap) — the
  private conventions are unguessable *even for Sonnet*. (Stronger model ≠ guesses the moat.)
- **(A) Incomparability — CERTIFIED ≥90%:** L_D = +0.762 both directions; clean double crossover
  (W1 solves API+trap 100% / fails enc; W2 solves enc 100% / fails API+trap).
- **(B2) Relevance mis-rank — CONFIRMED:** trap relevance W2>W1 but PASS W1 100% vs W2 0%;
  relevance agrees with PASS on honest tasks.
- **(C) Dominance control — CERTIFIES:** W1plus ⪰ W2, U_D=0.119, one-directional REALIZED.
- **(D) Anti-monotonicity — CERTIFIED on BOTH cells, MAXIMAL on Sonnet:** api_post_ok and
  api_argorder both go **W1 100% → W1plus 0%** → **I_T = −1.00, upper −0.69 ≤ −0.30** on each.
  (See §12a: a 3rd model, Opus, shows the harm is large but NOT monotone in capability — Sonnet is
  the starkest, so do NOT claim "intensifies with strength"; the defensible claim is robustness
  across the capability ladder.)
- **(F) Runtime tell:** W1plus +120% / +131% output tokens on the collapse cells.
- (One W2/trap call hit a cmd error; W2/trap is 0% by design, so it didn't affect the result.)

**STATUS: the Blackwell empirical anchor is COMPLETE across two models** (Haiku 4.5 + Sonnet 4.6),
all core claims certified on real `claude -p` spend (~$123 total). Incomparability, the confound-
proof relevance mis-rank, anti-monotonicity (2 cells/model), order-robustness, dominance control,
and the runtime fingerprint all hold.

## 12a. THIRD MODEL — OPUS 4.8, n=20 (2026-06-20, 320 calls, $49.84) + the monotonicity correction

`blackwell_opus_n20.json/.log`, `--model claude-opus-4-8`. Completes the capability ladder.
- **(A) Incomparability — CERTIFIED ≥90%:** L_D = +0.552 both directions (api_post_ok none 0%/W1
  100%/W2 0%; enc_amount none 0%/W1 0%/W2 100%).
- **(B2) Relevance mis-rank — CONFIRMED:** trap relevance W2>W1, PASS W1 100% vs W2 10%.
- **(D) Anti-monotonicity — reproduces, not certified at n=20:** W1plus collapses 100%→25% /
  100%→5%; I_T −0.75/−0.80 (strong) but upper −0.08/−0.11 (n=20 too few + Opus baseline leak:
  argorder/trap `none`=15%). Needs n≈80 to certify on Opus.
- **(C) Dominance:** strict-beat certified, but U_D=0.224 > 0.15 at n=20 (underpowered, not "clean").
- **(F) Runtime tell:** +204%/+204% output tokens on the API collapse cells.

**HONEST CORRECTION (important).** After Haiku+Sonnet I wrote that anti-monotonicity "intensifies
with model strength." The 3-point ladder FALSIFIES monotonicity:
| cell | Haiku | Sonnet | Opus |
|---|---|---|---|
| api_post_ok | 100→24% | 100→0% | 100→25% |
| api_argorder | 100→1% | 100→0% | 100→5% |
Sonnet (middle) is the *starkest*; Opus (strongest) is *less* so. **Defensible claim: the harm is
large and ROBUST across the capability ladder — NOT a monotone capability trend.** (Running the
3rd model is exactly what caught the overclaim; the earlier "intensifies" wording was retracted in
§12 and BLACKWELL.md §10.4.)

## 12b. CROSS-VENDOR — GPT-5.5 (Azure), n=40 (2026-06-20, 640 calls, your Azure quota)

`blackwell_gpt55_n40.json/.log`. Stdlib `urllib` Azure Responses launcher (key via env, never in a
file). **GPT path is single-shot completion + code extraction (NOT agentic like `claude -p`)** — a
cleaner probe of context-use, but a methodological difference to state in the paper. ($ shows 0 —
Azure API returns no cost field; token counts captured.)
- **(A) Incomparability — CERTIFIED ≥90% CROSS-VENDOR:** L_D = +0.762 both directions. ← the
  headline: incomparability is NOT an Anthropic-family artifact.
- **(B2) Relevance mis-rank — CONFIRMED:** trap relevance W2>W1, PASS W1 100% vs W2 0%.
- **(C) Dominance — CERTIFIES:** W1plus ⪰ W2, U_D=0.119, one-directional REALIZED.
- **(D) Anti-monotonicity — CERTIFIED on api_post_ok:** I_T −0.95, upper −0.60 (W1plus 100→0%).
  api_argorder does NOT certify because GPT's `none` baseline is 75% (see below).
- **(F) Runtime tell:** +281% / +274% output tokens on the API collapse cells.
- **NEW cross-vendor finding — the moat is MODEL-RELATIVE.** GPT-5.5 guesses the "private"
  conventions far more than Claude: `none` baselines api_argorder **75%**, enc_amount **55%**
  (Claude floored at 0% on both). So I(S;W|θ) genuinely depends on θ — GPT's prior already holds
  much of W. The certified claims rest on cells unguessable *for the model under test* (api_post_ok
  none 5%, trap 0% for GPT). This is the theory's model-relativity made empirical, not a failure —
  but it caps which cells certify per model, and means the demo's conventions are unguessable-for-
  Claude, partially-known-to-GPT. (One Azure HTTP 500 on a W2/trap call; that cell is 0% by design.)

## 12c. CROSS-VENDOR #2 — DeepSeek-V4-Pro (Azure AI Foundry /openai/v1/), n=40 (2026-06-21)

`blackwell_deepseek_n40.json/.log`. Third vendor; uses the OpenAI-compatible chat-completions API
(launcher auto-detects style from endpoint; retry-on-transient added). Single-shot, key via env.
- **(A) Incomparability — CERTIFIED:** L_D = +0.347 / +0.715 (both >0). Third vendor.
- **(B2) Relevance mis-rank — CONFIRMED:** trap relevance W2>W1, PASS W1 98% vs W2 0%.
- **(D) Anti-monotonicity — CERTIFIED on api_post_ok:** I_T −0.75, upper −0.36 (W1plus 0% vs W1 75%).
- **(F) Runtime tell:** +93% / +166% on the API collapse cells.
- **Sharpens the moat finding:** DeepSeek's `none` baselines are TIGHT like Claude (0/2/0/0%) — so
  GPT-5.5's wide prior (55–75% guessing) is **vendor-specific, not a general capability effect**;
  the model-relative moat tracks a vendor's *training*, not raw strength. Caveat: DeepSeek
  under-executes even WITH context (W1 rescues api_post_ok only to 75%, argorder 68%, vs ~100% for
  Claude/GPT) — an honest capability difference that shrinks the certified margin (argorder I_T
  upper −0.15, not certified).

## 12d. CROSS-VENDOR #3 — Kimi-K2.6 (Moonshot, Azure /openai/v1/), n=40 (2026-06-21)

`blackwell_kimi_n40.json/.log`. 4th vendor; chat-completions path, single-shot, key via env.
- **(A) Incomparability — CERTIFIED:** L_D = +0.675 / +0.762.
- **(B2) Relevance mis-rank — CONFIRMED:** trap relevance W2>W1, PASS W1 100% vs W2 0%.
- **(D) Anti-monotonicity — CERTIFIED on api_post_ok, MAXIMAL:** I_T −1.00, upper −0.69 (W1plus 0%
  vs W1 100% — total collapse, like Sonnet). api_argorder I_T −0.55 (not certified; baseline 45%).
- **(F) Runtime tell:** +203% / +249% on the API collapse cells.
- Baselines: api_post_ok/enc/trap ~0%, **api_argorder 45%** (partially knows the arg-order convention).

## 13. CONSOLIDATED 6-MODEL / 4-VENDOR VERDICT

| Claim | Haiku | Sonnet | Opus | GPT-5.5 | DeepSeek | Kimi-K2.6 |
|---|---|---|---|---|---|---|
| *vendor* | Anthropic | Anthropic | Anthropic | OpenAI | DeepSeek | Moonshot |
| Incomparability certified | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Relevance mis-rank | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Anti-monotonicity certified | ✅ 2 | ✅ 2 | ▲ n=20 | ✅ 1 | ✅ 1 | ✅ 1 |
| `none` argorder baseline | ~0% | 0% | 15% | 75% | 2% | 45% |

**Bottom line:** incomparability + the confound-proof relevance mis-rank replicate on **6 models
across 4 vendors** (Anthropic, OpenAI, DeepSeek, Moonshot) — decisively NOT a single-lab artifact.
Anti-monotonicity certified on ≥1 cell for 5/6 (Opus reproduces at n=20; needs n≈80), robust but NOT
monotone in capability. **Model-relative moat — now a continuous spectrum:** the `api_argorder`
`none` baseline runs Claude ~0% · DeepSeek 2% · Opus 15% · Kimi 45% · GPT-5.5 75%, so I(S;W|θ)
varies *continuously* across models — a clean empirical map of θ-dependence that tracks vendor
training more than capability. **Honest scope notes for the paper:** (1) frame the moat as
model-relative (the stronger framing) — or author more-exotic conventions for a vendor-universal 0%
floor; (2) Claude=agentic vs others=single-shot completion (a methodological difference, arguably a
cleaner context-use probe). Evidence is now far beyond paper-sufficient — the binding constraint is
WRITING, not more models.

## 14. CONFOUND-BREAK — Haiku SINGLE-SHOT vs agentic (2026-06-21, n=40, 640 calls, $13.47)

`blackwell_haiku_singleshot_n40.json/.log`, `--singleshot` (claude -p --max-turns 1, no tools;
code extracted from returned text = the SAME single-shot regime as the Azure models). Directly
breaks the vendor/harness confound (Anthropic=agentic vs others=single-shot) by measuring ONE model
both ways. **The effect survives the non-agentic harness:**
- Incomparability **CERTIFIED** (L_D +0.762 both directions) — vs agentic +0.88/+0.83.
- Relevance mis-rank **CONFIRMED** (trap relevance W2>W1, PASS W1 90% vs W2 0%).
- Dominance control **CERTIFIES** (one-directional).
- Anti-monotonicity **CERTIFIED on api_argorder** (I_T −0.93, upper −0.56). api_post_ok not
  certified single-shot (W1 rescue 52% vs 98% agentic — no agentic retries to self-correct — so the
  gap is smaller), but the effect direction holds (I_T −0.38). Runtime tell +115/+163/+114%.

**Conclusion: the incomparability, relevance-mis-rank, dominance, and anti-monotonicity results are
NOT artifacts of the agentic harness** — they replicate for the same model under single-shot
completion. This addresses the reviewer's #1 experimental concern (the agentic/single-shot ×
vendor confound). Honest nuance: agentic retries make Claude more reliable at *executing* a known
contract (post_ok 98% vs 52%), so absolute PASS differs by regime, but the order-theoretic claims
(certified incomparability + certified interference) hold in both.

## 15. GENERALITY — 2nd source pair in a DIFFERENT domain (2026-06-21, Haiku, n=40, 480 calls, $14.40)

`measure_blackwell_pair2.py`, `blackwell_pair2_n40.json/.log`. A 2nd incomparable private pair in a
`cache` module — V1 = `cache.put(key, value, *, ttl)` contract (arg order, kw-only ttl, True/False
insert flag, CacheError); V2 = key normalization invariant ('kx7-' namespace + underscore rule).
Reuses the full estimator/certificate machinery via monkeypatch. **Result: the partial order is NOT
a one-off.**
- Incomparability **CERTIFIED** (L_D +0.774 / +0.496) — clean double crossover in a different domain
  (V1 wins cache_put_ok+trap; V2 wins key_norm; all `none` baselines floor at 0%).
- Dominance control **CERTIFIES** (one-directional, U_D=0.113).
- Anti-monotonicity **reproduces in direction** (W1plus collapses cache_put_ok 80→28%, trap 75→48%;
  I_T −0.53/−0.28) but NOT certified at n=40 (W1 rescue only ~80%, smaller gaps than pair 1; needs
  n≈80). Runtime tell +67/+79%.
- Relevance mis-rank: **honest NULL** on pair-2's trap — the trap prompt's vocabulary leaned toward
  V1 (φ_lex 0.39 vs 0.25), so relevance AGREED with PASS; the trap design did not achieve the
  V2-lean for this domain. The strong mis-rank therefore remains a pair-1 result (6 models); pair 2
  establishes **generality of the incomparability + dominance results**, which was its purpose.

**Limitations §8 update:** the "single source pair" gap is now closed for the *incomparability* and
*dominance* claims (2 pairs, 2 domains, both certified). The strong *relevance mis-rank* is shown on
1 pair across 6 models; a vendor-/domain-general mis-rank would need a re-designed pair-2 trap (the
prompt must be lexically V2-leaning). Anti-monotonicity is certified on pair 1 (cross-vendor) and
directional on pair 2 (would certify at n≈80).
