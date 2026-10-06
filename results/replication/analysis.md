# Replication analysis: FINAL

11520 scheduled requests: 11516 graded, 0 ungraded, 0 failed, 4 interrupted, 0 not collected, 0 pending. Windows: d1-pm closed, d2-am closed, d2-pm closed, d3-am closed, d3-pm closed, d4-am closed. Calls used: 11547 of 12288. Graders agree on 11515 of 11516 graded draws.

| Model | Contrast | Blocks | Estimate | Primary bound | Verified | Worst case | Windows missing | Window range | Heterogeneity p |
|---|---|---|---|---|---|---|---|---|---|
| Haiku-4.5 | A1 | 240 | +0.992 | +0.765 | yes | yes (+0.765) | none | +0.97 to +1.00 | 0.545 |
| Haiku-4.5 | A2 | 240 | +0.763 | +0.536 | yes | yes (+0.536) | none | +0.65 to +0.85 | 0.395 |
| Haiku-4.5 | H1 | 240 | -0.992 | -0.765 | any yes, margin yes | any yes, margin yes (-0.765) | none | -1.00 to -0.97 | 0.545 |
| Haiku-4.5 | H2 | 240 | -0.846 | -0.619 | any yes, margin yes | any yes, margin yes (-0.619) | none | -0.88 to -0.78 | 0.782 |
| Sonnet-4.6 | A1 | 240 | +1.000 | +0.773 | yes | yes (+0.773) | none | +1.00 to +1.00 | 1.000 |
| Sonnet-4.6 | A2 | 240 | +1.000 | +0.773 | yes | yes (+0.773) | none | +1.00 to +1.00 | 1.000 |
| Sonnet-4.6 | H1 | 240 | -1.000 | -0.773 | any yes, margin yes | any yes, margin yes (-0.773) | none | -1.00 to -1.00 | 1.000 |
| Sonnet-4.6 | H2 | 240 | -1.000 | -0.773 | any yes, margin yes | any yes, margin yes (-0.773) | none | -1.00 to -1.00 | 1.000 |
| Opus-4.8 | A1 | 240 | +1.000 | +0.773 | yes | yes (+0.773) | none | +1.00 to +1.00 | 1.000 |
| Opus-4.8 | A2 | 240 | +1.000 | +0.773 | yes | yes (+0.773) | none | +1.00 to +1.00 | 1.000 |
| Opus-4.8 | H1 | 240 | -1.000 | -0.773 | any yes, margin yes | any yes, margin yes (-0.773) | none | -1.00 to -1.00 | 1.000 |
| Opus-4.8 | H2 | 240 | -1.000 | -0.773 | any yes, margin yes | any yes, margin yes (-0.773) | none | -1.00 to -1.00 | 1.000 |
| GPT-5.5 | A1 | 240 | +1.000 | +0.773 | yes | yes (+0.773) | none | +1.00 to +1.00 | 1.000 |
| GPT-5.5 | A2 | 238 | +0.992 | +0.764 | yes | yes (+0.757) | none | +0.97 to +1.00 | 0.552 |
| GPT-5.5 | H1 | 240 | -1.000 | -0.773 | any yes, margin yes | any yes, margin yes (-0.773) | none | -1.00 to -1.00 | 1.000 |
| GPT-5.5 | H2 | 240 | -1.000 | -0.773 | any yes, margin yes | any yes, margin yes (-0.773) | none | -1.00 to -1.00 | 1.000 |
| DeepSeek-V4-Pro | A1 | 240 | +0.758 | +0.532 | yes | yes (+0.532) | none | +0.68 to +0.85 | 0.289 |
| DeepSeek-V4-Pro | A2 | 240 | +0.767 | +0.540 | yes | yes (+0.540) | none | +0.70 to +0.88 | 0.576 |
| DeepSeek-V4-Pro | H1 | 240 | -0.754 | -0.527 | any yes, margin yes | any yes, margin yes (-0.527) | none | -0.85 to -0.68 | 0.277 |
| DeepSeek-V4-Pro | H2 | 240 | -0.454 | -0.227 | any yes, margin no | any yes, margin no (-0.227) | none | -0.57 to -0.33 | 0.795 |
| Kimi-K2.6 | A1 | 240 | +1.000 | +0.773 | yes | yes (+0.773) | none | +1.00 to +1.00 | 1.000 |
| Kimi-K2.6 | A2 | 239 | +0.946 | +0.718 | yes | yes (+0.715) | none | +0.92 to +0.97 | 0.791 |
| Kimi-K2.6 | H1 | 240 | -1.000 | -0.773 | any yes, margin yes | any yes, margin yes (-0.773) | none | -1.00 to -1.00 | 1.000 |
| Kimi-K2.6 | H2 | 239 | -1.000 | -0.773 | any yes, margin yes | any yes, margin yes (-0.769) | none | -1.00 to -1.00 | 1.000 |

PASS incomparability (A1 and A2 both verified): Haiku-4.5 yes, Sonnet-4.6 yes, Opus-4.8 yes, GPT-5.5 yes, DeepSeek-V4-Pro yes, Kimi-K2.6 yes
