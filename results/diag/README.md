# Raw-failure audit (Haiku-4.5, single-shot)

Diagnostic re-runs that **retain every raw completion, the extracted code, and the verifier's
stderr**, made to classify the failures behind the anomalous `api_post_ok` cell (W1 at ~52% while
the harder `api_argorder` cell sits at 100% under the same source). The published runs do not keep
raw outputs, so these are separate draws, not a re-scoring.

| File | Cell | n | Result |
|---|---|---|---|
| `api_post_ok_W1_diag.json` | api_post_ok / W1 | 12 | 5 PASS; all 7 failures = correct kw-only contract call, missing `import ledger` |
| `api_argorder_W1_diag.json` | api_argorder / W1 (control) | 8 | 8 PASS; `import ledger` present in 8/8 |
| `api_post_ok_W1plus_diag.json` | api_post_ok / W1+ | 8 | 2 PASS; 2 import-only slips; 4 genuine interference (amount wire-encoded per W2, e.g. `'+500#5'` for 500) |

Fields per draw: `raw` (model reply), `code` (what the verifier ran), `stderr_tail`, `pass`,
`class`, `fenced`, `starts_with_prose`, `out_tokens`, `cost`.

Produced by `harness/diag/haiku_diag.py` (same prompt, arm text, extractor and verifier as the
published harness). `haiku_ctrl.py` is the import-neutralized control for this cell and
`cell_rerun.py` the clean single-cell re-measurement used to replace outage-mixed cells.
