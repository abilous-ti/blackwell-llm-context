# Live verification: claude-sonnet-4-6, 16 requests

- every scheduled request was issued and received: yes
- no transport failure: yes
- every received response was graded: yes
- the provider returned a model field on every response: yes
- response id, usage and stop reason kept on every response: yes
- analysis is final (window closed, freeze holds, records match the design): yes
- calls used within the budget: yes

HTTP statuses of all attempts: {200: 16}
Model field returned: {'claude-sonnet-4-6': 16} (requested claude-sonnet-4-6)
Stop reasons: {'end_turn': 16}
Response fields kept: container, content, diagnostics, id, model, role, stop_details, stop_reason, stop_sequence, type, usage
Backend fingerprint: not sent by the provider
Endpoint as recorded: 2701afc737.services.ai.azure.com
Latency per request (s): median 3.4, max 10.7
Tokens: 3994 input, 2533 output (158 output per request)
Calls used: 16 of 48
Graders agree on 16 of 16 graded replies

| Task | Condition | PASS (published grader) | PASS (current grader) |
|---|---|---|---|
| api_argorder | W1 | 2/2 | 2/2 |
| api_argorder | W1plus | 0/2 | 0/2 |
| api_argorder | none | 0/2 | 0/2 |
| api_post_ok | W1 | 2/2 | 2/2 |
| api_post_ok | W1plus | 0/2 | 0/2 |
| api_post_ok | W2 | 0/2 | 0/2 |
| enc_amount | W1 | 0/2 | 0/2 |
| enc_amount | W2 | 2/2 | 2/2 |

Records, schedule, freeze and analysis: results/replication/smoke/20261001T073844Z-Sonnet-4.6
This check is not part of the replication and never enters its analysis.
