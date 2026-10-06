PACKAGE 3: listwise reranking on HotpotQA's retrieved candidates (fullwiki), confirm records natural_data/package3/confirm_fullwiki/records.jsonl
freeze: verified, nothing changed
questions: 300 (sufficient 90, complement 210)
requests: planned 7800 (ranking 600, answer 7200); issued 7800; received 7800
  ranking status: o0|received 300, o1|received 300
  answer status: failed_http400 13, received 7187

RETRIEVAL COVERAGE: supporting paragraphs among the 10 candidates, mean share [95% CI] (count with 0/1/2)
  all         n=300  0.55 [0.51, 0.59]  {'0': 60, '1': 150, '2': 90}
  sufficient  n= 90  1.00 [1.00, 1.00]  {'2': 90}
  complement  n=210  0.36 [0.33, 0.39]  {'0': 60, '1': 150}

EVIDENCE at K = 2, mean [95% CI]: support recall | all supporting in the top 2
  bm25     all         n=300  0.46 [0.42, 0.50] | 0.16 [0.12, 0.21]
  bm25     sufficient  n= 90  0.76 [0.70, 0.81] | 0.54 [0.44, 0.64]
  bm25     complement  n=210  0.33 [0.30, 0.36] | 0.00 [0.00, 0.00]
  mmr      all         n=300  0.43 [0.39, 0.46] | 0.12 [0.08, 0.15]
  mmr      sufficient  n= 90  0.67 [0.61, 0.72] | 0.39 [0.29, 0.49]
  mmr      complement  n=210  0.33 [0.29, 0.36] | 0.00 [0.00, 0.00]
  bge      all         n=300  0.48 [0.44, 0.52] | 0.21 [0.16, 0.25]
  bge      sufficient  n= 90  0.82 [0.76, 0.88] | 0.69 [0.59, 0.78]
  bge      complement  n=210  0.34 [0.30, 0.37] | 0.00 [0.00, 0.00]
  e5       all         n=300  0.48 [0.44, 0.52] | 0.20 [0.15, 0.25]
  e5       sufficient  n= 90  0.82 [0.76, 0.87] | 0.67 [0.57, 0.77]
  e5       complement  n=210  0.33 [0.30, 0.36] | 0.00 [0.00, 0.00]
  minilm   all         n=300  0.50 [0.46, 0.54] | 0.23 [0.18, 0.28]
  minilm   sufficient  n= 90  0.87 [0.82, 0.92] | 0.76 [0.67, 0.84]
  minilm   complement  n=210  0.34 [0.31, 0.37] | 0.00 [0.00, 0.00]
  rankgpt  all         n=300  0.52 [0.48, 0.56] | 0.26 [0.21, 0.31]
  rankgpt  sufficient  n= 90  0.93 [0.89, 0.97] | 0.88 [0.81, 0.94]
  rankgpt  complement  n=210  0.35 [0.32, 0.38] | 0.00 [0.00, 0.00]

