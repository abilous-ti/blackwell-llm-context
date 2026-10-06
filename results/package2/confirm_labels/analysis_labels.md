requests: scheduled 2880, received 2880, graded 2880, transport failures 0

PRIMARY: own-source accuracy vs proved cap (one-sided CP, alpha = 0.05/24 each)
model            task               own  k/n      L       cap    verified  deficiency lower bound
Haiku-4.5        inv_contract_label A     40/40   0.857   0.125  yes       delta(E_B, E_A) 0.732
Haiku-4.5        inv_sku_label      B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
Haiku-4.5        audit_code_label   A     40/40   0.857   0.333  yes       delta(E_B, E_A) 0.524
Haiku-4.5        audit_line_label   B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
Sonnet-4.6       inv_contract_label A     40/40   0.857   0.125  yes       delta(E_B, E_A) 0.732
Sonnet-4.6       inv_sku_label      B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
Sonnet-4.6       audit_code_label   A     40/40   0.857   0.333  yes       delta(E_B, E_A) 0.524
Sonnet-4.6       audit_line_label   B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
Opus-4.8         inv_contract_label A     40/40   0.857   0.125  yes       delta(E_B, E_A) 0.732
Opus-4.8         inv_sku_label      B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
Opus-4.8         audit_code_label   A     40/40   0.857   0.333  yes       delta(E_B, E_A) 0.524
Opus-4.8         audit_line_label   B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
GPT-5.5          inv_contract_label A     40/40   0.857   0.125  yes       delta(E_B, E_A) 0.732
GPT-5.5          inv_sku_label      B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
GPT-5.5          audit_code_label   A     40/40   0.857   0.333  yes       delta(E_B, E_A) 0.524
GPT-5.5          audit_line_label   B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
DeepSeek-V4-Pro  inv_contract_label A     40/40   0.857   0.125  yes       delta(E_B, E_A) 0.732
DeepSeek-V4-Pro  inv_sku_label      B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
DeepSeek-V4-Pro  audit_code_label   A     40/40   0.857   0.333  yes       delta(E_B, E_A) 0.524
DeepSeek-V4-Pro  audit_line_label   B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
Kimi-K2.6        inv_contract_label A     40/40   0.857   0.125  yes       delta(E_B, E_A) 0.732
Kimi-K2.6        inv_sku_label      B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
Kimi-K2.6        audit_code_label   A     40/40   0.857   0.333  yes       delta(E_B, E_A) 0.524
Kimi-K2.6        audit_line_label   B     40/40   0.857   0.125  yes       delta(E_A, E_B) 0.732
statements verified: 24 of 24; unchanged with missing outcomes counted as incorrect: 24 of 24
pair-model combinations certified incomparable: 12 of 12

