requests: scheduled 3840, received 3840, graded 3840, transport failures 0

PRIMARY: harm under the clarified contract, PASS(AcB) - PASS(Ac) (CP, two-sided, alpha = 0.05/24)
  Haiku-4.5        api_post_ok   A 40/40 AB  0/40 Ac 40/40 AcB 33/40  H_c -0.18 [-0.43, +0.14]  inconclusive
  Haiku-4.5        api_argorder  A 31/40 AB  0/40 Ac 37/40 AcB 37/40  H_c +0.00 [-0.30, +0.30]  no harm beyond the margin
  Haiku-4.5        cache_put_ok  A 38/40 AB  0/40 Ac 39/40 AcB 40/40  H_c +0.03 [-0.17, +0.22]  no harm beyond the margin
  Haiku-4.5        inv_book      A 39/40 AB 33/40 Ac 40/40 AcB  0/40  H_c -1.00 [-1.00, -0.66]  harm persists beyond the margin
  Sonnet-4.6       api_post_ok   A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  Sonnet-4.6       api_argorder  A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  Sonnet-4.6       cache_put_ok  A 40/40 AB  0/40 Ac 40/40 AcB  1/40  H_c -0.97 [-1.00, -0.60]  harm persists beyond the margin
  Sonnet-4.6       inv_book      A 40/40 AB  0/40 Ac 40/40 AcB  0/40  H_c -1.00 [-1.00, -0.66]  harm persists beyond the margin
  Opus-4.8         api_post_ok   A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  Opus-4.8         api_argorder  A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  Opus-4.8         cache_put_ok  A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  Opus-4.8         inv_book      A 40/40 AB  1/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  GPT-5.5          api_post_ok   A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  GPT-5.5          api_argorder  A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  GPT-5.5          cache_put_ok  A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  GPT-5.5          inv_book      A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  DeepSeek-V4-Pro  api_post_ok   A 29/40 AB  0/40 Ac 22/40 AcB 21/40  H_c -0.03 [-0.52, +0.48]  inconclusive
  DeepSeek-V4-Pro  api_argorder  A 25/40 AB  4/40 Ac 31/40 AcB 32/40  H_c +0.03 [-0.40, +0.44]  inconclusive
  DeepSeek-V4-Pro  cache_put_ok  A 26/40 AB  5/40 Ac 27/40 AcB 28/40  H_c +0.02 [-0.45, +0.49]  inconclusive
  DeepSeek-V4-Pro  inv_book      A 11/40 AB  2/40 Ac  6/40 AcB 19/40  H_c +0.32 [-0.17, +0.71]  no harm beyond the margin
  Kimi-K2.6        api_post_ok   A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  Kimi-K2.6        api_argorder  A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  Kimi-K2.6        cache_put_ok  A 40/40 AB  0/40 Ac 40/40 AcB 40/40  H_c +0.00 [-0.17, +0.17]  no harm beyond the margin
  Kimi-K2.6        inv_book      A 40/40 AB  0/40 Ac 40/40 AcB 34/40  H_c -0.15 [-0.40, +0.15]  inconclusive
readings: harm persists beyond the margin 3; inconclusive 5; no harm beyond the margin 16

SECONDARY: H_o = PASS(AB) - PASS(A); C = PASS(Ac) - PASS(A) (CP); D = H_c - H_o (block Hoeffding)
  Haiku-4.5        api_post_ok   H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +0.82 [-0.35, +2.00] (B=40)
  Haiku-4.5        api_argorder  H_o -0.78 [-0.94, -0.34]  C +0.15 [-0.24, +0.49]  D +0.78 [-0.40, +1.95] (B=40)
  Haiku-4.5        cache_put_ok  H_o -0.95 [-1.00, -0.56]  C +0.03 [-0.22, +0.27]  D +0.97 [-0.20, +2.15] (B=40)
  Haiku-4.5        inv_book      H_o -0.15 [-0.43, +0.19]  C +0.03 [-0.17, +0.22]  D -0.85 [-2.02, +0.32] (B=40)
  Sonnet-4.6       api_post_ok   H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  Sonnet-4.6       api_argorder  H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  Sonnet-4.6       cache_put_ok  H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +0.03 [-1.15, +1.20] (B=40)
  Sonnet-4.6       inv_book      H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +0.00 [-1.17, +1.17] (B=40)
  Opus-4.8         api_post_ok   H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  Opus-4.8         api_argorder  H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  Opus-4.8         cache_put_ok  H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  Opus-4.8         inv_book      H_o -0.97 [-1.00, -0.60]  C +0.00 [-0.17, +0.17]  D +0.97 [-0.20, +2.15] (B=40)
  GPT-5.5          api_post_ok   H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  GPT-5.5          api_argorder  H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  GPT-5.5          cache_put_ok  H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  GPT-5.5          inv_book      H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  DeepSeek-V4-Pro  api_post_ok   H_o -0.72 [-0.91, -0.28]  C -0.17 [-0.62, +0.34]  D +0.70 [-0.47, +1.87] (B=40)
  DeepSeek-V4-Pro  api_argorder  H_o -0.53 [-0.84, -0.02]  C +0.15 [-0.34, +0.58]  D +0.55 [-0.62, +1.72] (B=40)
  DeepSeek-V4-Pro  cache_put_ok  H_o -0.53 [-0.85, -0.01]  C +0.03 [-0.46, +0.50]  D +0.55 [-0.62, +1.72] (B=40)
  DeepSeek-V4-Pro  inv_book      H_o -0.23 [-0.54, +0.18]  C -0.13 [-0.52, +0.31]  D +0.55 [-0.62, +1.72] (B=40)
  Kimi-K2.6        api_post_ok   H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  Kimi-K2.6        api_argorder  H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  Kimi-K2.6        cache_put_ok  H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +1.00 [-0.17, +2.17] (B=40)
  Kimi-K2.6        inv_book      H_o -1.00 [-1.00, -0.66]  C +0.00 [-0.17, +0.17]  D +0.85 [-0.32, +2.02] (B=40)

DESCRIPTIVE: failing superset replies applying the other source's transformation (hit/fail)
  api_post_ok|AB         240/240
  api_post_ok|AcB        0/26
  api_argorder|AB        235/236
  api_argorder|AcB       0/11
  cache_put_ok|AB        235/235
  cache_put_ok|AcB       45/51
  inv_book|AB            204/204
  inv_book|AcB           95/107