ANSWERS, mean [95% CI]: exact match | F1
  all         Haiku-4.5        none     n=300  0.34 [0.28, 0.39] | 0.46 [0.41, 0.51]
  all         Haiku-4.5        full     n=300  0.27 [0.22, 0.32] | 0.41 [0.36, 0.46]
  all         Haiku-4.5        bm25     n=300  0.26 [0.21, 0.31] | 0.39 [0.34, 0.44]
  all         Haiku-4.5        mmr      n=300  0.23 [0.19, 0.28] | 0.34 [0.30, 0.39]
  all         Haiku-4.5        bge      n=300  0.27 [0.22, 0.32] | 0.39 [0.34, 0.44]
  all         Haiku-4.5        e5       n=300  0.23 [0.18, 0.28] | 0.36 [0.31, 0.41]
  all         Haiku-4.5        minilm   n=300  0.27 [0.22, 0.32] | 0.41 [0.36, 0.46]
  all         Haiku-4.5        rankgpt  n=300  0.29 [0.24, 0.34] | 0.43 [0.38, 0.48]
  all         GPT-5.5          none     n=300  0.48 [0.43, 0.54] | 0.67 [0.62, 0.71]
  all         GPT-5.5          full     n=299  0.52 [0.46, 0.57] | 0.70 [0.66, 0.74]
  all         GPT-5.5          bm25     n=299  0.52 [0.46, 0.57] | 0.69 [0.65, 0.74]
  all         GPT-5.5          mmr      n=299  0.52 [0.46, 0.58] | 0.69 [0.64, 0.73]
  all         GPT-5.5          bge      n=299  0.51 [0.45, 0.56] | 0.68 [0.63, 0.72]
  all         GPT-5.5          e5       n=298  0.51 [0.45, 0.57] | 0.69 [0.64, 0.73]
  all         GPT-5.5          minilm   n=298  0.53 [0.48, 0.59] | 0.72 [0.68, 0.77]
  all         GPT-5.5          rankgpt  n=299  0.51 [0.45, 0.56] | 0.69 [0.65, 0.74]
  all         DeepSeek-V4-Pro  none     n=300  0.44 [0.38, 0.50] | 0.58 [0.53, 0.63]
  all         DeepSeek-V4-Pro  full     n=298  0.39 [0.33, 0.45] | 0.53 [0.48, 0.58]
  all         DeepSeek-V4-Pro  bm25     n=300  0.38 [0.32, 0.43] | 0.49 [0.44, 0.54]
  all         DeepSeek-V4-Pro  mmr      n=300  0.34 [0.28, 0.39] | 0.47 [0.42, 0.52]
  all         DeepSeek-V4-Pro  bge      n=300  0.37 [0.32, 0.43] | 0.50 [0.45, 0.56]
  all         DeepSeek-V4-Pro  e5       n=299  0.37 [0.31, 0.42] | 0.50 [0.45, 0.55]
  all         DeepSeek-V4-Pro  minilm   n=299  0.40 [0.34, 0.45] | 0.52 [0.47, 0.57]
  all         DeepSeek-V4-Pro  rankgpt  n=300  0.41 [0.35, 0.46] | 0.54 [0.49, 0.59]
  sufficient  Haiku-4.5        none     n= 90  0.30 [0.21, 0.40] | 0.46 [0.37, 0.56]
  sufficient  Haiku-4.5        full     n= 90  0.44 [0.34, 0.54] | 0.71 [0.64, 0.78]
  sufficient  Haiku-4.5        bm25     n= 90  0.38 [0.28, 0.48] | 0.61 [0.53, 0.69]
  sufficient  Haiku-4.5        mmr      n= 90  0.32 [0.23, 0.42] | 0.51 [0.42, 0.61]
  sufficient  Haiku-4.5        bge      n= 90  0.42 [0.32, 0.52] | 0.63 [0.54, 0.71]
  sufficient  Haiku-4.5        e5       n= 90  0.37 [0.27, 0.47] | 0.62 [0.54, 0.70]
  sufficient  Haiku-4.5        minilm   n= 90  0.40 [0.30, 0.50] | 0.68 [0.60, 0.75]
  sufficient  Haiku-4.5        rankgpt  n= 90  0.46 [0.36, 0.56] | 0.71 [0.63, 0.78]
  sufficient  GPT-5.5          none     n= 90  0.37 [0.27, 0.47] | 0.60 [0.52, 0.68]
  sufficient  GPT-5.5          full     n= 90  0.41 [0.31, 0.51] | 0.70 [0.62, 0.77]
  sufficient  GPT-5.5          bm25     n= 89  0.39 [0.29, 0.49] | 0.66 [0.59, 0.74]
  sufficient  GPT-5.5          mmr      n= 89  0.45 [0.35, 0.55] | 0.67 [0.59, 0.75]
  sufficient  GPT-5.5          bge      n= 89  0.42 [0.31, 0.52] | 0.66 [0.58, 0.74]
  sufficient  GPT-5.5          e5       n= 89  0.42 [0.31, 0.52] | 0.68 [0.60, 0.76]
  sufficient  GPT-5.5          minilm   n= 89  0.42 [0.31, 0.52] | 0.68 [0.60, 0.76]
  sufficient  GPT-5.5          rankgpt  n= 89  0.42 [0.31, 0.52] | 0.70 [0.63, 0.77]
  sufficient  DeepSeek-V4-Pro  none     n= 90  0.36 [0.26, 0.46] | 0.55 [0.46, 0.64]
  sufficient  DeepSeek-V4-Pro  full     n= 88  0.50 [0.40, 0.60] | 0.73 [0.65, 0.80]
  sufficient  DeepSeek-V4-Pro  bm25     n= 90  0.41 [0.31, 0.51] | 0.61 [0.53, 0.69]
  sufficient  DeepSeek-V4-Pro  mmr      n= 90  0.39 [0.29, 0.49] | 0.58 [0.49, 0.67]
  sufficient  DeepSeek-V4-Pro  bge      n= 90  0.47 [0.37, 0.58] | 0.67 [0.59, 0.75]
  sufficient  DeepSeek-V4-Pro  e5       n= 90  0.46 [0.36, 0.56] | 0.67 [0.59, 0.75]
  sufficient  DeepSeek-V4-Pro  minilm   n= 90  0.50 [0.40, 0.60] | 0.70 [0.62, 0.78]
  sufficient  DeepSeek-V4-Pro  rankgpt  n= 90  0.49 [0.39, 0.59] | 0.71 [0.64, 0.79]
  complement  Haiku-4.5        none     n=210  0.35 [0.29, 0.41] | 0.46 [0.40, 0.52]
  complement  Haiku-4.5        full     n=210  0.19 [0.14, 0.25] | 0.28 [0.23, 0.34]
  complement  Haiku-4.5        bm25     n=210  0.20 [0.15, 0.26] | 0.29 [0.24, 0.35]
  complement  Haiku-4.5        mmr      n=210  0.20 [0.14, 0.25] | 0.27 [0.22, 0.33]
  complement  Haiku-4.5        bge      n=210  0.20 [0.15, 0.26] | 0.28 [0.23, 0.34]
  complement  Haiku-4.5        e5       n=210  0.17 [0.12, 0.22] | 0.25 [0.20, 0.31]
  complement  Haiku-4.5        minilm   n=210  0.22 [0.17, 0.28] | 0.30 [0.25, 0.36]
  complement  Haiku-4.5        rankgpt  n=210  0.22 [0.17, 0.28] | 0.31 [0.25, 0.37]
  complement  GPT-5.5          none     n=210  0.53 [0.47, 0.60] | 0.69 [0.64, 0.75]
  complement  GPT-5.5          full     n=209  0.56 [0.49, 0.63] | 0.70 [0.65, 0.76]
  complement  GPT-5.5          bm25     n=210  0.57 [0.50, 0.63] | 0.71 [0.65, 0.76]
  complement  GPT-5.5          mmr      n=210  0.55 [0.49, 0.62] | 0.69 [0.64, 0.75]
  complement  GPT-5.5          bge      n=210  0.54 [0.48, 0.61] | 0.68 [0.63, 0.74]
  complement  GPT-5.5          e5       n=209  0.55 [0.48, 0.62] | 0.69 [0.63, 0.74]
  complement  GPT-5.5          minilm   n=209  0.58 [0.52, 0.65] | 0.74 [0.69, 0.79]
  complement  GPT-5.5          rankgpt  n=210  0.54 [0.48, 0.61] | 0.69 [0.64, 0.75]
  complement  DeepSeek-V4-Pro  none     n=210  0.48 [0.40, 0.54] | 0.60 [0.54, 0.65]
  complement  DeepSeek-V4-Pro  full     n=210  0.34 [0.28, 0.40] | 0.44 [0.38, 0.50]
  complement  DeepSeek-V4-Pro  bm25     n=210  0.36 [0.30, 0.43] | 0.43 [0.37, 0.50]
  complement  DeepSeek-V4-Pro  mmr      n=210  0.31 [0.25, 0.38] | 0.42 [0.36, 0.48]
  complement  DeepSeek-V4-Pro  bge      n=210  0.33 [0.27, 0.39] | 0.43 [0.37, 0.49]
  complement  DeepSeek-V4-Pro  e5       n=209  0.33 [0.27, 0.40] | 0.43 [0.37, 0.49]
  complement  DeepSeek-V4-Pro  minilm   n=209  0.35 [0.29, 0.43] | 0.44 [0.38, 0.51]
  complement  DeepSeek-V4-Pro  rankgpt  n=210  0.37 [0.31, 0.44] | 0.47 [0.40, 0.53]

