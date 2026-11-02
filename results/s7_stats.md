# S7 stats: val

Measured, pointwise jev, tau = 7, n = 800 prompts per model.

| Model | judged | failed answer | dropped | mean score | median | pass rate |
|---|---:|---:|---:|---:|---:|---:|
| claude-sonnet-5-5 | 797 | 1 | 2 | 7.31 | 7.68 | 0.662 |
| deepseek-v4-flash | 798 | 0 | 2 | 7.30 | 7.66 | 0.654 |
| gemini-2.5-flash-lite | 798 | 0 | 2 | 6.81 | 7.11 | 0.535 |
| gpt-5.6-luna | 798 | 0 | 2 | 7.19 | 7.58 | 0.615 |

Pass rate counts a failed answer as a fail.
Repeat check n = 160: mean gap 0.119, within 1 point 1.000.
