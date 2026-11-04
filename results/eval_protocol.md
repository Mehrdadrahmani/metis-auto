# Evaluation protocol (frozen by tag `pre-test`)

Written on validation only, before any test label was opened. Anything not listed here is exploratory.
Test set: 300 prompts, 4 answers each, pointwise jev labels, pass = score ≥ 7 (τ = 7).

**Routers.** Shipped: UniRoute K = 8, λ = 0.5151, `artifacts/router_v1/` (D-117). Frozen comparison: UniRoute K = 4, λ = 0.04954, `artifacts/router_v1_k4/` (D-064 rule). λ is the largest value whose out-of-fold validation pass rate is not below always-DeepSeek (D-118, DEV-16). Budget-mode λ from `results/lambda_val.md` is reported as a secondary point.

**Primary comparison 1, always-Sonnet (PLAN §8.2).** Success needs all three: (1) cost per query at least 40% lower; (2) lower bound of the 95% CI of router minus Sonnet pass rate ≥ −5 points; (3) p90 latency from replay ≤ Sonnet's.

**Primary comparison 2, always-DeepSeek (added for this data).** Report the pass difference with 95% CI and the cost ratio. The router "adds value over DeepSeek" only if the CI lower bound is above 0 at a cost no more than 10% higher. Validation predicts it will not, and that is an acceptable result.

**Statistics.** Paired bootstrap, 10,000 draws, seed 20261020, whole sessions resampled; exact McNemar for pass differences. Cost is measured per prompt from test tokens and `configs/models.yaml` list prices, excluding DeepSeek peak-hour doubling. Normalized cost uses the frozen ĉ.

**Scoring rules.** Prompts Jev refused (1 test) are left out for all models. A failed answer keeps the worst score. The 3 test answers that stayed cut off are scored as they are.

**Secondary.** Ladder with area, QNC exact and QNC within 1 point: K = 8, K = 4, K = 1, ZeroRouter, K-NN k = 80, logistic, always-cheapest, always-best, with paired CIs of area differences. "No significant difference" is a valid result. Also: per-cluster and per-category pass and cost; routing shares; α = 2 row; val-vs-test gap; holdout demo with Gemini; 60 sealed test repeats vs first scores; length-controlled pass by prompt-length tercile.

**Production.** Cost of production's model on the same prompts where priced, and cosine similarity to production answers, with the M15 caveat that similarity is not quality.

**Replay.** Through the gateway with the settings in `configs/gateway.yaml` as committed at the end of WP-18, chosen on validation only: cache, checks, escalation, stickiness, and one 10-minute outage of the chosen model. Latencies are measured from stored calls; costs are simulated from stored tokens. The live latency run uses validation messages, never test.

**Labels on every number.** Measured or simulated, n, and a CI. Opened once through `scripts/eval_test.py`. A bug found later is fixed, the same protocol is rerun, and both results are reported. λ, K, τ and the router never change after opening.
