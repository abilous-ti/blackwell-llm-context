# Live verification: Kimi-K2.6, 16 requests

- every scheduled request was issued and received: yes
- no transport failure: yes
- every received response was graded: yes
- the provider returned a model field on every response: yes
- response id, usage and stop reason kept on every response: yes
- analysis is final (window closed, freeze holds, records match the design): yes
- calls used within the budget: yes

HTTP statuses of all attempts: {200: 16}
Model field returned: {'Kimi-K2.6': 16} (requested Kimi-K2.6)
Stop reasons: {'stop': 14, 'length': 2}
Response fields kept: choices, created, id, model, object, prompt_filter_results, usage
Backend fingerprint: not sent by the provider
Endpoint as recorded: f342d6ed59.services.ai.azure.com
Latency per request (s): median 9.3, max 72.4
Tokens: 3582 input, 43911 output (2744 output per request)
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

Records, schedule, freeze and analysis: results/replication/smoke/20261001T075903Z-Kimi-K2.6
This check is not part of the replication and never enters its analysis.
