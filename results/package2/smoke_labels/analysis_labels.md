requests: scheduled 72, received 72, graded 72, transport failures 0

PRIMARY: own-source accuracy vs proved cap (one-sided CP, alpha = 0.05/24 each)
model            task               own  k/n      L       cap    verified  deficiency lower bound
Haiku-4.5        inv_contract_label A      1/1    0.002   0.125  no        delta(E_B, E_A) 0.000
Haiku-4.5        inv_sku_label      B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
Haiku-4.5        audit_code_label   A      1/1    0.002   0.333  no        delta(E_B, E_A) 0.000
Haiku-4.5        audit_line_label   B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
Sonnet-4.6       inv_contract_label A      1/1    0.002   0.125  no        delta(E_B, E_A) 0.000
Sonnet-4.6       inv_sku_label      B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
Sonnet-4.6       audit_code_label   A      1/1    0.002   0.333  no        delta(E_B, E_A) 0.000
Sonnet-4.6       audit_line_label   B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
Opus-4.8         inv_contract_label A      1/1    0.002   0.125  no        delta(E_B, E_A) 0.000
Opus-4.8         inv_sku_label      B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
Opus-4.8         audit_code_label   A      1/1    0.002   0.333  no        delta(E_B, E_A) 0.000
Opus-4.8         audit_line_label   B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
GPT-5.5          inv_contract_label A      1/1    0.002   0.125  no        delta(E_B, E_A) 0.000
GPT-5.5          inv_sku_label      B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
GPT-5.5          audit_code_label   A      1/1    0.002   0.333  no        delta(E_B, E_A) 0.000
GPT-5.5          audit_line_label   B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
DeepSeek-V4-Pro  inv_contract_label A      1/1    0.002   0.125  no        delta(E_B, E_A) 0.000
DeepSeek-V4-Pro  inv_sku_label      B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
DeepSeek-V4-Pro  audit_code_label   A      1/1    0.002   0.333  no        delta(E_B, E_A) 0.000
DeepSeek-V4-Pro  audit_line_label   B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
Kimi-K2.6        inv_contract_label A      1/1    0.002   0.125  no        delta(E_B, E_A) 0.000
Kimi-K2.6        inv_sku_label      B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
Kimi-K2.6        audit_code_label   A      1/1    0.002   0.333  no        delta(E_B, E_A) 0.000
Kimi-K2.6        audit_line_label   B      1/1    0.002   0.125  no        delta(E_A, E_B) 0.000
statements verified: 0 of 24; unchanged with missing outcomes counted as incorrect: 24 of 24
pair-model combinations certified incomparable: 0 of 12

