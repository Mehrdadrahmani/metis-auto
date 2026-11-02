# S6 stats: val

Measured, n = 400 prompts per model, pilot answers reused.
Dollars are new gen_main calls only, by ledger.

| Model | ok | failed | retried for length | mean in | mean out | p50 ms | p90 ms | new $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-sonnet-5-5 | 399 | 1 | 22 | 5046 | 443 | 5132 | 9220 | 5.1738 |
| deepseek-v4-flash | 400 | 0 | 5 | 3006 | 235 | 2155 | 4177 | 0.2003 |
| gemini-2.5-flash-lite | 400 | 0 | 10 | 2625 | 246 | 1842 | 3944 | 0.1258 |
| gpt-5.6-luna | 400 | 0 | 7 | 2654 | 181 | 3467 | 7366 | 0.2594 |

Total new: $5.7594.
