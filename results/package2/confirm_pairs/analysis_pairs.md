requests: scheduled 9120, received 9120, graded 9120, transport failures 0

PRIMARY: PASS incomparability (hardened checks; alpha = 0.05/36 per statement)
pair       model            A - B on A-task (B, est, bound) B - A on B-task (B, est, bound) incomparable
cache      Haiku-4.5         40 +0.97 +0.40 yes             40 +1.00 +0.43 yes            YES
cache      Sonnet-4.6        40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
cache      Opus-4.8          40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
cache      GPT-5.5           40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
cache      DeepSeek-V4-Pro   40 +0.57 +0.00 yes             40 +1.00 +0.43 yes            YES
cache      Kimi-K2.6         40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
inventory  Haiku-4.5         40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
inventory  Sonnet-4.6        40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
inventory  Opus-4.8          40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
inventory  GPT-5.5           40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
inventory  DeepSeek-V4-Pro   40 +0.28 -0.30 no              40 +1.00 +0.43 yes            no
inventory  Kimi-K2.6         40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
audit      Haiku-4.5         40 +0.53 -0.05 no              40 +0.97 +0.40 yes            no
audit      Sonnet-4.6        40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
audit      Opus-4.8          40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
audit      GPT-5.5           40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
audit      DeepSeek-V4-Pro   40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
audit      Kimi-K2.6         40 +1.00 +0.43 yes             40 +1.00 +0.43 yes            YES
pair-model combinations verified PASS-incomparable: 16 of 18
decisions unchanged under worst-case imputation: 18 of 18; under the published checks: 18 of 18

