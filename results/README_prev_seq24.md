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

## incomparability corpus — `prev_seq24_incomparability.json`

* Part 1 (2026-09-08 05:56 → 10:06, the same pre-fix driver): none block and rounds 1–3 complete (1/21 pairs
  verified at n = 12); round 4 lost 45 of 84 draws to the next usage-limit window and the driver hung in its
  redraw passes (200 s timeouts, orphaned CLI processes), so it was killed at 10:06. Rounds 1–3 plus the scored
  round-4 draws were reconstructed from the transcripts (`prev_seq24_incomparability.transcripts.part1.jsonl.gz`,
  checksum `[0, 0, 1]`) into `prev_seq24_incomparability.resume.json`.
* Part 2: `prevalence_seq --resume` with the fixed driver tops every active cell up to n = 16 and continues
  rounds 5–6 under the same rule (the confidence sequence is anytime-valid, so any continuation pattern is
  admissible); the JSON records `resumed_from` and the driver log is appended to
  `prev_seq24_incomparability.log`.

Raw transcript directories stay local (`results/raw_transcripts/`, git-ignored): they carry the user's tool
and environment listings. Everything the reconstruction consumes is in the committed extracts.
