requests: issued 9240, received 9240, transport failures 13

EVIDENCE RETRIEVAL at the budget K (mean [95% CI]): support recall | all supporting retrieved
  hotpotqa|bm25      n=200  0.55 [0.50, 0.59] | 0.23 [0.17, 0.28]
  hotpotqa|mmr       n=200  0.62 [0.59, 0.66] | 0.30 [0.24, 0.37]
  hotpotqa|bge       n=200  0.70 [0.66, 0.75] | 0.47 [0.40, 0.54]
  hotpotqa|e5        n=200  0.68 [0.64, 0.72] | 0.42 [0.35, 0.49]
  hotpotqa|minilm    n=200  0.68 [0.64, 0.72] | 0.40 [0.33, 0.47]
  hotpotqa|rankgpt   n=200  0.90 [0.87, 0.93] | 0.82 [0.77, 0.87]
  musique|bm25       n=100  0.47 [0.41, 0.52] | 0.13 [0.07, 0.20]
  musique|mmr        n=100  0.45 [0.40, 0.50] | 0.07 [0.02, 0.12]
  musique|bge        n=100  0.62 [0.56, 0.67] | 0.28 [0.20, 0.37]
  musique|e5         n=100  0.63 [0.57, 0.69] | 0.32 [0.23, 0.41]
  musique|minilm     n=100  0.61 [0.56, 0.67] | 0.27 [0.19, 0.36]
  musique|rankgpt    n=100  0.92 [0.89, 0.95] | 0.80 [0.72, 0.87]