DIAGNOSTICS (one-sided CP at 0.05/48; FLAG = lower bound above the cap)
  Haiku-4.5        inv_contract_label none   0/1    L=0.000 cap=0.125 
  Haiku-4.5        inv_contract_label B      0/1    L=0.000 cap=0.125 
  Haiku-4.5        inv_sku_label      none   0/1    L=0.000 cap=0.125 
  Haiku-4.5        inv_sku_label      A      0/1    L=0.000 cap=0.125 
  Haiku-4.5        audit_code_label   none   0/1    L=0.000 cap=0.333 
  Haiku-4.5        audit_code_label   B      0/1    L=0.000 cap=0.333 
  Haiku-4.5        audit_line_label   none   0/1    L=0.000 cap=0.125 
  Haiku-4.5        audit_line_label   A      0/1    L=0.000 cap=0.125 
  Sonnet-4.6       inv_contract_label none   1/1    L=0.001 cap=0.125 
  Sonnet-4.6       inv_contract_label B      0/1    L=0.000 cap=0.125 
  Sonnet-4.6       inv_sku_label      none   0/1    L=0.000 cap=0.125 
  Sonnet-4.6       inv_sku_label      A      0/1    L=0.000 cap=0.125 
  Sonnet-4.6       audit_code_label   none   1/1    L=0.001 cap=0.333 
  Sonnet-4.6       audit_code_label   B      1/1    L=0.001 cap=0.333 
  Sonnet-4.6       audit_line_label   none   0/1    L=0.000 cap=0.125 
  Sonnet-4.6       audit_line_label   A      1/1    L=0.001 cap=0.125 
  Opus-4.8         inv_contract_label none   1/1    L=0.001 cap=0.125 
  Opus-4.8         inv_contract_label B      1/1    L=0.001 cap=0.125 
  Opus-4.8         inv_sku_label      none   0/1    L=0.000 cap=0.125 
  Opus-4.8         inv_sku_label      A      0/1    L=0.000 cap=0.125 
  Opus-4.8         audit_code_label   none   0/1    L=0.000 cap=0.333 
  Opus-4.8         audit_code_label   B      0/1    L=0.000 cap=0.333 
  Opus-4.8         audit_line_label   none   0/1    L=0.000 cap=0.125 
  Opus-4.8         audit_line_label   A      0/1    L=0.000 cap=0.125 
  GPT-5.5          inv_contract_label none   0/1    L=0.000 cap=0.125 
  GPT-5.5          inv_contract_label B      0/1    L=0.000 cap=0.125 
  GPT-5.5          inv_sku_label      none   0/1    L=0.000 cap=0.125 
  GPT-5.5          inv_sku_label      A      0/1    L=0.000 cap=0.125 
  GPT-5.5          audit_code_label   none   0/1    L=0.000 cap=0.333 
  GPT-5.5          audit_code_label   B      0/1    L=0.000 cap=0.333 
  GPT-5.5          audit_line_label   none   0/1    L=0.000 cap=0.125 
  GPT-5.5          audit_line_label   A      0/1    L=0.000 cap=0.125 
  DeepSeek-V4-Pro  inv_contract_label none   0/1    L=0.000 cap=0.125 
  DeepSeek-V4-Pro  inv_contract_label B      0/1    L=0.000 cap=0.125 
  DeepSeek-V4-Pro  inv_sku_label      none   0/1    L=0.000 cap=0.125 
  DeepSeek-V4-Pro  inv_sku_label      A      0/1    L=0.000 cap=0.125 
  DeepSeek-V4-Pro  audit_code_label   none   1/1    L=0.001 cap=0.333 
  DeepSeek-V4-Pro  audit_code_label   B      0/1    L=0.000 cap=0.333 
  DeepSeek-V4-Pro  audit_line_label   none   0/1    L=0.000 cap=0.125 
  DeepSeek-V4-Pro  audit_line_label   A      0/1    L=0.000 cap=0.125 
  Kimi-K2.6        inv_contract_label none   0/1    L=0.000 cap=0.125 
  Kimi-K2.6        inv_contract_label B      0/1    L=0.000 cap=0.125 
  Kimi-K2.6        inv_sku_label      none   0/1    L=0.000 cap=0.125 
  Kimi-K2.6        inv_sku_label      A      0/1    L=0.000 cap=0.125 
  Kimi-K2.6        audit_code_label   none   0/1    L=0.000 cap=0.333 
  Kimi-K2.6        audit_code_label   B      0/1    L=0.000 cap=0.333 
  Kimi-K2.6        audit_line_label   none   0/1    L=0.000 cap=0.125 
  Kimi-K2.6        audit_line_label   A      0/1    L=0.000 cap=0.125 
flags: 0

SECONDARY: own minus other-source accuracy (block differences, Hoeffding, alpha = 0.05/24)
  Haiku-4.5        inv_contract_label B=  1 +1.00 bound -2.51 
  Haiku-4.5        inv_sku_label      B=  1 +1.00 bound -2.51 
  Haiku-4.5        audit_code_label   B=  1 +1.00 bound -2.51 
  Haiku-4.5        audit_line_label   B=  1 +1.00 bound -2.51 
  Sonnet-4.6       inv_contract_label B=  1 +1.00 bound -2.51 
  Sonnet-4.6       inv_sku_label      B=  1 +1.00 bound -2.51 
  Sonnet-4.6       audit_code_label   B=  1 +0.00 bound -3.51 
  Sonnet-4.6       audit_line_label   B=  1 +0.00 bound -3.51 
  Opus-4.8         inv_contract_label B=  1 +0.00 bound -3.51 
  Opus-4.8         inv_sku_label      B=  1 +1.00 bound -2.51 
  Opus-4.8         audit_code_label   B=  1 +1.00 bound -2.51 
  Opus-4.8         audit_line_label   B=  1 +1.00 bound -2.51 
  GPT-5.5          inv_contract_label B=  1 +1.00 bound -2.51 
  GPT-5.5          inv_sku_label      B=  1 +1.00 bound -2.51 
  GPT-5.5          audit_code_label   B=  1 +1.00 bound -2.51 
  GPT-5.5          audit_line_label   B=  1 +1.00 bound -2.51 
  DeepSeek-V4-Pro  inv_contract_label B=  1 +1.00 bound -2.51 
  DeepSeek-V4-Pro  inv_sku_label      B=  1 +1.00 bound -2.51 
  DeepSeek-V4-Pro  audit_code_label   B=  1 +1.00 bound -2.51 
  DeepSeek-V4-Pro  audit_line_label   B=  1 +1.00 bound -2.51 
  Kimi-K2.6        inv_contract_label B=  1 +1.00 bound -2.51 
  Kimi-K2.6        inv_sku_label      B=  1 +1.00 bound -2.51 
  Kimi-K2.6        audit_code_label   B=  1 +1.00 bound -2.51 
  Kimi-K2.6        audit_line_label   B=  1 +1.00 bound -2.51 

