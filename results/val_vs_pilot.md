# Validation against pilot

Measured, pointwise jev, pass mark 7. Same judge, same answers for pilot prompts.
Pilot n = 100, new n = 299, all n = 399.
Rates show a 95% Wilson interval.

## Pass rate

| Model | Pilot | New | All | New minus pilot (95% CI) |
|---|---:|---:|---:|---:|
| deepseek-v4-flash | 73.0% (64% to 81%) | 62.2% (57% to 68%) | 64.9% (60% to 69%) | -10.8% (-21.1% to -0.5%) |
| gpt-5.6-luna | 65.0% (55% to 74%) | 59.9% (54% to 65%) | 61.2% (56% to 66%) | -5.1% (-16.1% to +5.8%) |
| gemini-2.5-flash-lite | 57.0% (47% to 66%) | 52.8% (47% to 58%) | 53.9% (49% to 59%) | -4.2% (-15.4% to +7.1%) |
| claude-sonnet-5-5 | 72.0% (63% to 80%) | 62.9% (57% to 68%) | 65.2% (60% to 70%) | -9.1% (-19.5% to +1.3%) |

## Mean score

| Model | Pilot | New | All |
|---|---:|---:|---:|
| deepseek-v4-flash | 7.62 | 7.21 | 7.31 |
| gpt-5.6-luna | 7.36 | 7.18 | 7.22 |
| gemini-2.5-flash-lite | 7.16 | 6.76 | 6.86 |
| claude-sonnet-5-5 | 7.58 | 7.25 | 7.33 |

## Patterns

| Share of prompts | Pilot | New | All |
|---|---:|---:|---:|
| All 4 pass | 49.0% | 38.1% | 40.9% |
| All 4 fail | 17.0% | 22.7% | 21.3% |
| At least one passes (ceiling) | 83.0% | 77.3% | 78.7% |
| DeepSeek passes, Sonnet fails | 7.0% | 9.7% | 9.0% |
| Sonnet passes, DeepSeek fails | 6.0% | 10.4% | 9.3% |

## Separability and stability

| Set | n | D, K = 1 | D, K = 3 | D, K = 8 | C, K = 3 | C, K = 8 |
|---|---:|---:|---:|---:|---:|---:|
| Pilot | 100 | 0.333 | 0.111 | 0.042 | 0.635 | 0.280 |
| New | 299 | 0.333 | 0.111 | 0.042 | 0.760 | 0.360 |
| All | 399 | 0.500 | 0.167 | 0.104 | 0.736 | 0.533 |

## Pass rate by cluster, K = 3, all validation

| Cluster | n | pilot n | all fail | deepseek-v4-flash | gpt-5.6-luna | gemini-2.5-flash-lite | claude-sonnet-5-5 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 179 | 39 | 19.6% | 67.0% | 64.2% | 61.5% | 68.2% |
| 1 | 87 | 25 | 32.2% | 55.2% | 47.1% | 36.8% | 48.3% |
| 2 | 133 | 36 | 16.5% | 68.4% | 66.2% | 54.9% | 72.2% |

## Pass rate by cluster, K = 8, all validation

| Cluster | n | pilot n | all fail | deepseek-v4-flash | gpt-5.6-luna | gemini-2.5-flash-lite | claude-sonnet-5-5 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 61 | 15 | 13.1% | 73.8% | 65.6% | 75.4% | 72.1% |
| 1 | 50 | 12 | 36.0% | 58.0% | 46.0% | 34.0% | 48.0% |
| 2 | 34 | 7 | 8.8% | 85.3% | 73.5% | 61.8% | 79.4% |
| 3 | 45 | 14 | 26.7% | 44.4% | 62.2% | 40.0% | 53.3% |
| 4 | 54 | 13 | 22.2% | 66.7% | 61.1% | 42.6% | 66.7% |
| 5 | 26 | 7 | 23.1% | 50.0% | 50.0% | 42.3% | 50.0% |
| 6 | 96 | 22 | 20.8% | 64.6% | 61.5% | 59.4% | 68.8% |
| 7 | 33 | 10 | 18.2% | 75.8% | 69.7% | 66.7% | 78.8% |
