requests: scheduled 1140, received 1140, graded 1140, transport failures 0

PRIMARY: PASS incomparability (hardened checks; alpha = 0.05/36 per statement)
pair       model            A - B on A-task (B, est, bound) B - A on B-task (B, est, bound) incomparable
cache      Haiku-4.5          5 +0.80 -0.82 no               5 +1.00 -0.62 no             no
cache      Sonnet-4.6         5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
cache      Opus-4.8           5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
cache      GPT-5.5            5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
cache      DeepSeek-V4-Pro    5 +0.60 -1.02 no               5 +1.00 -0.62 no             no
cache      Kimi-K2.6          5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
inventory  Haiku-4.5          5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
inventory  Sonnet-4.6         5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
inventory  Opus-4.8           5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
inventory  GPT-5.5            5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
inventory  DeepSeek-V4-Pro    5 +0.40 -1.22 no               5 +1.00 -0.62 no             no
inventory  Kimi-K2.6          5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
audit      Haiku-4.5          5 +0.40 -1.22 no               5 +1.00 -0.62 no             no
audit      Sonnet-4.6         5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
audit      Opus-4.8           5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
audit      GPT-5.5            5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
audit      DeepSeek-V4-Pro    5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
audit      Kimi-K2.6          5 +1.00 -0.62 no               5 +1.00 -0.62 no             no
pair-model combinations verified PASS-incomparable: 0 of 18
decisions unchanged under worst-case imputation: 18 of 18; under the published checks: 18 of 18