DESCRIPTIVE: own-source accuracy per hidden state (no simultaneous coverage)
  DeepSeek-V4-Pro  audit_code_label   table=t3                                 1/1
  DeepSeek-V4-Pro  audit_line_label   epoch=oct|sep=^|user=lower               1/1
  DeepSeek-V4-Pro  inv_contract_label exc=ReserveError|kw=hold|order=qty_first 1/1
  DeepSeek-V4-Pro  inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=6   1/1
  GPT-5.5          audit_code_label   table=t1                                 1/1
  GPT-5.5          audit_line_label   epoch=hex|sep=^|user=lower               1/1
  GPT-5.5          inv_contract_label exc=ReserveError|kw=lease|order=qty_first 1/1
  GPT-5.5          inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=5   1/1
  Haiku-4.5        audit_code_label   table=t3                                 1/1
  Haiku-4.5        audit_line_label   epoch=oct|sep=^|user=lower               1/1
  Haiku-4.5        inv_contract_label exc=StockError|kw=hold|order=qty_first   1/1
  Haiku-4.5        inv_sku_label      check=mod7:KMPRTWY|prefix=iv9.|width=5   1/1
  Kimi-K2.6        audit_code_label   table=t1                                 1/1
  Kimi-K2.6        audit_line_label   epoch=hex|sep=~|user=upper               1/1
  Kimi-K2.6        inv_contract_label exc=StockError|kw=lease|order=sku_first  1/1
  Kimi-K2.6        inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=6   1/1
  Opus-4.8         audit_code_label   table=t3                                 1/1
  Opus-4.8         audit_line_label   epoch=hex|sep=^|user=upper               1/1
  Opus-4.8         inv_contract_label exc=StockError|kw=hold|order=sku_first   1/1
  Opus-4.8         inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=5   1/1
  Sonnet-4.6       audit_code_label   table=t2                                 1/1
  Sonnet-4.6       audit_line_label   epoch=hex|sep=~|user=lower               1/1
  Sonnet-4.6       inv_contract_label exc=StockError|kw=lease|order=sku_first  1/1
  Sonnet-4.6       inv_sku_label      check=mod7:KMPRTWY|prefix=sk4-|width=6   1/1
DESCRIPTIVE: choices without context
  DeepSeek-V4-Pro  audit_code_label   {'3': 1}
  DeepSeek-V4-Pro  audit_line_label   {'3': 1}
  DeepSeek-V4-Pro  inv_contract_label {'6': 1}
  DeepSeek-V4-Pro  inv_sku_label      {'1': 1}
  GPT-5.5          audit_code_label   {'2': 1}
  GPT-5.5          audit_line_label   {'3': 1}
  GPT-5.5          inv_contract_label {'5': 1}
  GPT-5.5          inv_sku_label      {'6': 1}
  Haiku-4.5        audit_code_label   {'1': 1}
  Haiku-4.5        audit_line_label   {'1': 1}
  Haiku-4.5        inv_contract_label {'6': 1}
  Haiku-4.5        inv_sku_label      {'8': 1}
  Kimi-K2.6        audit_code_label   {'None': 1}
  Kimi-K2.6        audit_line_label   {'3': 1}
  Kimi-K2.6        inv_contract_label {'5': 1}
  Kimi-K2.6        inv_sku_label      {'None': 1}
  Opus-4.8         audit_code_label   {'1': 1}
  Opus-4.8         audit_line_label   {'1': 1}
  Opus-4.8         inv_contract_label {'5': 1}
  Opus-4.8         inv_sku_label      {'8': 1}
  Sonnet-4.6       audit_code_label   {'2': 1}
  Sonnet-4.6       audit_line_label   {'1': 1}
  Sonnet-4.6       inv_contract_label {'7': 1}
  Sonnet-4.6       inv_sku_label      {'4': 1}
invalid replies: Kimi-K2.6 other/none 5