PRIMARY: RankGPT minus each local ranker, F1, all questions (estimate [simultaneous 95%, Bonferroni over 15])
  Haiku-4.5|rankgpt-bm25                       n=300  0.04 [-0.01, 0.09] 
  Haiku-4.5|rankgpt-mmr                        n=300  0.08 [0.02, 0.15] RankGPT better
  Haiku-4.5|rankgpt-bge                        n=300  0.04 [-0.01, 0.09] 
  Haiku-4.5|rankgpt-e5                         n=300  0.06 [0.01, 0.12] RankGPT better
  Haiku-4.5|rankgpt-minilm                     n=300  0.01 [-0.04, 0.06] 
  GPT-5.5|rankgpt-bm25                         n=299  0.00 [-0.04, 0.04] 
  GPT-5.5|rankgpt-mmr                          n=299  0.01 [-0.04, 0.06] 
  GPT-5.5|rankgpt-bge                          n=299  0.02 [-0.03, 0.06] 
  GPT-5.5|rankgpt-e5                           n=298  0.01 [-0.03, 0.05] 
  GPT-5.5|rankgpt-minilm                       n=298  -0.03 [-0.07, 0.01] 
  DeepSeek-V4-Pro|rankgpt-bm25                 n=300  0.05 [-0.01, 0.12] 
  DeepSeek-V4-Pro|rankgpt-mmr                  n=300  0.07 [0.01, 0.14] RankGPT better
  DeepSeek-V4-Pro|rankgpt-bge                  n=300  0.04 [-0.02, 0.09] 
  DeepSeek-V4-Pro|rankgpt-e5                   n=299  0.04 [-0.02, 0.10] 
  DeepSeek-V4-Pro|rankgpt-minilm               n=299  0.02 [-0.03, 0.08] 

