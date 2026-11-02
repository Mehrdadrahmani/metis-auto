# Router ladder on validation

Measured, held out, n = 798, 40 halves (10 for logistic). Comparison only: UniRoute ships (M1).
QNC: cheapest budget reaching the best single model on the held-out half, as a share of its cost. 1.000 can mean never reached.
Read QNC with care: the best single model flips between DeepSeek and Sonnet across halves, and their costs differ 24 times.
Spread is across halves that share data, not a confidence interval.

| Router | Area | Minus UniRoute K* | QNC exact | QNC within 1 point |
|---|---:|---:|---:|---:|
| UniRoute K = 4 | 0.6634 | +0.0000 | 0.725 | 0.413 |
| UniRoute K = 1 | 0.6545 | -0.0089 | 0.688 | 0.345 |
| ZeroRouter | 0.6545 | -0.0089 | 0.688 | 0.345 |
| K-NN k = 80 | 0.6636 | +0.0002 | 1.297 | 0.664 |
| Logistic | 0.6532 | -0.0083 | 2.137 | 0.776 |
| Always-cheapest | 0.5351 | -0.1283 | 1.000 | 1.000 |
| Always-best | 0.2085 | -0.4548 | 1.000 | 1.000 |

K-NN k tuned on [5, 10, 20, 40, 80]: {"5": 0.6224, "10": 0.6369, "20": 0.647, "40": 0.659, "80": 0.6636}.