SECONDARY: augmentation (estimate, upper bound at alpha = 0.05/72, harm verified?)
  cache      Haiku-4.5        cache_put_ok   AB - A   B= 40 -0.97 -0.37 HARM
  cache      Haiku-4.5        cache_put_ok   BA - A   B= 40 -0.97 -0.37 HARM
  cache      Haiku-4.5        key_norm       AB - B   B= 40 +0.00 +0.60 
  cache      Haiku-4.5        key_norm       BA - B   B= 40 +0.00 +0.60 
  cache      Sonnet-4.6       cache_put_ok   AB - A   B= 40 -1.00 -0.40 HARM
  cache      Sonnet-4.6       cache_put_ok   BA - A   B= 40 -1.00 -0.40 HARM
  cache      Sonnet-4.6       key_norm       AB - B   B= 40 +0.00 +0.60 
  cache      Sonnet-4.6       key_norm       BA - B   B= 40 +0.00 +0.60 
  cache      Opus-4.8         cache_put_ok   AB - A   B= 40 -1.00 -0.40 HARM
  cache      Opus-4.8         cache_put_ok   BA - A   B= 40 -0.15 +0.45 
  cache      Opus-4.8         key_norm       AB - B   B= 40 +0.00 +0.60 
  cache      Opus-4.8         key_norm       BA - B   B= 40 +0.00 +0.60 
  cache      GPT-5.5          cache_put_ok   AB - A   B= 40 -1.00 -0.40 HARM
  cache      GPT-5.5          cache_put_ok   BA - A   B= 40 -1.00 -0.40 HARM
  cache      GPT-5.5          key_norm       AB - B   B= 40 +0.00 +0.60 
  cache      GPT-5.5          key_norm       BA - B   B= 40 +0.00 +0.60 
  cache      DeepSeek-V4-Pro  cache_put_ok   AB - A   B= 40 -0.45 +0.15 
  cache      DeepSeek-V4-Pro  cache_put_ok   BA - A   B= 40 -0.35 +0.25 
  cache      DeepSeek-V4-Pro  key_norm       AB - B   B= 40 +0.00 +0.60 
  cache      DeepSeek-V4-Pro  key_norm       BA - B   B= 40 +0.00 +0.60 
  cache      Kimi-K2.6        cache_put_ok   AB - A   B= 40 -1.00 -0.40 HARM
  cache      Kimi-K2.6        cache_put_ok   BA - A   B= 40 -1.00 -0.40 HARM
  cache      Kimi-K2.6        key_norm       AB - B   B= 40 +0.00 +0.60 
  cache      Kimi-K2.6        key_norm       BA - B   B= 40 +0.00 +0.60 
  inventory  Haiku-4.5        inv_book       AB - A   B= 40 -0.03 +0.58 
  inventory  Haiku-4.5        inv_book       BA - A   B= 40 +0.00 +0.60 
  inventory  Haiku-4.5        inv_sku        AB - B   B= 40 +0.00 +0.60 
  inventory  Haiku-4.5        inv_sku        BA - B   B= 40 +0.00 +0.60 
  inventory  Sonnet-4.6       inv_book       AB - A   B= 40 -1.00 -0.40 HARM
  inventory  Sonnet-4.6       inv_book       BA - A   B= 40 -1.00 -0.40 HARM
  inventory  Sonnet-4.6       inv_sku        AB - B   B= 40 +0.00 +0.60 
  inventory  Sonnet-4.6       inv_sku        BA - B   B= 40 +0.00 +0.60 
  inventory  Opus-4.8         inv_book       AB - A   B= 40 -1.00 -0.40 HARM
  inventory  Opus-4.8         inv_book       BA - A   B= 40 -1.00 -0.40 HARM
  inventory  Opus-4.8         inv_sku        AB - B   B= 40 +0.00 +0.60 
  inventory  Opus-4.8         inv_sku        BA - B   B= 40 +0.00 +0.60 
  inventory  GPT-5.5          inv_book       AB - A   B= 40 -1.00 -0.40 HARM
  inventory  GPT-5.5          inv_book       BA - A   B= 40 -1.00 -0.40 HARM
  inventory  GPT-5.5          inv_sku        AB - B   B= 40 +0.00 +0.60 
  inventory  GPT-5.5          inv_sku        BA - B   B= 40 +0.00 +0.60 
  inventory  DeepSeek-V4-Pro  inv_book       AB - A   B= 40 -0.25 +0.35 
  inventory  DeepSeek-V4-Pro  inv_book       BA - A   B= 40 -0.28 +0.33 
  inventory  DeepSeek-V4-Pro  inv_sku        AB - B   B= 40 -0.03 +0.58 
  inventory  DeepSeek-V4-Pro  inv_sku        BA - B   B= 40 +0.00 +0.60 
  inventory  Kimi-K2.6        inv_book       AB - A   B= 40 -1.00 -0.40 HARM
  inventory  Kimi-K2.6        inv_book       BA - A   B= 40 -1.00 -0.40 HARM
  inventory  Kimi-K2.6        inv_sku        AB - B   B= 40 +0.00 +0.60 
  inventory  Kimi-K2.6        inv_sku        BA - B   B= 40 +0.00 +0.60 
  audit      Haiku-4.5        audit_code     AB - A   B= 40 +0.17 +0.78 
  audit      Haiku-4.5        audit_code     BA - A   B= 40 +0.33 +0.93 
  audit      Haiku-4.5        audit_line     AB - B   B= 40 +0.03 +0.63 
  audit      Haiku-4.5        audit_line     BA - B   B= 40 -0.12 +0.48 
  audit      Sonnet-4.6       audit_code     AB - A   B= 40 +0.00 +0.60 
  audit      Sonnet-4.6       audit_code     BA - A   B= 40 +0.00 +0.60 
  audit      Sonnet-4.6       audit_line     AB - B   B= 40 +0.00 +0.60 
  audit      Sonnet-4.6       audit_line     BA - B   B= 40 +0.00 +0.60 
  audit      Opus-4.8         audit_code     AB - A   B= 40 +0.00 +0.60 
  audit      Opus-4.8         audit_code     BA - A   B= 40 +0.00 +0.60 
  audit      Opus-4.8         audit_line     AB - B   B= 40 +0.00 +0.60 
  audit      Opus-4.8         audit_line     BA - B   B= 40 +0.00 +0.60 
  audit      GPT-5.5          audit_code     AB - A   B= 40 +0.00 +0.60 
  audit      GPT-5.5          audit_code     BA - A   B= 40 +0.00 +0.60 
  audit      GPT-5.5          audit_line     AB - B   B= 40 +0.00 +0.60 
  audit      GPT-5.5          audit_line     BA - B   B= 40 +0.00 +0.60 
  audit      DeepSeek-V4-Pro  audit_code     AB - A   B= 40 +0.00 +0.60 
  audit      DeepSeek-V4-Pro  audit_code     BA - A   B= 40 +0.00 +0.60 
  audit      DeepSeek-V4-Pro  audit_line     AB - B   B= 40 +0.00 +0.60 
  audit      DeepSeek-V4-Pro  audit_line     BA - B   B= 40 -0.07 +0.53 
  audit      Kimi-K2.6        audit_code     AB - A   B= 40 +0.00 +0.60 
  audit      Kimi-K2.6        audit_code     BA - A   B= 40 +0.00 +0.60 
  audit      Kimi-K2.6        audit_line     AB - B   B= 40 +0.00 +0.60 
  audit      Kimi-K2.6        audit_line     BA - B   B= 40 +0.00 +0.60 

