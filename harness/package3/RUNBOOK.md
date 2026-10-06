# Package 3 runbook: listwise reranking on HotpotQA's retrieved candidates (fullwiki)

These are the commands the authors run, in order, in their own terminal, from the repository root
(`C:\Users\AndriyBilous\Documents\GitHub\blackwell-llm-context`). `python` is the main Python 3.11.
These steps use the standard library only.

**Keys.** Set the same environment variables as for package 2's run, in that terminal only:

- `BW_ENDPOINT_HAIKU`, `BW_KEY_HAIKU`
- `BW_ENDPOINT_GPT55`, `BW_KEY_GPT55`
- `BW_ENDPOINT_DEEPSEEK`, `BW_KEY_DEEPSEEK`

No script prints, logs or stores them.

**Already done before the freeze; do not repeat (each step is refused after the freeze):** the
download and its check, the sample and items, the local rankings, the mock pipeline and the freeze
itself.

## 1. Verify the freeze

```
python harness/package3/freeze_fullwiki.py --verify
```

Expected: `freeze <time>: verified, nothing changed (18 files; ...)`. If any frozen file has
changed, the confirmatory run is refused.

Optional read-only audits, which write nothing:

- `python harness/package3/fullwiki_data.py --check` checks the download (size, SHA-256 and the
  `SHA256SUMS.txt` line).
- `python harness/package3/fullwiki_data.py --verify-draw` recomputes the sample in memory and
  compares it with the frozen items (takes about a minute).

## 2. Pre-flight check (no request is sent)

```
python harness/package3/run_fullwiki.py --confirm --dry-run
```

Expected output:

- freeze verified;
- at least 300 MB free on the records' drive;
- `ranking requests to issue: 600 of 600`;
- `answer requests to issue: 6300 now, plus up to 900 RankGPT answers ... total planned 7800`;
- all six `BW_*` names listed under "set" (names only, never values).

## 3. Smoke run: 2 smoke questions, never confirmatory ones, 52 requests

```
python harness/package3/run_fullwiki.py --smoke 2
python harness/package3/analyze_fullwiki.py --smoke
```

The smoke run sends 4 ranking requests and then 48 answer requests (3 models x 8 conditions x 2
questions). In the summary, check:

- 0 transport failures;
- RankGPT complete parses 4/4;
- an `Answer:` line in the replies.

Records go to `natural_data/package3/smoke_fullwiki/` and enter no analysis.

## 4. Confirmatory run: 7,800 requests

```
python harness/package3/run_fullwiki.py --confirm
```

- Requests: 600 ranking requests (Haiku-4.5, 300 questions x 2 input orders), then up to 7,200
  answer requests (Haiku-4.5, GPT-5.5 and DeepSeek-V4-Pro x 8 conditions x 300 questions). A question
  whose o0 ranking fails in transport gets no RankGPT answers, 3 fewer requests each.
- Four lanes per model, as in package 2.
- Duration: package 2's 9,240 requests took about 4.5 hours with four lanes per model.
- Tokens, estimated from package 2's measured use: about 1.2 M input and 0.03 M output tokens for
  ranking; about 3 M input and 1-2 M output tokens for answers (GPT-5.5 reasons longest).
- Records: `natural_data/package3/confirm_fullwiki/records.jsonl`, about 25-30 MB.

## 5. Resuming after any stop

Run the same command again:

```
python harness/package3/run_fullwiki.py --confirm
```

- Requests already issued are skipped, and every saved reply is kept.
- A request that was in flight when the process died is counted as "interrupted": a missing
  observation, never sent again.
- **Ctrl+C** stops gracefully: each lane finishes its request in flight, saves the reply and stops.
- **Low disk:** with less than 100 MB free, every lane stops before its next request. Free space
  (a live run needs at least 300 MB to start) and rerun.
- **A halted lane** (three consecutive transport failures): check that model's endpoint and key,
  then rerun.
- **`run.lock exists`:** if no run is active (for example after a crash or a closed terminal),
  delete `natural_data/package3/confirm_fullwiki/run.lock` and rerun.
- **Progress at any time:** `python harness/package3/run_fullwiki.py --confirm --summary`

## 6. Analysis

```
python harness/package3/analyze_fullwiki.py
```

This verifies the freeze and writes `results/package3/analysis_fullwiki.json` and
`results/package3/analysis_fullwiki.md`. The output contains:

- the coverage table;
- the answers;
- the primary (15) and secondary (30) families;
- the evidence criterion;
- the worst-case sensitivity;
- RankGPT resource use;
- the verdict by the pre-declared reading rules (PROTOCOL_FULLWIKI.md, Section 7).

## Expected request totals

| Step | Ranking | Answers | Total |
|---|---|---|---|
| Smoke (`--smoke 2`) | 4 | 48 | 52 |
| Confirmatory | 600 | 7,200 | 7,800 |

## Do not

- Do not edit any frozen file: the confirmatory run is then refused.
- Do not rerun the `fullwiki_data.py` build (anything without `--check` or `--verify-draw`) or
  `run_fullwiki.py --phase local`; both are refused after the freeze anyway.
- Do not put mock or smoke records into `confirm_fullwiki/`.

## For reference: how the frozen inputs were produced (6 October 2026; do not repeat)

```
python harness/package3/fullwiki_data.py --check
python harness/package3/fullwiki_data.py
C:/Users/AndriyBilous/stv/Scripts/python.exe harness/package3/run_fullwiki.py --phase local
python harness/package3/run_fullwiki.py --mock
python harness/package3/analyze_fullwiki.py --mock
python harness/package3/freeze_fullwiki.py
```