DIAGNOSTICS (one-sided CP at 0.05/48; FLAG = lower bound above the cap)
  Haiku-4.5        inv_contract_label none   4/40   L=0.011 cap=0.125 
  Haiku-4.5        inv_contract_label B      6/40   L=0.029 cap=0.125 
  Haiku-4.5        inv_sku_label      none   3/40   L=0.005 cap=0.125 
  Haiku-4.5        inv_sku_label      A      1/40   L=0.000 cap=0.125 
  Haiku-4.5        audit_code_label   none   4/40   L=0.011 cap=0.333 
  Haiku-4.5        audit_code_label   B      9/40   L=0.066 cap=0.333 
  Haiku-4.5        audit_line_label   none   2/40   L=0.001 cap=0.125 
  Haiku-4.5        audit_line_label   A      2/40   L=0.001 cap=0.125 
  Sonnet-4.6       inv_contract_label none   2/40   L=0.001 cap=0.125 
  Sonnet-4.6       inv_contract_label B     10/40   L=0.081 cap=0.125 
  Sonnet-4.6       inv_sku_label      none   4/40   L=0.011 cap=0.125 
  Sonnet-4.6       inv_sku_label      A      5/40   L=0.019 cap=0.125 
  Sonnet-4.6       audit_code_label   none  17/40   L=0.201 cap=0.333 
  Sonnet-4.6       audit_code_label   B     17/40   L=0.201 cap=0.333 
  Sonnet-4.6       audit_line_label   none   7/40   L=0.041 cap=0.125 
  Sonnet-4.6       audit_line_label   A      4/40   L=0.011 cap=0.125 
  Opus-4.8         inv_contract_label none   6/40   L=0.029 cap=0.125 
  Opus-4.8         inv_contract_label B      6/40   L=0.029 cap=0.125 
  Opus-4.8         inv_sku_label      none   4/40   L=0.011 cap=0.125 
  Opus-4.8         inv_sku_label      A      4/40   L=0.011 cap=0.125 
  Opus-4.8         audit_code_label   none  14/40   L=0.146 cap=0.333 
  Opus-4.8         audit_code_label   B     16/40   L=0.182 cap=0.333 
  Opus-4.8         audit_line_label   none   1/40   L=0.000 cap=0.125 
  Opus-4.8         audit_line_label   A      2/40   L=0.001 cap=0.125 
  GPT-5.5          inv_contract_label none   3/40   L=0.005 cap=0.125 
  GPT-5.5          inv_contract_label B      3/40   L=0.005 cap=0.125 
  GPT-5.5          inv_sku_label      none   4/40   L=0.011 cap=0.125 
  GPT-5.5          inv_sku_label      A      4/40   L=0.011 cap=0.125 
  GPT-5.5          audit_code_label   none  14/40   L=0.146 cap=0.333 
  GPT-5.5          audit_code_label   B     13/40   L=0.128 cap=0.333 
  GPT-5.5          audit_line_label   none   4/40   L=0.011 cap=0.125 
  GPT-5.5          audit_line_label   A      6/40   L=0.029 cap=0.125 
  DeepSeek-V4-Pro  inv_contract_label none   4/40   L=0.011 cap=0.125 
  DeepSeek-V4-Pro  inv_contract_label B      3/40   L=0.005 cap=0.125 
  DeepSeek-V4-Pro  inv_sku_label      none   3/40   L=0.005 cap=0.125 
  DeepSeek-V4-Pro  inv_sku_label      A      3/40   L=0.005 cap=0.125 
  DeepSeek-V4-Pro  audit_code_label   none  15/40   L=0.163 cap=0.333 
  DeepSeek-V4-Pro  audit_code_label   B     11/40   L=0.096 cap=0.333 
  DeepSeek-V4-Pro  audit_line_label   none   4/40   L=0.011 cap=0.125 
  DeepSeek-V4-Pro  audit_line_label   A      5/40   L=0.019 cap=0.125 
  Kimi-K2.6        inv_contract_label none   3/40   L=0.005 cap=0.125 
  Kimi-K2.6        inv_contract_label B      3/40   L=0.005 cap=0.125 
  Kimi-K2.6        inv_sku_label      none   1/40   L=0.000 cap=0.125 
  Kimi-K2.6        inv_sku_label      A      0/40   L=0.000 cap=0.125 
  Kimi-K2.6        audit_code_label   none   6/40   L=0.029 cap=0.333 
  Kimi-K2.6        audit_code_label   B      1/40   L=0.000 cap=0.333 
  Kimi-K2.6        audit_line_label   none   3/40   L=0.005 cap=0.125 
  Kimi-K2.6        audit_line_label   A      4/40   L=0.011 cap=0.125 
flags: 0

SECONDARY: own minus other-source accuracy (block differences, Hoeffding, alpha = 0.05/24)
  Haiku-4.5        inv_contract_label B= 40 +0.85 bound +0.29 verified
  Haiku-4.5        inv_sku_label      B= 40 +0.97 bound +0.42 verified
  Haiku-4.5        audit_code_label   B= 40 +0.78 bound +0.22 verified
  Haiku-4.5        audit_line_label   B= 40 +0.95 bound +0.39 verified
  Sonnet-4.6       inv_contract_label B= 40 +0.75 bound +0.19 verified
  Sonnet-4.6       inv_sku_label      B= 40 +0.88 bound +0.32 verified
  Sonnet-4.6       audit_code_label   B= 40 +0.57 bound +0.02 verified
  Sonnet-4.6       audit_line_label   B= 40 +0.90 bound +0.34 verified
  Opus-4.8         inv_contract_label B= 40 +0.85 bound +0.29 verified
  Opus-4.8         inv_sku_label      B= 40 +0.90 bound +0.34 verified
  Opus-4.8         audit_code_label   B= 40 +0.60 bound +0.04 verified
  Opus-4.8         audit_line_label   B= 40 +0.95 bound +0.39 verified
  GPT-5.5          inv_contract_label B= 40 +0.93 bound +0.37 verified
  GPT-5.5          inv_sku_label      B= 40 +0.90 bound +0.34 verified
  GPT-5.5          audit_code_label   B= 40 +0.68 bound +0.12 verified
  GPT-5.5          audit_line_label   B= 40 +0.85 bound +0.29 verified
  DeepSeek-V4-Pro  inv_contract_label B= 40 +0.93 bound +0.37 verified
  DeepSeek-V4-Pro  inv_sku_label      B= 40 +0.93 bound +0.37 verified
  DeepSeek-V4-Pro  audit_code_label   B= 40 +0.72 bound +0.17 verified
  DeepSeek-V4-Pro  audit_line_label   B= 40 +0.88 bound +0.32 verified
  Kimi-K2.6        inv_contract_label B= 40 +0.93 bound +0.37 verified
  Kimi-K2.6        inv_sku_label      B= 40 +1.00 bound +0.44 verified
  Kimi-K2.6        audit_code_label   B= 40 +0.97 bound +0.42 verified
  Kimi-K2.6        audit_line_label   B= 40 +0.90 bound +0.34 verified

