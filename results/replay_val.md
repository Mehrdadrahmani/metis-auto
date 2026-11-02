# Replay on validation

Simulated cost and latency from stored calls, pass from stored labels, n = 798. In-sample for the router, so its pass is a little optimistic: see `results/lambda_frozen.md` for unseen figures.
Replay of K = 8 plain equals the offline router: 0.6591. Cached answers have no stored label, so pass excludes them.

| Setup | Pass (95% CI) | $ per 1k | p50 s | p90 s | Cache hits | Escalated | Failed | Failovers |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| TakRouter K = 8, plain | 65.9% (62.5% to 69.0%) | 0.696 | 2.28 | 4.63 | 0.0% | 0.0% | 0.0% | 0 |
| TakRouter K = 4, plain | 67.5% (64.3% to 70.7%) | 5.506 | 3.08 | 7.59 | 0.0% | 0.0% | 0.0% | 0 |
| Always Sonnet | 66.2% (62.9% to 69.4%) | 16.267 | 5.15 | 9.34 | 0.0% | 0.0% | 0.1% | 0 |
| Always DeepSeek | 65.4% (62.1% to 68.5%) | 0.664 | 2.21 | 4.15 | 0.0% | 0.0% | 0.0% | 0 |
| Always Gemini | 53.5% (50.1% to 57.1%) | 0.403 | 1.84 | 3.95 | 0.0% | 0.0% | 0.0% | 0 |
| K = 8 + checks | 65.8% (62.4% to 68.8%) | 0.993 | 2.36 | 4.79 | 0.0% | 1.9% | 0.0% | 0 |
| K = 8 + cache | 65.9% (62.5% to 69.0%) | 0.696 | 2.28 | 4.63 | 0.0% | 0.0% | 0.0% | 0 |
| K = 8 + cache + checks | 65.8% (62.4% to 68.8%) | 0.993 | 2.36 | 4.79 | 0.0% | 1.9% | 0.0% | 0 |
| K = 4 + cache + checks | 67.4% (64.2% to 70.6%) | 5.671 | 3.12 | 7.89 | 0.0% | 0.3% | 0.0% | 0 |
| K = 8 + all, 10-min outage | 65.9% (62.6% to 69.2%) | 1.020 | 2.46 | 5.07 | 0.0% | 2.1% | 0.0% | 20 |
| K = 8 + sticky δ 0.02 | 65.9% (62.5% to 69.0%) | 0.696 | 2.28 | 4.63 | 0.0% | 0.0% | 0.0% | 0 |
| K = 8 + sticky δ 0.05 | 65.9% (62.5% to 69.0%) | 0.696 | 2.28 | 4.63 | 0.0% | 0.0% | 0.0% | 0 |
| K = 8 + sticky δ 0.1 | 65.9% (62.5% to 69.0%) | 0.696 | 2.28 | 4.64 | 0.0% | 0.0% | 0.0% | 0 |