ANSWERS (mean [95% CI]): exact match | F1
  hotpot_aug|DeepSeek-V4-Pro|dist+gold     n= 99  0.62 [0.52, 0.72] | 0.77 [0.70, 0.84]
  hotpot_aug|DeepSeek-V4-Pro|gold          n= 99  0.62 [0.52, 0.72] | 0.78 [0.71, 0.85]
  hotpot_aug|DeepSeek-V4-Pro|gold+dist     n= 99  0.61 [0.51, 0.70] | 0.76 [0.68, 0.83]
  hotpot_aug|DeepSeek-V4-Pro|none          n=100  0.39 [0.29, 0.48] | 0.53 [0.45, 0.62]
  hotpot_aug|GPT-5.5|dist+gold             n=100  0.65 [0.55, 0.74] | 0.78 [0.70, 0.85]
  hotpot_aug|GPT-5.5|gold                  n= 98  0.68 [0.59, 0.78] | 0.81 [0.74, 0.87]
  hotpot_aug|GPT-5.5|gold+dist             n= 98  0.66 [0.57, 0.76] | 0.80 [0.72, 0.86]
  hotpot_aug|GPT-5.5|none                  n=100  0.46 [0.36, 0.56] | 0.61 [0.52, 0.70]
  hotpot_aug|Haiku-4.5|dist+gold           n=100  0.60 [0.50, 0.69] | 0.77 [0.70, 0.84]
  hotpot_aug|Haiku-4.5|gold                n=100  0.60 [0.51, 0.70] | 0.76 [0.69, 0.83]
  hotpot_aug|Haiku-4.5|gold+dist           n=100  0.59 [0.49, 0.68] | 0.78 [0.71, 0.84]
  hotpot_aug|Haiku-4.5|none                n=100  0.27 [0.19, 0.36] | 0.37 [0.29, 0.46]
  hotpot_rank|DeepSeek-V4-Pro|bge          n=199  0.52 [0.45, 0.59] | 0.63 [0.57, 0.69]
  hotpot_rank|DeepSeek-V4-Pro|bm25         n=200  0.41 [0.34, 0.47] | 0.52 [0.46, 0.58]
  hotpot_rank|DeepSeek-V4-Pro|e5           n=200  0.51 [0.44, 0.57] | 0.62 [0.55, 0.68]
  hotpot_rank|DeepSeek-V4-Pro|full         n=200  0.65 [0.58, 0.71] | 0.79 [0.74, 0.84]
  hotpot_rank|DeepSeek-V4-Pro|minilm       n=200  0.49 [0.42, 0.56] | 0.61 [0.54, 0.67]
  hotpot_rank|DeepSeek-V4-Pro|mmr          n=200  0.44 [0.37, 0.51] | 0.57 [0.50, 0.63]
  hotpot_rank|DeepSeek-V4-Pro|none         n=200  0.48 [0.41, 0.56] | 0.60 [0.54, 0.66]
  hotpot_rank|DeepSeek-V4-Pro|rankgpt      n=200  0.62 [0.56, 0.69] | 0.79 [0.74, 0.84]
  hotpot_rank|GPT-5.5|bge                  n=199  0.61 [0.54, 0.68] | 0.78 [0.73, 0.83]
  hotpot_rank|GPT-5.5|bm25                 n=199  0.58 [0.51, 0.65] | 0.74 [0.69, 0.79]
  hotpot_rank|GPT-5.5|e5                   n=200  0.58 [0.52, 0.65] | 0.76 [0.70, 0.80]
  hotpot_rank|GPT-5.5|full                 n=200  0.67 [0.60, 0.73] | 0.83 [0.79, 0.87]
  hotpot_rank|GPT-5.5|minilm               n=199  0.60 [0.53, 0.67] | 0.76 [0.71, 0.81]
  hotpot_rank|GPT-5.5|mmr                  n=200  0.57 [0.50, 0.64] | 0.74 [0.68, 0.79]
  hotpot_rank|GPT-5.5|none                 n=200  0.57 [0.50, 0.64] | 0.71 [0.66, 0.76]
  hotpot_rank|GPT-5.5|rankgpt              n=199  0.66 [0.59, 0.72] | 0.82 [0.78, 0.86]
  hotpot_rank|Haiku-4.5|bge                n=200  0.44 [0.37, 0.51] | 0.54 [0.48, 0.60]
  hotpot_rank|Haiku-4.5|bm25               n=200  0.34 [0.28, 0.41] | 0.43 [0.37, 0.50]
  hotpot_rank|Haiku-4.5|e5                 n=200  0.42 [0.35, 0.48] | 0.53 [0.46, 0.59]
  hotpot_rank|Haiku-4.5|full               n=200  0.61 [0.54, 0.68] | 0.77 [0.72, 0.82]
  hotpot_rank|Haiku-4.5|minilm             n=200  0.41 [0.34, 0.48] | 0.52 [0.46, 0.59]
  hotpot_rank|Haiku-4.5|mmr                n=200  0.35 [0.28, 0.41] | 0.48 [0.41, 0.54]
  hotpot_rank|Haiku-4.5|none               n=200  0.34 [0.27, 0.40] | 0.44 [0.38, 0.50]
  hotpot_rank|Haiku-4.5|rankgpt            n=200  0.61 [0.54, 0.68] | 0.77 [0.71, 0.82]
  musique_rank|DeepSeek-V4-Pro|bge         n=100  0.37 [0.28, 0.47] | 0.45 [0.36, 0.55]
  musique_rank|DeepSeek-V4-Pro|bm25        n= 99  0.28 [0.20, 0.37] | 0.32 [0.24, 0.41]
  musique_rank|DeepSeek-V4-Pro|e5          n=100  0.35 [0.26, 0.45] | 0.46 [0.37, 0.55]
  musique_rank|DeepSeek-V4-Pro|full        n=100  0.63 [0.53, 0.72] | 0.74 [0.67, 0.82]
  musique_rank|DeepSeek-V4-Pro|minilm      n=100  0.41 [0.31, 0.50] | 0.50 [0.41, 0.59]
  musique_rank|DeepSeek-V4-Pro|mmr         n=100  0.25 [0.17, 0.34] | 0.35 [0.27, 0.44]
  musique_rank|DeepSeek-V4-Pro|none        n=100  0.22 [0.14, 0.30] | 0.35 [0.27, 0.44]
  musique_rank|DeepSeek-V4-Pro|rankgpt     n=100  0.65 [0.56, 0.74] | 0.77 [0.69, 0.84]
  musique_rank|GPT-5.5|bge                 n=100  0.43 [0.34, 0.53] | 0.54 [0.45, 0.63]
  musique_rank|GPT-5.5|bm25                n=100  0.38 [0.29, 0.48] | 0.52 [0.44, 0.61]
  musique_rank|GPT-5.5|e5                  n=100  0.43 [0.33, 0.53] | 0.58 [0.49, 0.66]
  musique_rank|GPT-5.5|full                n=100  0.65 [0.56, 0.74] | 0.80 [0.73, 0.86]
  musique_rank|GPT-5.5|minilm              n=100  0.50 [0.40, 0.60] | 0.64 [0.56, 0.72]
  musique_rank|GPT-5.5|mmr                 n=100  0.41 [0.31, 0.51] | 0.54 [0.45, 0.63]
  musique_rank|GPT-5.5|none                n=100  0.28 [0.19, 0.37] | 0.47 [0.39, 0.55]
  musique_rank|GPT-5.5|rankgpt             n=100  0.65 [0.56, 0.74] | 0.82 [0.76, 0.88]
  musique_rank|Haiku-4.5|bge               n=100  0.31 [0.22, 0.40] | 0.37 [0.29, 0.47]
  musique_rank|Haiku-4.5|bm25              n=100  0.16 [0.09, 0.23] | 0.22 [0.15, 0.30]
  musique_rank|Haiku-4.5|e5                n=100  0.28 [0.19, 0.37] | 0.38 [0.30, 0.47]
  musique_rank|Haiku-4.5|full              n=100  0.59 [0.49, 0.69] | 0.71 [0.63, 0.78]
  musique_rank|Haiku-4.5|minilm            n=100  0.28 [0.19, 0.37] | 0.37 [0.29, 0.46]
  musique_rank|Haiku-4.5|mmr               n=100  0.14 [0.08, 0.21] | 0.21 [0.14, 0.29]
  musique_rank|Haiku-4.5|none              n=100  0.13 [0.07, 0.20] | 0.25 [0.18, 0.32]
  musique_rank|Haiku-4.5|rankgpt           n=100  0.50 [0.40, 0.60] | 0.65 [0.57, 0.73]

