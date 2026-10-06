# Declarative label experiment: amendment 1 (analysis only)

Written 5 October 2026, about 20:45 Kyiv, after confirmatory collection had started (643 replies
received at 20:44) and BEFORE any confirmatory outcome was viewed: up to the recording of this
amendment only the numbers of issued and received lines had been counted; no grade, choice or
reply text of the confirmatory run had been read. The amendment follows an external methodological
review received at that time. It changes the analysis only; data collection, prompts, parsing,
grading and the schedule are unchanged. The frozen files (`FREEZE_labels.json`, frozen 17:41:31 UTC)
are not edited; this file and `analyze_labels_amended.py` are hashed in
`FREEZE_labels_amendment.json` before any outcome is viewed. Both changes are conservative: they can
only make a statement harder to verify. The frozen analysis (`analyze_labels.py`) is still run and
reported unchanged.

## A1. Missing outcomes in the primary analysis

The primary statement of PROTOCOL_LABELS.md Section 4 now uses every scheduled own-source block in
the denominator (n = 40 per cell): a missing outcome (transport failure, halted lane, or a request
never issued) counts as incorrect, as an invalid decision already does. The one-sided
Clopper-Pearson bound, alpha = 0.05/24 per statement, the caps and the decision rule (L > cap) are
otherwise unchanged. The complete-case bound of Section 4 becomes a sensitivity analysis.

## A2. Analysis robust to drift (pre-specified before outcomes were viewed)

Clopper-Pearson coverage assumes a fixed rule and identically distributed outcomes. If the backend
drifts, block i is answered by some rule M_i, fixed during its call, with success probability q_i
over the random state. Each M_i is a rule that uses the own source, so the randomization argument
gives delta(E_other, E_own) >= q_i - c for every i, hence delta(E_other, E_own) >= qbar - c, with
qbar the mean of the q_i. For independent outcomes with possibly unequal success probabilities,
Hoeffding's inequality gives the lower confidence bound

  L_H = k/n - sqrt(ln(1/alpha) / (2n)),   alpha = 0.05/24,   n = scheduled blocks (missing = incorrect),

with P(qbar < L_H) <= alpha. Each primary decision is reported as drift-robust when L_H > c, with
max(0, L_H - c) as the corresponding lower bound on directional deficiency. Rejection thresholds at
n = 40: at least 17 correct for cap 1/8 and 25 for cap 1/3 (Clopper-Pearson: 13 and 23);
L_H(40/40) = 0.722.

## Power (computed at the time of the amendment; informative only)

Probability of verification at n = 40 for true own-source accuracies 0.6 / 0.8 / 0.95: cap 1/8,
Clopper-Pearson 1.000 / 1.000 / 1.000 and Hoeffding 0.992 / 1.000 / 1.000; cap 1/3,
Clopper-Pearson 0.689 / 1.000 / 1.000 and Hoeffding 0.440 / 0.997 / 1.000.

## Reporting

The results table reports, per pair, task and model: k of 40, the amended primary bound (A1), the
drift-robust bound (A2), the complete-case bound (sensitivity) and the diagnostics of Section 4. A
pair is certified incomparable for a model when both of its amended primary statements are
verified; the paper states whether that holds under A2 as well. All results are published,
including unverified directions.