SECONDARY: augmentation (estimate, upper bound at alpha = 0.05/72, harm verified?)
  cache      Haiku-4.5        cache_put_ok   AB - A   B=  5 -0.80 +0.91 
  cache      Haiku-4.5        cache_put_ok   BA - A   B=  5 -0.80 +0.91 
  cache      Haiku-4.5        key_norm       AB - B   B=  5 +0.00 +1.71 
  cache      Haiku-4.5        key_norm       BA - B   B=  5 -0.20 +1.51 
  cache      Sonnet-4.6       cache_put_ok   AB - A   B=  5 -1.00 +0.71 
  cache      Sonnet-4.6       cache_put_ok   BA - A   B=  5 -1.00 +0.71 
  cache      Sonnet-4.6       key_norm       AB - B   B=  5 +0.00 +1.71 
  cache      Sonnet-4.6       key_norm       BA - B   B=  5 +0.00 +1.71 
  cache      Opus-4.8         cache_put_ok   AB - A   B=  5 -1.00 +0.71 
  cache      Opus-4.8         cache_put_ok   BA - A   B=  5 +0.00 +1.71 
  cache      Opus-4.8         key_norm       AB - B   B=  5 +0.00 +1.71 
  cache      Opus-4.8         key_norm       BA - B   B=  5 +0.00 +1.71 
  cache      GPT-5.5          cache_put_ok   AB - A   B=  5 -1.00 +0.71 
  cache      GPT-5.5          cache_put_ok   BA - A   B=  5 -1.00 +0.71 
  cache      GPT-5.5          key_norm       AB - B   B=  5 +0.00 +1.71 
  cache      GPT-5.5          key_norm       BA - B   B=  5 +0.00 +1.71 
  cache      DeepSeek-V4-Pro  cache_put_ok   AB - A   B=  5 -0.60 +1.11 
  cache      DeepSeek-V4-Pro  cache_put_ok   BA - A   B=  5 -0.40 +1.31 
  cache      DeepSeek-V4-Pro  key_norm       AB - B   B=  5 +0.00 +1.71 
  cache      DeepSeek-V4-Pro  key_norm       BA - B   B=  5 +0.00 +1.71 
  cache      Kimi-K2.6        cache_put_ok   AB - A   B=  5 -1.00 +0.71 
  cache      Kimi-K2.6        cache_put_ok   BA - A   B=  5 -1.00 +0.71 
  cache      Kimi-K2.6        key_norm       AB - B   B=  5 +0.00 +1.71 
  cache      Kimi-K2.6        key_norm       BA - B   B=  5 +0.00 +1.71 
  inventory  Haiku-4.5        inv_book       AB - A   B=  5 +0.00 +1.71 
  inventory  Haiku-4.5        inv_book       BA - A   B=  5 +0.00 +1.71 
  inventory  Haiku-4.5        inv_sku        AB - B   B=  5 +0.00 +1.71 
  inventory  Haiku-4.5        inv_sku        BA - B   B=  5 +0.00 +1.71 
  inventory  Sonnet-4.6       inv_book       AB - A   B=  5 -1.00 +0.71 
  inventory  Sonnet-4.6       inv_book       BA - A   B=  5 -1.00 +0.71 
  inventory  Sonnet-4.6       inv_sku        AB - B   B=  5 +0.00 +1.71 
  inventory  Sonnet-4.6       inv_sku        BA - B   B=  5 +0.00 +1.71 
  inventory  Opus-4.8         inv_book       AB - A   B=  5 -1.00 +0.71 
  inventory  Opus-4.8         inv_book       BA - A   B=  5 -1.00 +0.71 
  inventory  Opus-4.8         inv_sku        AB - B   B=  5 +0.00 +1.71 
  inventory  Opus-4.8         inv_sku        BA - B   B=  5 +0.00 +1.71 
  inventory  GPT-5.5          inv_book       AB - A   B=  5 -1.00 +0.71 
  inventory  GPT-5.5          inv_book       BA - A   B=  5 -1.00 +0.71 
  inventory  GPT-5.5          inv_sku        AB - B   B=  5 +0.00 +1.71 
  inventory  GPT-5.5          inv_sku        BA - B   B=  5 +0.00 +1.71 
  inventory  DeepSeek-V4-Pro  inv_book       AB - A   B=  5 -0.40 +1.31 
  inventory  DeepSeek-V4-Pro  inv_book       BA - A   B=  5 -0.40 +1.31 
  inventory  DeepSeek-V4-Pro  inv_sku        AB - B   B=  5 +0.00 +1.71 
  inventory  DeepSeek-V4-Pro  inv_sku        BA - B   B=  5 +0.00 +1.71 
  inventory  Kimi-K2.6        inv_book       AB - A   B=  5 -1.00 +0.71 
  inventory  Kimi-K2.6        inv_book       BA - A   B=  5 -1.00 +0.71 
  inventory  Kimi-K2.6        inv_sku        AB - B   B=  5 +0.00 +1.71 
  inventory  Kimi-K2.6        inv_sku        BA - B   B=  5 +0.00 +1.71 
  audit      Haiku-4.5        audit_code     AB - A   B=  5 +0.40 +2.11 
  audit      Haiku-4.5        audit_code     BA - A   B=  5 +0.60 +2.31 
  audit      Haiku-4.5        audit_line     AB - B   B=  5 -0.20 +1.51 
  audit      Haiku-4.5        audit_line     BA - B   B=  5 -0.20 +1.51 
  audit      Sonnet-4.6       audit_code     AB - A   B=  5 +0.00 +1.71 
  audit      Sonnet-4.6       audit_code     BA - A   B=  5 +0.00 +1.71 
  audit      Sonnet-4.6       audit_line     AB - B   B=  5 +0.00 +1.71 
  audit      Sonnet-4.6       audit_line     BA - B   B=  5 +0.00 +1.71 
  audit      Opus-4.8         audit_code     AB - A   B=  5 +0.00 +1.71 
  audit      Opus-4.8         audit_code     BA - A   B=  5 +0.00 +1.71 
  audit      Opus-4.8         audit_line     AB - B   B=  5 +0.00 +1.71 
  audit      Opus-4.8         audit_line     BA - B   B=  5 +0.00 +1.71 
  audit      GPT-5.5          audit_code     AB - A   B=  5 +0.00 +1.71 
  audit      GPT-5.5          audit_code     BA - A   B=  5 +0.00 +1.71 
  audit      GPT-5.5          audit_line     AB - B   B=  5 +0.00 +1.71 
  audit      GPT-5.5          audit_line     BA - B   B=  5 +0.00 +1.71 
  audit      DeepSeek-V4-Pro  audit_code     AB - A   B=  5 +0.00 +1.71 
  audit      DeepSeek-V4-Pro  audit_code     BA - A   B=  5 +0.00 +1.71 
  audit      DeepSeek-V4-Pro  audit_line     AB - B   B=  5 +0.00 +1.71 
  audit      DeepSeek-V4-Pro  audit_line     BA - B   B=  5 +0.00 +1.71 
  audit      Kimi-K2.6        audit_code     AB - A   B=  5 +0.00 +1.71 
  audit      Kimi-K2.6        audit_code     BA - A   B=  5 +0.00 +1.71 
  audit      Kimi-K2.6        audit_line     AB - B   B=  5 +0.00 +1.71 
  audit      Kimi-K2.6        audit_line     BA - B   B=  5 +0.00 +1.71 

