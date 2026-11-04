# Router check on validation

Measured, held out, validation only. Pointwise jev, pass mark 7.
n = 798 prompts in 764 sessions. Sealed files not opened.

## Models

| Model | Cost share of Sonnet | Pass rate |
|---|---:|---:|
| gemini-2.5-flash-lite | 0.025 | 53.5% |
| deepseek-v4-flash | 0.041 | 65.4% |
| gpt-5.6-luna | 0.052 | 61.5% |
| claude-sonnet-5-5 | 1.000 | 66.2% |

Best possible (a perfect router): 79.4%. Hull used by ZeroRouter on all val: gemini-2.5-flash-lite, deepseek-v4-flash, claude-sonnet-5-5.

## S9 score by K

Mean normalized area, 40 held-out halves. ZeroRouter on the same halves: 0.6545. K limit 9, K* = 4.
The spread is of halves that share data, so it is too narrow to be a confidence interval.

| K | Area | Minus K = 1 | Minus ZeroRouter | Share of halves above ZeroRouter |
|---:|---:|---:|---:|---:|
| 1 | 0.6545 | +0.0000 | +0.0000 | 42% |
| 3 | 0.6629 | +0.0084 | +0.0084 | 92% |
| 4 | 0.6634 | +0.0089 | +0.0089 | 82% |
| 5 | 0.6598 | +0.0053 | +0.0053 | 70% |
| 6 | 0.6581 | +0.0036 | +0.0036 | 70% |
| 7 | 0.6526 | -0.0019 | -0.0019 | 50% |
| 8 | 0.6522 | -0.0023 | -0.0023 | 45% |
| 9 | 0.6527 | -0.0017 | -0.0017 | 50% |
| 10 | 0.6488 | -0.0056 | -0.0056 | 38% |
| 11 | 0.6488 | -0.0057 | -0.0057 | 35% |
| 12 | 0.6511 | -0.0034 | -0.0034 | 45% |
| 13 | 0.6488 | -0.0057 | -0.0057 | 32% |
| 14 | 0.6453 | -0.0092 | -0.0092 | 18% |
| 15 | 0.6475 | -0.0070 | -0.0070 | 30% |
| 16 | 0.6450 | -0.0094 | -0.0094 | 20% |
| 17 | 0.6579 | +0.0034 | +0.0034 | 65% |
| 18 | 0.6527 | -0.0017 | -0.0017 | 55% |
| 19 | 0.6452 | -0.0092 | -0.0092 | 35% |
| 20 | 0.6455 | -0.0090 | -0.0090 | 28% |

## Router against ZeroRouter at the same cost

Out of fold: 10 folds, 5 repeats, sessions whole. Interval: 95% bootstrap over sessions.
Gap in points of pass rate. Zero inside the interval means no measured gain.

| Router | λ | Cost | Pass rate | Gap to ZeroRouter (95% CI) |
|---|---:|---:|---:|---:|
| K = 1 | 0 | 0.924 | 65.5% | +0.0% (+0.0% to +0.0%) |
| K = 1 | 0.01 | 0.364 | 64.2% | +0.0% (+0.0% to +0.0%) |
| K = 1 | 0.03 | 0.041 | 65.4% | +0.0% (+0.0% to +0.0%) |
| K = 1 | 0.1 | 0.041 | 65.4% | +0.0% (+0.0% to +0.0%) |
| K = 1 | 0.3 | 0.041 | 65.4% | +0.0% (+0.0% to +0.0%) |
| K = 1 | 1 | 0.041 | 65.4% | +0.0% (+0.0% to +0.0%) |
| K = 3 | 0 | 0.773 | 67.5% | +2.1% (+0.7% to +3.4%) |
| K = 3 | 0.01 | 0.748 | 67.2% | +1.7% (+0.4% to +3.0%) |
| K = 3 | 0.03 | 0.360 | 65.2% | +0.1% (-0.9% to +1.1%) |
| K = 3 | 0.1 | 0.041 | 65.4% | +0.0% (+0.0% to +0.0%) |
| K = 3 | 0.3 | 0.041 | 65.4% | +0.0% (+0.0% to +0.0%) |
| K = 3 | 1 | 0.041 | 65.4% | +0.0% (+0.0% to +0.0%) |
| K = 8 | 0 | 0.534 | 64.6% | -0.7% (-2.0% to +0.6%) |
| K = 8 | 0.01 | 0.531 | 64.7% | -0.6% (-1.9% to +0.7%) |
| K = 8 | 0.03 | 0.303 | 65.2% | -0.1% (-1.4% to +1.1%) |
| K = 8 | 0.1 | 0.042 | 65.4% | +0.1% (-1.0% to +1.2%) |
| K = 8 | 0.3 | 0.042 | 65.4% | +0.1% (-1.0% to +1.3%) |
| K = 8 | 1 | 0.042 | 65.1% | -0.0% (-1.2% to +1.1%) |
| K* = 4 | 0 | 0.529 | 66.1% | +0.7% (-0.6% to +1.9%) |
| K* = 4 | 0.01 | 0.473 | 66.4% | +1.0% (-0.4% to +2.3%) |
| K* = 4 | 0.03 | 0.417 | 66.9% | +1.4% (-0.0% to +2.8%) |
| K* = 4 | 0.1 | 0.041 | 64.7% | -0.7% (-1.2% to -0.3%) |
| K* = 4 | 0.3 | 0.041 | 64.6% | -0.6% (-1.1% to -0.3%) |
| K* = 4 | 1 | 0.041 | 64.4% | -0.6% (-1.1% to -0.2%) |
