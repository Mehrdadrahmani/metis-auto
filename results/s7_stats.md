# S7 stats: val

Measured, pointwise jev, tau = 7, n = 400 prompts per model.

| Model | judged | failed answer | dropped | mean score | median | pass rate |
|---|---:|---:|---:|---:|---:|---:|
| claude-sonnet-5-5 | 398 | 1 | 1 | 7.35 | 7.71 | 0.652 |
| deepseek-v4-flash | 399 | 0 | 1 | 7.31 | 7.68 | 0.649 |
| gemini-2.5-flash-lite | 399 | 0 | 1 | 6.86 | 7.17 | 0.539 |
| gpt-5.6-luna | 399 | 0 | 1 | 7.22 | 7.55 | 0.612 |

Pass rate counts a failed answer as a fail.
Repeat check n = 80: mean gap 0.147, within 1 point 1.000.