PRIMARY: RankGPT minus each ranker, F1 (estimate [simultaneous 95%, 15 per dataset])
  hotpot_rank|Haiku-4.5|rankgpt-bm25       n=200  0.33 [0.24, 0.43] RankGPT better
  hotpot_rank|Haiku-4.5|rankgpt-mmr        n=200  0.29 [0.19, 0.39] RankGPT better
  hotpot_rank|Haiku-4.5|rankgpt-bge        n=200  0.23 [0.14, 0.31] RankGPT better
  hotpot_rank|Haiku-4.5|rankgpt-e5         n=200  0.24 [0.15, 0.34] RankGPT better
  hotpot_rank|Haiku-4.5|rankgpt-minilm     n=200  0.24 [0.15, 0.34] RankGPT better
  hotpot_rank|GPT-5.5|rankgpt-bm25         n=199  0.08 [0.03, 0.14] RankGPT better
  hotpot_rank|GPT-5.5|rankgpt-mmr          n=199  0.09 [0.03, 0.15] RankGPT better
  hotpot_rank|GPT-5.5|rankgpt-bge          n=199  0.04 [0.00, 0.08] RankGPT better
  hotpot_rank|GPT-5.5|rankgpt-e5           n=199  0.07 [0.02, 0.12] RankGPT better
  hotpot_rank|GPT-5.5|rankgpt-minilm       n=199  0.06 [0.02, 0.11] RankGPT better
  hotpot_rank|DeepSeek-V4-Pro|rankgpt-bm25 n=200  0.27 [0.18, 0.37] RankGPT better
  hotpot_rank|DeepSeek-V4-Pro|rankgpt-mmr  n=200  0.22 [0.14, 0.32] RankGPT better
  hotpot_rank|DeepSeek-V4-Pro|rankgpt-bge  n=199  0.16 [0.08, 0.25] RankGPT better
  hotpot_rank|DeepSeek-V4-Pro|rankgpt-e5   n=200  0.17 [0.09, 0.27] RankGPT better
  hotpot_rank|DeepSeek-V4-Pro|rankgpt-minilm n=200  0.18 [0.10, 0.28] RankGPT better
  musique_rank|Haiku-4.5|rankgpt-bm25      n=100  0.43 [0.29, 0.58] RankGPT better
  musique_rank|Haiku-4.5|rankgpt-mmr       n=100  0.44 [0.30, 0.59] RankGPT better
  musique_rank|Haiku-4.5|rankgpt-bge       n=100  0.28 [0.13, 0.42] RankGPT better
  musique_rank|Haiku-4.5|rankgpt-e5        n=100  0.27 [0.13, 0.41] RankGPT better
  musique_rank|Haiku-4.5|rankgpt-minilm    n=100  0.28 [0.14, 0.44] RankGPT better
  musique_rank|GPT-5.5|rankgpt-bm25        n=100  0.29 [0.17, 0.42] RankGPT better
  musique_rank|GPT-5.5|rankgpt-mmr         n=100  0.28 [0.16, 0.39] RankGPT better
  musique_rank|GPT-5.5|rankgpt-bge         n=100  0.28 [0.16, 0.40] RankGPT better
  musique_rank|GPT-5.5|rankgpt-e5          n=100  0.24 [0.12, 0.36] RankGPT better
  musique_rank|GPT-5.5|rankgpt-minilm      n=100  0.18 [0.08, 0.30] RankGPT better
  musique_rank|DeepSeek-V4-Pro|rankgpt-bm25 n= 99  0.45 [0.29, 0.61] RankGPT better
  musique_rank|DeepSeek-V4-Pro|rankgpt-mmr n=100  0.41 [0.27, 0.56] RankGPT better
  musique_rank|DeepSeek-V4-Pro|rankgpt-bge n=100  0.32 [0.19, 0.45] RankGPT better
  musique_rank|DeepSeek-V4-Pro|rankgpt-e5  n=100  0.31 [0.18, 0.44] RankGPT better
  musique_rank|DeepSeek-V4-Pro|rankgpt-minilm n=100  0.26 [0.12, 0.40] RankGPT better

