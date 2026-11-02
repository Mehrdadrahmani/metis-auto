# S6 stats: test

Measured, n = 300 prompts per model. Counts, tokens, speed and dollars only: no text and no quality.

| Model | ok | failed | retried for length | mean in | mean out | p50 ms | p90 ms | new $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-sonnet-5-5 | 300 | 0 | 18 | 5231 | 462 | 5131 | 8813 | 5.4884 |
| deepseek-v4-flash | 300 | 0 | 6 | 3138 | 260 | 2321 | 4227 | 0.2173 |
| gemini-2.5-flash-lite | 300 | 0 | 11 | 2763 | 255 | 1971 | 4175 | 0.1377 |
| gpt-5.6-luna | 300 | 0 | 6 | 2766 | 188 | 3139 | 6501 | 0.2749 |

Total new: $6.1182.