SECONDARY: the same contrasts per subgroup (estimate [simultaneous 95%, Bonferroni over 30])
  sufficient|Haiku-4.5|rankgpt-bm25            n= 90  0.10 [0.01, 0.21] RankGPT better
  sufficient|Haiku-4.5|rankgpt-mmr             n= 90  0.19 [0.06, 0.32] RankGPT better
  sufficient|Haiku-4.5|rankgpt-bge             n= 90  0.08 [-0.03, 0.19] 
  sufficient|Haiku-4.5|rankgpt-e5              n= 90  0.09 [-0.01, 0.20] 
  sufficient|Haiku-4.5|rankgpt-minilm          n= 90  0.03 [-0.03, 0.10] 
  sufficient|GPT-5.5|rankgpt-bm25              n= 89  0.04 [-0.02, 0.11] 
  sufficient|GPT-5.5|rankgpt-mmr               n= 89  0.03 [-0.05, 0.12] 
  sufficient|GPT-5.5|rankgpt-bge               n= 89  0.04 [-0.00, 0.11] 
  sufficient|GPT-5.5|rankgpt-e5                n= 89  0.02 [-0.02, 0.08] 
  sufficient|GPT-5.5|rankgpt-minilm            n= 89  0.02 [-0.02, 0.07] 
  sufficient|DeepSeek-V4-Pro|rankgpt-bm25      n= 90  0.10 [-0.01, 0.22] 
  sufficient|DeepSeek-V4-Pro|rankgpt-mmr       n= 90  0.13 [0.03, 0.25] RankGPT better
  sufficient|DeepSeek-V4-Pro|rankgpt-bge       n= 90  0.04 [-0.01, 0.12] 
  sufficient|DeepSeek-V4-Pro|rankgpt-e5        n= 90  0.04 [-0.03, 0.14] 
  sufficient|DeepSeek-V4-Pro|rankgpt-minilm    n= 90  0.01 [-0.04, 0.08] 
  complement|Haiku-4.5|rankgpt-bm25            n=210  0.02 [-0.05, 0.08] 
  complement|Haiku-4.5|rankgpt-mmr             n=210  0.04 [-0.03, 0.11] 
  complement|Haiku-4.5|rankgpt-bge             n=210  0.03 [-0.05, 0.10] 
  complement|Haiku-4.5|rankgpt-e5              n=210  0.05 [-0.01, 0.12] 
  complement|Haiku-4.5|rankgpt-minilm          n=210  0.00 [-0.06, 0.08] 
  complement|GPT-5.5|rankgpt-bm25              n=210  -0.02 [-0.08, 0.05] 
  complement|GPT-5.5|rankgpt-mmr               n=210  -0.00 [-0.06, 0.06] 
  complement|GPT-5.5|rankgpt-bge               n=210  0.01 [-0.05, 0.07] 
  complement|GPT-5.5|rankgpt-e5                n=209  0.00 [-0.06, 0.06] 
  complement|GPT-5.5|rankgpt-minilm            n=209  -0.05 [-0.12, 0.01] 
  complement|DeepSeek-V4-Pro|rankgpt-bm25      n=210  0.03 [-0.06, 0.12] 
  complement|DeepSeek-V4-Pro|rankgpt-mmr       n=210  0.05 [-0.04, 0.14] 
  complement|DeepSeek-V4-Pro|rankgpt-bge       n=210  0.03 [-0.04, 0.12] 
  complement|DeepSeek-V4-Pro|rankgpt-e5        n=209  0.04 [-0.04, 0.12] 
  complement|DeepSeek-V4-Pro|rankgpt-minilm    n=209  0.02 [-0.05, 0.11] 