AUGMENTATION (estimate [simultaneous 95%, 6 per metric]); negative = harm
  Haiku-4.5|gold+dist - gold|em            n=100  -0.01 [-0.08, 0.06] 
  Haiku-4.5|gold+dist - gold|f1            n=100  0.02 [-0.02, 0.07] 
  Haiku-4.5|dist+gold - gold|em            n=100  0.00 [-0.07, 0.07] 
  Haiku-4.5|dist+gold - gold|f1            n=100  0.01 [-0.05, 0.07] 
  GPT-5.5|gold+dist - gold|em              n= 98  -0.02 [-0.08, 0.03] 
  GPT-5.5|gold+dist - gold|f1              n= 98  -0.02 [-0.06, 0.02] 
  GPT-5.5|dist+gold - gold|em              n= 98  -0.03 [-0.09, 0.03] 
  GPT-5.5|dist+gold - gold|f1              n= 98  -0.03 [-0.08, 0.01] 
  DeepSeek-V4-Pro|gold+dist - gold|em      n= 98  0.00 [-0.08, 0.07] 
  DeepSeek-V4-Pro|gold+dist - gold|f1      n= 98  -0.01 [-0.06, 0.03] 
  DeepSeek-V4-Pro|dist+gold - gold|em      n= 99  0.00 [-0.08, 0.08] 
  DeepSeek-V4-Pro|dist+gold - gold|f1      n= 99  -0.01 [-0.06, 0.04] 

OVERHEAD: latency s | input tok | output tok | extra attempts | complete parses | top-K agreement | Kendall tau | support recall
  Haiku-4.5|5      1.3 [1.3, 1.3] | 838 [784, 890] | 22 [22, 22] | 0 | 40/40 | 0.99 [0.96, 1.00] | 0.79 [0.75, 0.83] | 0.97 [0.93, 1.00]
  Haiku-4.5|10     1.5 [1.4, 1.5] | 1448 [1365, 1541] | 42 [42, 42] | 0 | 40/40 | 0.95 [0.88, 1.00] | 0.67 [0.58, 0.74] | 0.87 [0.80, 0.93]
  Haiku-4.5|20     1.7 [1.6, 1.8] | 2789 [2653, 2933] | 82 [82, 82] | 0 | 40/40 | 0.92 [0.84, 0.98] | 0.55 [0.47, 0.62] | 0.79 [0.72, 0.86]
  GPT-5.5|5        5.2 [4.8, 5.7] | 742 [695, 788] | 363 [329, 397] | 0 | 40/40 | 1.00 [1.00, 1.00] | 0.91 [0.82, 0.98] | 0.97 [0.94, 1.00]
  GPT-5.5|10       7.8 [7.1, 8.6] | 1291 [1212, 1374] | 583 [519, 661] | 0 | 40/40 | 1.00 [1.00, 1.00] | 0.81 [0.74, 0.87] | 0.91 [0.85, 0.96]
  GPT-5.5|20       10.7 [9.2, 12.3] | 2484 [2359, 2613] | 860 [735, 993] | 0 | 40/40 | 0.93 [0.86, 1.00] | 0.74 [0.67, 0.80] | 0.88 [0.81, 0.94]

Answer-line compliance: DeepSeek-V4-Pro 2793/2795; Haiku-4.5 2800/2800; GPT-5.5 2785/2792
