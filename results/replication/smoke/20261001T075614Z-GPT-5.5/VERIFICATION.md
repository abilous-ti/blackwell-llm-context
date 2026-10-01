# Live verification: gpt-5.5, 16 requests

- every scheduled request was issued and received: yes
- no transport failure: yes
- every received response was graded: yes
- the provider returned a model field on every response: yes
- response id, usage and stop reason kept on every response: yes
- analysis is final (window closed, freeze holds, records match the design): yes
- calls used within the budget: yes

HTTP statuses of all attempts: {200: 16}
Model field returned: {'gpt-5.5': 16} (requested gpt-5.5)
Stop reasons: {'completed': 16}
Response fields kept: background, completed_at, content_filters, created_at, error, frequency_penalty, id, incomplete_details, instructions, max_output_tokens, max_tool_calls, metadata, model, moderation, object, output, parallel_tool_calls, presence_penalty, previous_response_id, prompt_cache_key, prompt_cache_retention, reasoning, safety_identifier, service_tier, status, store, temperature, text, tool_choice, tool_usage, tools, top_logprobs, top_p, truncation, usage, user
Backend fingerprint: not sent by the provider
Endpoint as recorded: f342d6ed59.services.ai.azure.com
Latency per request (s): median 7.2, max 80.3
Tokens: 3564 input, 15492 output (968 output per request)
Calls used: 16 of 48
Graders agree on 16 of 16 graded replies

| Task | Condition | PASS (published grader) | PASS (current grader) |
|---|---|---|---|
| api_argorder | W1 | 2/2 | 2/2 |
| api_argorder | W1plus | 0/2 | 0/2 |
| api_argorder | none | 2/2 | 2/2 |
| api_post_ok | W1 | 2/2 | 2/2 |
| api_post_ok | W1plus | 0/2 | 0/2 |
| api_post_ok | W2 | 0/2 | 0/2 |
| enc_amount | W1 | 0/2 | 0/2 |
| enc_amount | W2 | 2/2 | 2/2 |

Records, schedule, freeze and analysis: results/replication/smoke/20261001T075614Z-GPT-5.5
This check is not part of the replication and never enters its analysis.