SECONDARY: ledger controls (estimate, two-sided interval at alpha = 0.05/36)
  Haiku-4.5        api_post_ok   W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  Haiku-4.5        api_post_ok   W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  Haiku-4.5        api_post_ok   W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 
  Sonnet-4.6       api_post_ok   W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  Sonnet-4.6       api_post_ok   W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  Sonnet-4.6       api_post_ok   W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 
  Opus-4.8         api_post_ok   W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  Opus-4.8         api_post_ok   W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  Opus-4.8         api_post_ok   W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 
  GPT-5.5          api_post_ok   W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  GPT-5.5          api_post_ok   W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  GPT-5.5          api_post_ok   W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 
  DeepSeek-V4-Pro  api_post_ok   W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  DeepSeek-V4-Pro  api_post_ok   W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  DeepSeek-V4-Pro  api_post_ok   W1pad - W1      B=  5 -0.20 [-1.91, +1.51] 
  Kimi-K2.6        api_post_ok   W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  Kimi-K2.6        api_post_ok   W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  Kimi-K2.6        api_post_ok   W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 
  Haiku-4.5        api_argorder  W1plus - W1     B=  5 -0.80 [-2.51, +0.91] 
  Haiku-4.5        api_argorder  W1plus_rev - W1 B=  5 -0.80 [-2.51, +0.91] 
  Haiku-4.5        api_argorder  W1pad - W1      B=  5 +0.20 [-1.51, +1.91] 
  Sonnet-4.6       api_argorder  W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  Sonnet-4.6       api_argorder  W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  Sonnet-4.6       api_argorder  W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 
  Opus-4.8         api_argorder  W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  Opus-4.8         api_argorder  W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  Opus-4.8         api_argorder  W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 
  GPT-5.5          api_argorder  W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  GPT-5.5          api_argorder  W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  GPT-5.5          api_argorder  W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 
  DeepSeek-V4-Pro  api_argorder  W1plus - W1     B=  5 -0.60 [-2.31, +1.11] 
  DeepSeek-V4-Pro  api_argorder  W1plus_rev - W1 B=  5 -0.20 [-1.91, +1.51] 
  DeepSeek-V4-Pro  api_argorder  W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 
  Kimi-K2.6        api_argorder  W1plus - W1     B=  5 -1.00 [-2.71, +0.71] 
  Kimi-K2.6        api_argorder  W1plus_rev - W1 B=  5 -1.00 [-2.71, +0.71] 
  Kimi-K2.6        api_argorder  W1pad - W1      B=  5 +0.00 [-1.71, +1.71] 

No-context baselines (passes / graded): cache key_norm GPT-5.5 2/5; inventory inv_sku GPT-5.5 2/5; audit audit_code GPT-5.5 1/5
Replies graded differently by the published and hardened checks: 0
