requests: scheduled 2880, received 2880, graded 2880, transport failures 0

AMENDED PRIMARY (A1, CP, missing = incorrect) and DRIFT-ROBUST (A2, Hoeffding); alpha = 0.05/24 each
model            task               own  k/sched cap    A1 L / ok      A2 L_H / ok    complete-case deficiency bounds A1 / A2
Haiku-4.5        inv_contract_label A    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.732 / 0.597
Haiku-4.5        inv_sku_label      B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
Haiku-4.5        audit_code_label   A    40/40   0.333  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.524 / 0.389
Haiku-4.5        audit_line_label   B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
Sonnet-4.6       inv_contract_label A    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.732 / 0.597
Sonnet-4.6       inv_sku_label      B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
Sonnet-4.6       audit_code_label   A    40/40   0.333  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.524 / 0.389
Sonnet-4.6       audit_line_label   B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
Opus-4.8         inv_contract_label A    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.732 / 0.597
Opus-4.8         inv_sku_label      B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
Opus-4.8         audit_code_label   A    40/40   0.333  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.524 / 0.389
Opus-4.8         audit_line_label   B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
GPT-5.5          inv_contract_label A    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.732 / 0.597
GPT-5.5          inv_sku_label      B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
GPT-5.5          audit_code_label   A    40/40   0.333  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.524 / 0.389
GPT-5.5          audit_line_label   B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
DeepSeek-V4-Pro  inv_contract_label A    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.732 / 0.597
DeepSeek-V4-Pro  inv_sku_label      B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
DeepSeek-V4-Pro  audit_code_label   A    40/40   0.333  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.524 / 0.389
DeepSeek-V4-Pro  audit_line_label   B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
Kimi-K2.6        inv_contract_label A    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.732 / 0.597
Kimi-K2.6        inv_sku_label      B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
Kimi-K2.6        audit_code_label   A    40/40   0.333  0.857  yes     0.722  yes     yes          delta(E_B, E_A) >= 0.524 / 0.389
Kimi-K2.6        audit_line_label   B    40/40   0.125  0.857  yes     0.722  yes     yes          delta(E_A, E_B) >= 0.732 / 0.597
statements verified: A1 24 of 24; A2 24 of 24; complete-case 24 of 24
pair-model combinations certified incomparable: A1 12 of 12; A2 12 of 12
diagnostic flags (frozen analysis, 0.05/48): 0