SECONDARY: ledger controls (estimate, two-sided interval at alpha = 0.05/36)
  Haiku-4.5        api_post_ok   W1plus - W1     B= 40 -1.00 [-1.60, -0.40] verified
  Haiku-4.5        api_post_ok   W1plus_rev - W1 B= 40 -1.00 [-1.60, -0.40] verified
  Haiku-4.5        api_post_ok   W1pad - W1      B= 40 +0.00 [-0.60, +0.60] 
  Sonnet-4.6       api_post_ok   W1plus - W1     B= 40 -1.00 [-1.60, -0.40] verified
  Sonnet-4.6       api_post_ok   W1plus_rev - W1 B= 40 -1.00 [-1.60, -0.40] verified
  Sonnet-4.6       api_post_ok   W1pad - W1      B= 40 +0.00 [-0.60, +0.60] 
  Opus-4.8         api_post_ok   W1plus - W1     B= 40 -1.00 [-1.60, -0.40] verified
  Opus-4.8         api_post_ok   W1plus_rev - W1 B= 40 -1.00 [-1.60, -0.40] verified
  Opus-4.8         api_post_ok   W1pad - W1      B= 40 +0.00 [-0.60, +0.60] 
  GPT-5.5          api_post_ok   W1plus - W1     B= 40 -1.00 [-1.60, -0.40] verified
  GPT-5.5          api_post_ok   W1plus_rev - W1 B= 40 -1.00 [-1.60, -0.40] verified
  GPT-5.5          api_post_ok   W1pad - W1      B= 40 +0.00 [-0.60, +0.60] 
  DeepSeek-V4-Pro  api_post_ok   W1plus - W1     B= 40 -0.78 [-1.38, -0.17] verified
  DeepSeek-V4-Pro  api_post_ok   W1plus_rev - W1 B= 40 -0.65 [-1.25, -0.05] verified
  DeepSeek-V4-Pro  api_post_ok   W1pad - W1      B= 40 -0.12 [-0.73, +0.48] 
  Kimi-K2.6        api_post_ok   W1plus - W1     B= 40 -1.00 [-1.60, -0.40] verified
  Kimi-K2.6        api_post_ok   W1plus_rev - W1 B= 40 -1.00 [-1.60, -0.40] verified
  Kimi-K2.6        api_post_ok   W1pad - W1      B= 40 +0.00 [-0.60, +0.60] 
  Haiku-4.5        api_argorder  W1plus - W1     B= 40 -0.82 [-1.43, -0.22] verified
  Haiku-4.5        api_argorder  W1plus_rev - W1 B= 40 -0.82 [-1.43, -0.22] verified
  Haiku-4.5        api_argorder  W1pad - W1      B= 40 +0.17 [-0.43, +0.78] 
  Sonnet-4.6       api_argorder  W1plus - W1     B= 40 -1.00 [-1.60, -0.40] verified
  Sonnet-4.6       api_argorder  W1plus_rev - W1 B= 40 -1.00 [-1.60, -0.40] verified
  Sonnet-4.6       api_argorder  W1pad - W1      B= 40 +0.00 [-0.60, +0.60] 
  Opus-4.8         api_argorder  W1plus - W1     B= 40 -1.00 [-1.60, -0.40] verified
  Opus-4.8         api_argorder  W1plus_rev - W1 B= 40 -1.00 [-1.60, -0.40] verified
  Opus-4.8         api_argorder  W1pad - W1      B= 40 +0.00 [-0.60, +0.60] 
  GPT-5.5          api_argorder  W1plus - W1     B= 40 -1.00 [-1.60, -0.40] verified
  GPT-5.5          api_argorder  W1plus_rev - W1 B= 40 -1.00 [-1.60, -0.40] verified
  GPT-5.5          api_argorder  W1pad - W1      B= 40 +0.00 [-0.60, +0.60] 
  DeepSeek-V4-Pro  api_argorder  W1plus - W1     B= 40 -0.57 [-1.18, +0.03] 
  DeepSeek-V4-Pro  api_argorder  W1plus_rev - W1 B= 40 -0.55 [-1.15, +0.05] 
  DeepSeek-V4-Pro  api_argorder  W1pad - W1      B= 40 +0.05 [-0.55, +0.65] 
  Kimi-K2.6        api_argorder  W1plus - W1     B= 40 -1.00 [-1.60, -0.40] verified
  Kimi-K2.6        api_argorder  W1plus_rev - W1 B= 40 -1.00 [-1.60, -0.40] verified
  Kimi-K2.6        api_argorder  W1pad - W1      B= 40 +0.00 [-0.60, +0.60] 

No-context baselines (passes / graded): cache cache_put_ok GPT-5.5 1/40
Replies graded differently by the published and hardened checks: 11
