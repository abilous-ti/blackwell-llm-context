# prev_seq24 — sequential prevalence probe at n_max = 24 (harness + incomparability corpora)

Driver: `harness/prevalence_seq.py` — two-stage rule (anytime-valid beta-mixture confidence sequence at α/2
in flight, Clopper–Pearson at α/2 at n_max; rounds of 4; pair-hopeless futility from n = 8), model
`claude-haiku-4-5-20251001`, single-shot, 2 workers. Both runs were launched 2026-09-07 16:40 as one chained job.

## harness corpus — `prev_seq24_harness.json` (reconstructed, validated)

* Run 2026-09-07 16:45 → 2026-09-08 05:56. All six rounds completed and the summary was printed; the driver
  then crashed at its final `json.dumps` (outage bookkeeping keyed by tuples; fixed in c7cb5c8, which also adds
  per-round checkpoints). The in-memory counts were lost with the process.
* Counts were rebuilt from the per-call Claude CLI session transcripts by
  `harness/diag/reconstruct_seq_from_transcripts.py`: the same reply text → the same `_extract_code` → the same
  deterministic `verify_in`. Validation against the run log (`prev_seq24_harness.log`): none-baseline, the
  per-round verified-pair counts `[0, 0, 1, 3, 3, 4]`, the final tallies (5 INCOMPARABLE / 31 unresolved;
  sign patterns 10 no-evidence / 21 one-way / 5 incomparable; co-retrieved 1 / 11 / 2) and the driver-level
  call count (1494 = one temp dir per call) all reproduce the log exactly.
* Session classification (2140 CLI sessions inside 1494 driver calls): 1178 scored; 950 synthetic error
  replies (934 "session limit — resets 3:50am" from the account's usage window ≈00:20–03:50, 16 connection
  errors ≈17:20); 10 tool-using replies that the CLI aborted at max-turns 1 and the driver retried; 2 replies
  that arrived after the 200 s driver timeout. Two manual diagnostic calls made while the run was in flight
  (22:53–22:58) were removed before reconstruction. The five-hour gap 17:24–22:24 with no sessions at all is a
  machine sleep / disconnect, not an API event.
* Outage accounting: in round 3 (n = 8 → 12) 88 draws over 22 cells hit the usage-limit window; three redraw
  passes recovered 42 (the passes that ran after 03:50); 46 draws in 12 cells stayed unscored, so those cells
  end at n = 20 (one at 22). Driver calls 1494 = 1178 scored + 316 failed attempts. Spend $32.93 is the
  CLI-reported total from the log (token-based estimate $26.85).
* The redacted extract `prev_seq24_harness.transcripts.jsonl.gz` (cell, timing, status, token usage, reply
  text — no paths or environment) reproduces the JSON exactly:

      python harness/diag/reconstruct_seq_from_transcripts.py --transcripts results/prev_seq24_harness.transcripts.jsonl.gz \
        --corpus harness --calls-from-log 1494 --spend-from-log 32.93 --redrawn-from-log 316 --expect-rounds 0,0,1,3,3,4 --out <file>

* Like-for-like with the fixed-n probe on the same corpus (`prevalence_haiku_n16_v2.merged.json`, n = 16):
  36/36 pair verdicts agree (the same 5 incomparable pairs), identical sign patterns
  (`harness/prevalence_compare.py`).
* Cost, stated honestly: 1178 scored draws against 1440 for a fixed-n = 24 grid (1.22×), but **no cell was ever
  stopped early** (45 active cells in every round). The saving is the protocol's leaky-task screen (the none arm
  runs first; the 9 × 24 candidate draws on the leaky task are never drawn) plus the 46 unscored draws.
  Sequential stopping itself saved nothing on this grid — exactly what the separation-point analysis predicted
  (n* ≈ 12 at these α; zero cells must run to n_max). The C1 savings are real only in the n ≈ 40 verification
  regime with few pairs.

## incomparability corpus — `prev_seq24_incomparability.json` (complete; a three-part run)