DESCRIPTIVE: own-source accuracy per hidden state (no simultaneous coverage)
  DeepSeek-V4-Pro  audit_code_label   table=t1                                 14/14
  DeepSeek-V4-Pro  audit_code_label   table=t2                                 13/13
  DeepSeek-V4-Pro  audit_code_label   table=t3                                 13/13
  DeepSeek-V4-Pro  audit_line_label   epoch=hex|sep=^|user=lower               4/4
  DeepSeek-V4-Pro  audit_line_label   epoch=hex|sep=^|user=upper               3/3
  DeepSeek-V4-Pro  audit_line_label   epoch=hex|sep=~|user=lower               5/5
  DeepSeek-V4-Pro  audit_line_label   epoch=hex|sep=~|user=upper               4/4
  DeepSeek-V4-Pro  audit_line_label   epoch=oct|sep=^|user=lower               5/5
  DeepSeek-V4-Pro  audit_line_label   epoch=oct|sep=^|user=upper               10/10
  DeepSeek-V4-Pro  audit_line_label   epoch=oct|sep=~|user=lower               6/6
  DeepSeek-V4-Pro  audit_line_label   epoch=oct|sep=~|user=upper               3/3
  DeepSeek-V4-Pro  inv_contract_label exc=ReserveError|kw=hold|order=qty_first 5/5
  DeepSeek-V4-Pro  inv_contract_label exc=ReserveError|kw=hold|order=sku_first 6/6
  DeepSeek-V4-Pro  inv_contract_label exc=ReserveError|kw=lease|order=qty_first 7/7
  DeepSeek-V4-Pro  inv_contract_label exc=ReserveError|kw=lease|order=sku_first 3/3
  DeepSeek-V4-Pro  inv_contract_label exc=StockError|kw=hold|order=qty_first   1/1
  DeepSeek-V4-Pro  inv_contract_label exc=StockError|kw=hold|order=sku_first   4/4
  DeepSeek-V4-Pro  inv_contract_label exc=StockError|kw=lease|order=qty_first  3/3
  DeepSeek-V4-Pro  inv_contract_label exc=StockError|kw=lease|order=sku_first  11/11
  DeepSeek-V4-Pro  inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=5   3/3
  DeepSeek-V4-Pro  inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=6   2/2
  DeepSeek-V4-Pro  inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=5   8/8
  DeepSeek-V4-Pro  inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=6   4/4
  DeepSeek-V4-Pro  inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=5 7/7
  DeepSeek-V4-Pro  inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=6 3/3
  DeepSeek-V4-Pro  inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=5 8/8
  DeepSeek-V4-Pro  inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=6 5/5
  GPT-5.5          audit_code_label   table=t1                                 12/12
  GPT-5.5          audit_code_label   table=t2                                 12/12
  GPT-5.5          audit_code_label   table=t3                                 16/16
  GPT-5.5          audit_line_label   epoch=hex|sep=^|user=lower               4/4
  GPT-5.5          audit_line_label   epoch=hex|sep=^|user=upper               6/6
  GPT-5.5          audit_line_label   epoch=hex|sep=~|user=lower               6/6
  GPT-5.5          audit_line_label   epoch=hex|sep=~|user=upper               4/4
  GPT-5.5          audit_line_label   epoch=oct|sep=^|user=lower               4/4
  GPT-5.5          audit_line_label   epoch=oct|sep=^|user=upper               6/6
  GPT-5.5          audit_line_label   epoch=oct|sep=~|user=lower               2/2
  GPT-5.5          audit_line_label   epoch=oct|sep=~|user=upper               8/8
  GPT-5.5          inv_contract_label exc=ReserveError|kw=hold|order=qty_first 7/7
  GPT-5.5          inv_contract_label exc=ReserveError|kw=hold|order=sku_first 2/2
  GPT-5.5          inv_contract_label exc=ReserveError|kw=lease|order=qty_first 2/2
  GPT-5.5          inv_contract_label exc=ReserveError|kw=lease|order=sku_first 7/7
  GPT-5.5          inv_contract_label exc=StockError|kw=hold|order=qty_first   6/6
  GPT-5.5          inv_contract_label exc=StockError|kw=hold|order=sku_first   3/3
  GPT-5.5          inv_contract_label exc=StockError|kw=lease|order=qty_first  9/9
  GPT-5.5          inv_contract_label exc=StockError|kw=lease|order=sku_first  4/4
  GPT-5.5          inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=5   2/2
  GPT-5.5          inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=6   12/12
  GPT-5.5          inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=5   2/2
  GPT-5.5          inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=6   5/5
  GPT-5.5          inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=5 4/4
  GPT-5.5          inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=6 9/9
  GPT-5.5          inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=5 5/5
  GPT-5.5          inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=6 1/1
  Haiku-4.5        audit_code_label   table=t1                                 17/17
  Haiku-4.5        audit_code_label   table=t2                                 8/8
  Haiku-4.5        audit_code_label   table=t3                                 15/15
  Haiku-4.5        audit_line_label   epoch=hex|sep=^|user=lower               7/7
  Haiku-4.5        audit_line_label   epoch=hex|sep=^|user=upper               7/7
  Haiku-4.5        audit_line_label   epoch=hex|sep=~|user=lower               7/7
  Haiku-4.5        audit_line_label   epoch=hex|sep=~|user=upper               2/2
  Haiku-4.5        audit_line_label   epoch=oct|sep=^|user=lower               2/2
  Haiku-4.5        audit_line_label   epoch=oct|sep=^|user=upper               5/5
  Haiku-4.5        audit_line_label   epoch=oct|sep=~|user=lower               7/7
  Haiku-4.5        audit_line_label   epoch=oct|sep=~|user=upper               3/3
  Haiku-4.5        inv_contract_label exc=ReserveError|kw=hold|order=qty_first 7/7
  Haiku-4.5        inv_contract_label exc=ReserveError|kw=hold|order=sku_first 7/7
  Haiku-4.5        inv_contract_label exc=ReserveError|kw=lease|order=qty_first 5/5
  Haiku-4.5        inv_contract_label exc=ReserveError|kw=lease|order=sku_first 5/5
  Haiku-4.5        inv_contract_label exc=StockError|kw=hold|order=qty_first   3/3
  Haiku-4.5        inv_contract_label exc=StockError|kw=hold|order=sku_first   5/5
  Haiku-4.5        inv_contract_label exc=StockError|kw=lease|order=qty_first  4/4
  Haiku-4.5        inv_contract_label exc=StockError|kw=lease|order=sku_first  4/4
  Haiku-4.5        inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=5   1/1
  Haiku-4.5        inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=6   3/3
  Haiku-4.5        inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=5   10/10
  Haiku-4.5        inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=6   9/9
  Haiku-4.5        inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=5 3/3
  Haiku-4.5        inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=6 1/1
  Haiku-4.5        inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=5 4/4
  Haiku-4.5        inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=6 9/9
  Kimi-K2.6        audit_code_label   table=t1                                 10/10
  Kimi-K2.6        audit_code_label   table=t2                                 20/20
  Kimi-K2.6        audit_code_label   table=t3                                 10/10
  Kimi-K2.6        audit_line_label   epoch=hex|sep=^|user=lower               5/5
  Kimi-K2.6        audit_line_label   epoch=hex|sep=^|user=upper               2/2
  Kimi-K2.6        audit_line_label   epoch=hex|sep=~|user=lower               4/4
  Kimi-K2.6        audit_line_label   epoch=hex|sep=~|user=upper               4/4
  Kimi-K2.6        audit_line_label   epoch=oct|sep=^|user=lower               7/7
  Kimi-K2.6        audit_line_label   epoch=oct|sep=^|user=upper               7/7
  Kimi-K2.6        audit_line_label   epoch=oct|sep=~|user=lower               6/6
  Kimi-K2.6        audit_line_label   epoch=oct|sep=~|user=upper               5/5
  Kimi-K2.6        inv_contract_label exc=ReserveError|kw=hold|order=qty_first 3/3
  Kimi-K2.6        inv_contract_label exc=ReserveError|kw=hold|order=sku_first 3/3
  Kimi-K2.6        inv_contract_label exc=ReserveError|kw=lease|order=qty_first 3/3
  Kimi-K2.6        inv_contract_label exc=ReserveError|kw=lease|order=sku_first 9/9
  Kimi-K2.6        inv_contract_label exc=StockError|kw=hold|order=qty_first   7/7
  Kimi-K2.6        inv_contract_label exc=StockError|kw=hold|order=sku_first   5/5
  Kimi-K2.6        inv_contract_label exc=StockError|kw=lease|order=qty_first  6/6
  Kimi-K2.6        inv_contract_label exc=StockError|kw=lease|order=sku_first  4/4
  Kimi-K2.6        inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=5   6/6
  Kimi-K2.6        inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=6   2/2
  Kimi-K2.6        inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=5   5/5
  Kimi-K2.6        inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=6   3/3
  Kimi-K2.6        inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=5 7/7
  Kimi-K2.6        inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=6 5/5
  Kimi-K2.6        inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=5 6/6
  Kimi-K2.6        inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=6 6/6
  Opus-4.8         audit_code_label   table=t1                                 14/14
  Opus-4.8         audit_code_label   table=t2                                 14/14
  Opus-4.8         audit_code_label   table=t3                                 12/12
  Opus-4.8         audit_line_label   epoch=hex|sep=^|user=lower               1/1
  Opus-4.8         audit_line_label   epoch=hex|sep=^|user=upper               7/7
  Opus-4.8         audit_line_label   epoch=hex|sep=~|user=lower               2/2
  Opus-4.8         audit_line_label   epoch=hex|sep=~|user=upper               6/6
  Opus-4.8         audit_line_label   epoch=oct|sep=^|user=lower               8/8
  Opus-4.8         audit_line_label   epoch=oct|sep=^|user=upper               8/8
  Opus-4.8         audit_line_label   epoch=oct|sep=~|user=lower               5/5
  Opus-4.8         audit_line_label   epoch=oct|sep=~|user=upper               3/3
  Opus-4.8         inv_contract_label exc=ReserveError|kw=hold|order=qty_first 5/5
  Opus-4.8         inv_contract_label exc=ReserveError|kw=hold|order=sku_first 5/5
  Opus-4.8         inv_contract_label exc=ReserveError|kw=lease|order=qty_first 3/3
  Opus-4.8         inv_contract_label exc=ReserveError|kw=lease|order=sku_first 3/3
  Opus-4.8         inv_contract_label exc=StockError|kw=hold|order=qty_first   8/8
  Opus-4.8         inv_contract_label exc=StockError|kw=hold|order=sku_first   6/6
  Opus-4.8         inv_contract_label exc=StockError|kw=lease|order=qty_first  4/4
  Opus-4.8         inv_contract_label exc=StockError|kw=lease|order=sku_first  6/6
  Opus-4.8         inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=5   10/10
  Opus-4.8         inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=6   5/5
  Opus-4.8         inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=5   4/4
  Opus-4.8         inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=6   4/4
  Opus-4.8         inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=5 3/3
  Opus-4.8         inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=6 2/2
  Opus-4.8         inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=5 7/7
  Opus-4.8         inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=6 5/5
  Sonnet-4.6       audit_code_label   table=t1                                 14/14
  Sonnet-4.6       audit_code_label   table=t2                                 17/17
  Sonnet-4.6       audit_code_label   table=t3                                 9/9
  Sonnet-4.6       audit_line_label   epoch=hex|sep=^|user=lower               6/6
  Sonnet-4.6       audit_line_label   epoch=hex|sep=^|user=upper               3/3
  Sonnet-4.6       audit_line_label   epoch=hex|sep=~|user=lower               5/5
  Sonnet-4.6       audit_line_label   epoch=hex|sep=~|user=upper               6/6
  Sonnet-4.6       audit_line_label   epoch=oct|sep=^|user=lower               6/6
  Sonnet-4.6       audit_line_label   epoch=oct|sep=^|user=upper               8/8
  Sonnet-4.6       audit_line_label   epoch=oct|sep=~|user=lower               3/3
  Sonnet-4.6       audit_line_label   epoch=oct|sep=~|user=upper               3/3
  Sonnet-4.6       inv_contract_label exc=ReserveError|kw=hold|order=sku_first 4/4
  Sonnet-4.6       inv_contract_label exc=ReserveError|kw=lease|order=qty_first 5/5
  Sonnet-4.6       inv_contract_label exc=ReserveError|kw=lease|order=sku_first 5/5
  Sonnet-4.6       inv_contract_label exc=StockError|kw=hold|order=qty_first   8/8
  Sonnet-4.6       inv_contract_label exc=StockError|kw=hold|order=sku_first   7/7
  Sonnet-4.6       inv_contract_label exc=StockError|kw=lease|order=qty_first  6/6
  Sonnet-4.6       inv_contract_label exc=StockError|kw=lease|order=sku_first  5/5
  Sonnet-4.6       inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=5   7/7
  Sonnet-4.6       inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=6   3/3
  Sonnet-4.6       inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=5   7/7
  Sonnet-4.6       inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=6   5/5
  Sonnet-4.6       inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=5 3/3
  Sonnet-4.6       inv_sku_label      check=mod9:ABCDEFGHJ|prefix=iv9.|width=6 4/4
  Sonnet-4.6       inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=5 5/5
  Sonnet-4.6       inv_sku_label      check=mod9:ABCDEFGHJ|prefix=sk4-|width=6 6/6
