# Gateway latency

Measured on this Mac, MPS, nano embedder, n = 1000 synthetic Persian messages, 3 to 400 words. Mock model call, so the model's own time is not included.

| Stage | p50 ms | p95 ms | p99 ms |
|---|---:|---:|---:|
| rules | 0.01 | 0.01 | 0.01 |
| embed | 22.68 | 70.68 | 88.05 |
| cache | 0.57 | 1.55 | 1.88 |
| route | 0.07 | 0.09 | 0.10 |
| total overhead | 23.4 | 72.2 | 89.3 |

Budget p95 ≤ 100 ms: met.
