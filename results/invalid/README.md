# Invalid runs (kept for the record, never to be cited)

## prevalence_haiku_n16_run1_quotebug.{json,log}  (2026-09-06, $9.10)
39 of 60 cells are dead (0/16 with ERR, zero cost). Root cause: the chunk wrapper enclosed each
docstring in triple quotes; on Windows `claude_cmd` runs `cmd.exe /c claude.cmd ...`, and cmd.exe
toggles its quote state on every `"` (ignoring backslash escapes), after which any `< > |` in the
prompt act as redirections and the CLI receives a mangled prompt. Every chunk containing `< > |`
after the quotes died; chunks without them survived. Confirmed by re-running a dead cell with the
special characters neutralized (executes) and with the fixed quote-free format (executes).
The 21 live cells are real but were produced under a different prompt format from the fix, so
the whole probe was re-run uniformly as prevalence_haiku_n16_v2.
