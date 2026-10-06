# Declarative label experiment: confirmatory protocol

Status: DRAFT, 5 October 2026, written before any request of this experiment. It is frozen
(`freeze_labels.py`: code, this file and the confirmatory schedule with its hidden states) after
the smoke run is read for defects and before the first confirmatory request.

## 1. Purpose (R1.1, R3.2, R3.3)

A statistical lower bound on directional deficiency under proved caps, measured over freshly
sampled hidden states, for the two certified pairs (inventory, audit). It complements and does not
replace (i) the structural theorem, the finite-family no-garbling argument of Lemma 1, which is the
deterministic proof of incomparability, and (ii) the fixed-model PASS comparisons at the realized
state (package 2, Section 1). The bound L - c is a different statistic from the paper's PASS-gap
surrogate; it is not an estimator of the full Le Cam deficiency.

## 2. Decision problem

States theta = (theta_A, theta_B) range over the declared families of `pairs.py` (inventory 8 x 8,
audit 3 x 8) under the uniform product prior. Observation: none, A(theta_A) or B(theta_B), the
package-2 renderings. Decision in the X-label task (X in {A, B}): an option number from a fixed
menu that lists every point of X's family; utility 1 when the option is theta_X, 0 otherwise
(invalid replies 0). The question, the menu and the answer instruction are identical for every
state. Grading compares the chosen number with the hidden state in the analysis process; no reply
is executed.

## 3. Theorem used

Directional deficiency delta(E_A, E_B) = inf_K sup_theta TV(K P_theta^A, P_theta^B), with
TV(P, Q) = sup_C |P(C) - Q(C)|. For utility in [0, 1] and prior pi: if the Bayes value of E_A (best
over all rules with the same decision space) is at most c, and a fixed rule using E_B has success
probability q_B, then delta(E_A, E_B) >= max(0, q_B - c); with a valid lower confidence bound L_B on
q_B, delta(E_A, E_B) >= max(0, L_B - c) on its coverage event. This is the classical randomization
(risk-comparison) argument (van Rooyen and Williamson, 2014, Section 4.1 and Appendix 7.9), applied
in both directions; it is not a new theorem about Le Cam deficiency.

Caps, proved by enumeration in `labels.certify()`: every decision of the complete decision space
{1, ..., N, invalid} is accepted under at most r = 1 state, so under the uniform prior a rule whose
input carries no information about theta_X succeeds with probability at most r/N: inventory A 1/8,
inventory B 1/8, audit A 1/3, audit B 1/8. The input of the decision procedure is the prompt only:
no execution feedback, files, checker objects or request metadata reach the model. The no-context
prompt is identical for all states, and the other-source prompt depends on the other coordinate
only (both checked by enumeration), which under the product prior is independent of theta_X. The
own-source rendering is injective and an ideal reader attains value 1 (checked).

## 4. Design and analysis

- Blocks: per model, pair and label task, n = 40 blocks. Each block draws theta_A and theta_B
  independently, uniformly, with replacement, from operating-system entropy; the three arms (none,
  A, B) share the block's state; arm order is shuffled and blocks are interleaved per model; four
  lanes per model. 2 pairs x 2 tasks x 3 arms x 40 blocks x 6 models = 2,880 requests. The schedule,
  states included, is written before the first request and hashed by the freeze. The record of the
  draws is an audit device, not evidence of secrecy, which rests on the prompt-only input (Section 3).
- Models: Haiku-4.5, Sonnet-4.6, Opus-4.8, GPT-5.5, DeepSeek-V4-Pro, Kimi-K2.6; default decoding;
  the transport of the replication.
- Parsing, fixed in advance and state-independent: the last 'Answer: <number>' of a reply;
  otherwise a reply that is a bare number; anything else, or a number outside 1..N, is an invalid
  decision and counts as incorrect.
- Primary (24 statements: 2 pairs x 2 tasks x 6 models; alpha = 0.05/24 each, simultaneous by
  Bonferroni): the one-sided Clopper-Pearson lower bound L on own-source accuracy; verified when
  L > cap; reported with max(0, L - cap) as the lower bound on delta(E_other, E_own). A pair is
  certified incomparable for a model when both of its statements are verified. Coverage assumes
  i.i.d. state draws with replacement, a fixed rule (same model, prompt template and default
  decoding) and no backend drift during the run (the paper's Assumption 2).
- Rejection thresholds at n = 40 (not power figures): at least 13 correct for cap 1/8 and 23 for
  cap 1/3; L(40/40) = 0.857.
- Sensitivity: missing own-source outcomes counted as incorrect over all scheduled blocks.
- Diagnostics, with their own error budget (0.05/48, one-sided): other-source and no-context
  accuracy whose lower bound exceeds the cap is flagged. A flag is evidence against the combined
  assumptions (a parser or analysis defect, side information, or a statistical false alarm), not a
  diagnosis of a text leak. Every flag is reported.
- Secondary: own minus other-source accuracy per task (block-difference Hoeffding bound,
  alpha = 0.05/24, complete blocks), a fixed-model comparison over the hidden states.
- Descriptive only, without simultaneous coverage: per-state accuracy (about five observations
  per state), choices without context, invalid replies.

## 5. Smoke run

n = 1 per cell (72 requests), development data excluded from every analysis, read only for defects
(rendering, parsing, transport). Any change it prompts is listed here before the freeze.

Smoke result (5 October, `results/package2/smoke_labels`, read before the freeze): 72 of 72 replies
received, no transport failure; all 24 own-source replies valid. Five Kimi-K2.6 replies, all in
no-context or other-source arms, reached the output limit with no visible text; under Section 4 they
are invalid decisions and count as incorrect. No change was made: the primary uses own-source replies
only, and invalid replies in the diagnostic arms are reported with their count.

## 6. Reporting

Every result is reported, including unfavourable ones and diagnostic flags; no outcome is discarded
after inspection. The statements are statistical, with the stated simultaneous confidence and
structural assumptions; the deterministic proof of incomparability remains the finite-family
no-garbling argument.
