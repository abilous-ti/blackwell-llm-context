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
| `haiku`, `sonnet`, `opus` | Anthropic CLI, single-shot | same regime as the paper |
| `deepseek`, `kimi` | Azure chat completions | same regime as the paper |
| `gpt55-codex` | Codex CLI (`--model gpt-5.5`) | **agentic**, not the paper's single-shot Azure regime; no GPT deployment was available |
| `gpt-6-astra-codex` | Codex CLI default model | **not in the paper roster**; generality evidence only |
| `gpt54mini-codex` | Codex CLI (`--model gpt-5.4-mini`) | **not in the paper roster**; generality evidence only |

Draws recorded after the harness fix carry `model_requested` / `model_served`; earlier
ones do not, and their identity was confirmed by direct probe (the Anthropic CLI reports
the served model in `modelUsage`).

Credentials were read from the environment and are not stored here.