EVIDENCE CRITERION: RankGPT minus each local ranker, support recall at K, all questions (simultaneous 95%, Bonferroni over 5); missing RankGPT rankings 0
  rankgpt-bm25                                 n=300  0.06 [0.04, 0.10] RankGPT better
  rankgpt-mmr                                  n=300  0.10 [0.06, 0.13] RankGPT better
  rankgpt-bge                                  n=300  0.04 [0.01, 0.07] RankGPT better
  rankgpt-e5                                   n=300  0.04 [0.02, 0.07] RankGPT better
  rankgpt-minilm                               n=300  0.02 [0.00, 0.04] 
  criterion holds (all five verified positive): no

WORST CASE (primary family; missing RankGPT answer F1 0, missing comparator answer F1 1)
  Haiku-4.5|rankgpt-bm25                       n=300  0.04 [-0.01, 0.09]   (missing: RankGPT 0, comparator 0)
  Haiku-4.5|rankgpt-mmr                        n=300  0.08 [0.02, 0.15] RankGPT better  (missing: RankGPT 0, comparator 0)
  Haiku-4.5|rankgpt-bge                        n=300  0.04 [-0.01, 0.09]   (missing: RankGPT 0, comparator 0)
  Haiku-4.5|rankgpt-e5                         n=300  0.06 [0.01, 0.12] RankGPT better  (missing: RankGPT 0, comparator 0)
  Haiku-4.5|rankgpt-minilm                     n=300  0.01 [-0.04, 0.06]   (missing: RankGPT 0, comparator 0)
  GPT-5.5|rankgpt-bm25                         n=300  -0.00 [-0.05, 0.04]   (missing: RankGPT 1, comparator 1)
  GPT-5.5|rankgpt-mmr                          n=300  0.01 [-0.04, 0.05]   (missing: RankGPT 1, comparator 1)
  GPT-5.5|rankgpt-bge                          n=300  0.01 [-0.04, 0.06]   (missing: RankGPT 1, comparator 1)
  GPT-5.5|rankgpt-e5                           n=300  0.00 [-0.04, 0.05]   (missing: RankGPT 1, comparator 2)
  GPT-5.5|rankgpt-minilm                       n=300  -0.03 [-0.08, 0.01]   (missing: RankGPT 1, comparator 2)
  DeepSeek-V4-Pro|rankgpt-bm25                 n=300  0.05 [-0.01, 0.12]   (missing: RankGPT 0, comparator 0)
  DeepSeek-V4-Pro|rankgpt-mmr                  n=300  0.07 [0.01, 0.14] RankGPT better  (missing: RankGPT 0, comparator 0)
  DeepSeek-V4-Pro|rankgpt-bge                  n=300  0.04 [-0.02, 0.09]   (missing: RankGPT 0, comparator 0)
  DeepSeek-V4-Pro|rankgpt-e5                   n=300  0.04 [-0.02, 0.10]   (missing: RankGPT 0, comparator 1)
  DeepSeek-V4-Pro|rankgpt-minilm               n=300  0.02 [-0.03, 0.07]   (missing: RankGPT 0, comparator 1)

RANKGPT RESOURCES (Haiku-4.5, both input orders): requests 600, transport failures 0, extra attempts 0
  latency s 1.53 [1.49, 1.57] | input tokens 1671 [1638, 1704] | output tokens 50 [47, 54]
  complete parses o0 291/300, o1 297/300; top-2 agreement o0 vs o1 0.79 [0.76, 0.82]; Kendall tau 0.53 [0.49, 0.56] (pairs 300)

Answer-line compliance: DeepSeek-V4-Pro 2396/2396; GPT-5.5 2387/2391; Haiku-4.5 2400/2400

VERDICT (PROTOCOL_FULLWIKI.md, Section 7): rule 4, little or no improvement: the advantage has narrower scope than the supplied-pool benchmark suggested
  P+ 3, P- 0 (of 15); S+ 3, C+ 0 (of 15 each); evidence criterion does not hold
  worst case: P+ 3, P- 0 -> rule 4, little or no improvement (same row)