DESCRIPTIVE: choices without context
  DeepSeek-V4-Pro  audit_code_label   {'1': 33, '2': 6, '3': 1}
  DeepSeek-V4-Pro  audit_line_label   {'1': 24, '3': 10, '4': 2, '5': 1, '6': 1, '7': 2}
  DeepSeek-V4-Pro  inv_contract_label {'1': 1, '2': 3, '5': 12, '6': 24}
  DeepSeek-V4-Pro  inv_sku_label      {'1': 23, '2': 3, '3': 9, '4': 5}
  GPT-5.5          audit_code_label   {'2': 38, '3': 2}
  GPT-5.5          audit_line_label   {'1': 16, '3': 24}
  GPT-5.5          inv_contract_label {'5': 40}
  GPT-5.5          inv_sku_label      {'1': 6, '2': 1, '5': 7, '6': 2, '7': 17, '8': 7}
  Haiku-4.5        audit_code_label   {'1': 12, '2': 19, 'None': 9}
  Haiku-4.5        audit_line_label   {'1': 40}
  Haiku-4.5        inv_contract_label {'1': 5, '2': 4, '5': 13, '6': 16, '7': 1, '8': 1}
  Haiku-4.5        inv_sku_label      {'1': 1, '2': 7, '4': 25, '8': 6, 'None': 1}
  Kimi-K2.6        audit_code_label   {'1': 20, '2': 3, 'None': 17}
  Kimi-K2.6        audit_line_label   {'1': 7, '3': 31, 'None': 2}
  Kimi-K2.6        inv_contract_label {'5': 33, 'None': 7}
  Kimi-K2.6        inv_sku_label      {'1': 3, 'None': 37}
  Opus-4.8         audit_code_label   {'1': 28, '2': 12}
  Opus-4.8         audit_line_label   {'1': 5, '3': 34, '7': 1}
  Opus-4.8         inv_contract_label {'5': 39, '6': 1}
  Opus-4.8         inv_sku_label      {'1': 3, '4': 8, '6': 2, '7': 6, '8': 21}
  Sonnet-4.6       audit_code_label   {'2': 40}
  Sonnet-4.6       audit_line_label   {'1': 34, '3': 3, '5': 2, '7': 1}
  Sonnet-4.6       inv_contract_label {'5': 16, '7': 17, '8': 7}
  Sonnet-4.6       inv_sku_label      {'1': 5, '3': 2, '4': 2, '7': 24, '8': 7}
invalid replies: Haiku-4.5 other/none 13; Kimi-K2.6 other/none 156
