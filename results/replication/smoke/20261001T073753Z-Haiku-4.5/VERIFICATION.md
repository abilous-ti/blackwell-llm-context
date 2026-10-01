# Live verification: claude-haiku-4-5, 16 requests

- every scheduled request was issued and received: yes
- no transport failure: yes
- every received response was graded: yes
- the provider returned a model field on every response: yes
- response id, usage and stop reason kept on every response: yes
- analysis is final (window closed, freeze holds, records match the design): yes
- calls used within the budget: yes

HTTP statuses of all attempts: {200: 16}
Model field returned: {'claude-haiku-4-5-20251001': 16} (requested claude-haiku-4-5)
Stop reasons: {'end_turn': 16}
Response fields kept: container, content, diagnostics, id, model, role, stop_details, stop_reason, stop_sequence, type, usage
Backend fingerprint: not sent by the provider
Endpoint as recorded: 2701afc737.services.ai.azure.com
Latency per request (s): median 3.6, max 6.8
Tokens: 3994 input, 5012 output (313 output per request)
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
| enc_amount | W2 | 1/2 | 1/2 |

Records, schedule, freeze and analysis: results/replication/smoke/20261001T073753Z-Haiku-4.5
This check is not part of the replication and never enters its analysis.
