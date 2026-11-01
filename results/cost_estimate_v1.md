# Cost estimate v1 (WP-06 step 10)

Assumptions: T_in = 2871 (eligible prompts (chars / 3)), T_out = 300, judge output = 150, template = 500 tokens. Metis prices, no prompt-cache discount. Instructions are not cut to 6,000 tokens here, so judge cost leans high. deepseek-v4-flash costs double in peak hours: not included. Prices are from `configs/models.yaml`; simulated from formulas, nothing measured yet.

| Item | Calls | USD |
|---|---:|---:|
| Pilot generation: deepseek-v4-flash | 100 | 0.07 |
| Pilot generation: gpt-5.6-luna | 100 | 0.10 |
| Pilot generation: gemini-2.5-flash-lite | 100 | 0.04 |
| Pilot generation: claude-sonnet-5-5 | 100 | 0.96 |
| Pilot generation: deepseek-v4-pro | 100 | 0.27 |
| Pilot pointwise: judge | 500 | 5.03 |
| Pilot pairwise: judge | 800 | 8.57 |
| Pilot pointwise: jev | 500 | 0.08 |
| Pilot pairwise: jev | 800 | 0.15 |
| Main generation: deepseek-v4-flash | 600 | 0.40 |
| Main generation: gpt-5.6-luna | 600 | 0.62 |
| Main generation: gemini-2.5-flash-lite | 600 | 0.27 |
| Main generation: claude-sonnet-5-5 | 600 | 5.77 |
| Main judging, pointwise (gpt-5.6-terra) | 2400 | 24.13 |
| Main judging, pairwise (gpt-5.6-terra) | 3600 | 38.58 |
| Re-judge 5% | 120 | 1.21 |

**Pilot with both judges: $15.28.** Main generation: $7.06.

Total, pointwise path: $47.68. Total, pairwise path: $62.12. Cap: $60.
