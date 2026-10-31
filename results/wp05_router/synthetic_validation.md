# Synthetic validation of the router (WP-05 step 9)

Simulated data with a planted answer: 3 prompt types in 64 dimensions, 4 models, 5,000 train / 400 val / 300 test, whole sessions resampled. No real data.

## Planted structure: routers at K = 3 (simulated, n_test = 300, one dataset)

| Router | Area | QNC | QNC within 1 point |
|---|---:|---:|---:|
| UniRoute | 0.9495 | 1.000 | 0.036 |
| ZeroRouter | 0.8650 | 1.000 | 0.945 |
| K-NN (k = 40) | 0.9524 | 0.225 | 0.036 |
| Logistic | 0.9495 | 1.000 | 0.036 |

Single models (no curve): Always-best cost 1.00, quality 0.9533; Always-cheapest cost 0.03, quality 0.7767. QNC 1.000 means the exact quality of the best model was never reached.

UniRoute minus ZeroRouter area: **+0.0845**, 95% CI [+0.0520, +0.1178] (10,000 session resamples).
Separability (criterion D): 0.56.

UniRoute deferral curve, distinct points (cost, quality): (0.030, 0.777), (0.036, 0.950), (0.068, 0.930), (0.092, 0.910)

## No structure: routers at K = 3 (simulated, n_test = 300, one dataset)

| Router | Area | QNC | QNC within 1 point |
|---|---:|---:|---:|
| UniRoute | 0.8577 | 1.000 | 0.952 |
| ZeroRouter | 0.8633 | 1.000 | 0.946 |
| K-NN (k = 80) | 0.8485 | 0.985 | 0.950 |
| Logistic | 0.8581 | 1.000 | 0.953 |

Single models (no curve): Always-best cost 1.00, quality 0.9533; Always-cheapest cost 0.03, quality 0.7733. QNC 1.000 means the exact quality of the best model was never reached.

UniRoute minus ZeroRouter area: **-0.0057**, 95% CI [-0.0253, +0.0217] (10,000 session resamples).
Separability (criterion D): 0.50.

## Choosing K: which rule finds the truth? (100 simulated datasets each)

The planted answer is K = 3. Area change = test area at the picked K minus at K = 3.

| Data | Rule | K = 3 picked | Other picks | Area change, mean | worst |
|---|---|---:|---|---:|---:|
| Planted structure | highest score (spec) | 12 | K4: 8, K5: 17, K6: 15, K7: 23, K8: 25 | +0.0003 | -0.0130 |
| Planted structure | smallest K within one spread | 93 | K4: 2, K5: 2, K7: 2, K8: 1 | -0.0001 | -0.0165 |
| No structure | highest score (spec) | 22 | K4: 12, K5: 18, K6: 18, K7: 12, K8: 18 | -0.0005 | -0.0260 |
| No structure | smallest K within one spread | 90 | K4: 5, K5: 1, K6: 2, K7: 1, K8: 1 | -0.0006 | -0.0305 |

Models: cheap-a (0.03), cheap-b (0.05), mid (0.13), strong (1.0).
