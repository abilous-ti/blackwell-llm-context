# Retention re-measurement of the interference cells

Fresh draws (`n=40` per arm) of every verified interference cell, with **raw completions
retained**, made because the published harness discards them. Produced by
`harness/diag/audit_any.py`.

Each draw is scored twice: under the published verifier and under the import-neutralized
one, and carries the packaging signals (`fenced`, `starts_with_prose`, `code_empty`,
`call_present`) plus `has_import` / `encoded_amount`.

These are new draws months after the original runs, not a re-scoring. They test whether
the phenomenon reproduces, not whether the published proportions replicate exactly.

## Labels

| Label | Backend | Note |
|---|---|---|
| `haiku`, `sonnet`, `opus` | Anthropic CLI, single-shot | superseded command-line regime; the paper's Anthropic rows are read from the HTTP runs with retention in `results/retain_api/`, and these files enter only the drift comparison |
| `deepseek`, `kimi` | Azure chat completions | same HTTP regime as the paper; fresh draws used for the drift comparison, not for any published number |
| `gpt55` | Azure Responses (`gpt-5.5`), `kind: azure` | same HTTP regime as the paper; the source of the published GPT-5.5 `trap_store_wire` cells (both arms) and of the eight-entry reproduction check in the paper's Appendix D |
| `gpt55-codex` | Codex CLI (`--model gpt-5.5`) | **agentic**, not the paper's single-shot Azure regime; recorded before a GPT deployment was available; not used by the paper |
| `gpt-6-astra-codex` | Codex CLI default model | **not in the paper roster**; generality evidence only |
| `gpt54mini-codex` | Codex CLI (`--model gpt-5.4-mini`) | **not in the paper roster**; generality evidence only |

Draws recorded after the harness fix carry `model_requested` / `model_served`; earlier
ones do not, and their identity was confirmed by direct probe (the Anthropic CLI reports
the served model in `modelUsage`).

Credentials were read from the environment and are not stored here.