* Part 1 (2026-09-08 05:56 → 10:06, the pre-fix driver): none block and rounds 1–3 complete (1/21 verified at
  n = 12); round 4 lost 45 of 84 draws to the account's next usage-limit window ("resets 8:50am") and the driver
  hung in its redraw passes (200 s timeouts, orphaned CLI processes), so it was killed at 10:06. Reconstructed
  from the transcripts (checksum `[0, 0, 1]`) into `prev_seq24_incomparability.resume.json`.
* Part 2 (10:13 → 10:40, fixed driver, `--resume`): topped the three short cells up to n = 16 (6 calls); the
  round-4 check verified 2/21; round 5 then hit the account's WEEKLY limit ("resets Sep 9, 6pm", 33 synthetic
  replies) and the run was stopped at 10:40 to protect the quota. Reconstructed (checksum `[0, 0, 1, 2]`) into
  `prev_seq24_incomparability.resume2.json`; its per-cell counts at n = 16 agree with the driver's own checkpoint
  on all 40 cells.
* Part 3 (11:15 → 11:33, after the reset, `--resume` from resume2): 3 top-up calls to n = 20, round 6 (84 calls),
  stage 2; 0 outage draws; the driver wrote the JSON itself (`resumed_from` recorded). The confidence sequence is
  anytime-valid, so the two pauses do not affect validity.
* Cross-validation of the reconstruction method on a run whose ground truth exists: rebuilding the whole run
  from `prev_seq24_incomparability.transcripts.jsonl.gz` (953 sessions in 733 driver calls) reproduces the
  driver's JSON — per-round checksums `[0, 0, 1, 2, 2, 2]`, every pair row (verdict, pattern, L values, n at
  verdict) and the counts of every drawn cell are identical.
* Results: D_clean = 3 (t_cpx 75 % and t_code 79 % leaky), K = 7, 21 pairs (10 co-retrieved). Verified
  incomparable 2/21: hat_delta vs required_n_dominance (stage 1, n = 12) and hat_delta vs
  required_n_incomparability (stage 1, n = 16) — decisive chunks for different tasks. Sign patterns
  7 no-evidence / 12 one-way / 2 incomparable; co-retrieved 6 / 4 / 0. The sibling pair required_n_dominance vs
  required_n_incomparability is "no evidence" for the right reason: each docstring also solves the other's task
  (16/24 and 19/24), so neither beats the other — an overlap, not an incomparability. The four helper chunks
  (clopper_pearson, extract_code, scalar_table, verify_in) solve nothing (≤ 2/24) and lose one-way to every
  decisive chunk.
* Cost, stated honestly: 624 scored draws vs 960 for a fixed-n = 24 grid (1.54×), all of it the leaky-task screen
  (7 × 2 × 24 candidate draws on the two leaky tasks never drawn); no cell stopped early (21 active in every
  round). Driver calls 733 = 624 scored + 109 failed attempts; spend ≈ $14 (token-based estimate $13.49; the
  JSON's $13.96 mixes the checkpoint's estimate with the CLI-reported cost of part 3).

## Across the three private corpora

| corpus | rule | pairs verified incomparable | co-retrieved | early cell stops |
|---|---|---|---|---|
| harness (seq24, this file) | two-stage, n_max 24 | 5/36 | 2/14 | none |
| tokenguard (`prev_seq_tokenguard.json`) | two-stage, n_max 16, old zero-cell futility | 9/28 | 0/12 | futility only |
| incomparability (seq24, this file) | two-stage, n_max 24 | 2/21 | 0/10 | none |

16/85 pairs (19 %) verified incomparable overall, 2/36 (6 %) among co-retrieved pairs. In every corpus the
verified pairs are pairs of decisive chunks for different tasks, and same-module siblings that cover each
other's coordinate come out nested or no-evidence — the structure the theory predicts, on natural text with
retrieval-selected candidates. Sequential stopping never fired on a prevalence grid; its savings belong to the
n ≈ 40 verification regime.

Raw transcript directories stay local (`results/raw_transcripts/`, git-ignored): they carry the user's tool
and environment listings. Everything the reconstruction consumes is in the committed extracts.
