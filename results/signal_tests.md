# Signal tests on validation

Measured, held out, n = 798, 40 halves. ZeroRouter area 0.6545.
Cheap gap: pass rate minus always-DeepSeek at λ = 0.1. Shuffle: same groups in random order, 100 times, 95th percentile of area gain.
Many signals were tried on one set, so a small win can be luck.

| Signal | Groups | Area | Minus ZeroRouter | Shuffle 95% | Beats shuffle | Cheap gap |
|---|---:|---:|---:|---:|---|---:|
| No signal (K = 1) | 1 | 0.6545 | +0.0000 |  |  | +0.0% |
| Message K = 8 | 8 | 0.6522 | -0.0023 | +0.0074 | no | -1.1% |
| Message K = 4 | 4 | 0.6634 | +0.0089 | +0.0127 | no | -0.8% |
| Bot groups | 7 | 0.6592 | +0.0047 | +0.0070 | no | -1.4% |
| Single bot, top 20 + other | 21 | 0.6585 | +0.0040 | +0.0034 | yes | -1.4% |
| Bot category | 1 | 0.6545 | +0.0000 | +0.0000 | yes | +0.0% |
| Uses RAG | 2 | 0.6632 | +0.0087 | +0.0098 | no | -0.1% |
| Language | 3 | 0.6583 | +0.0039 | +0.0028 | yes | -0.2% |
| Instruction length | 3 | 0.6582 | +0.0037 | +0.0073 | no | -0.3% |
| Message length, 4 bands | 4 | 0.6610 | +0.0066 | +0.0112 | no | -0.8% |
| Prompt tokens, 4 bands | 4 | 0.6576 | +0.0031 | +0.0098 | no | -0.4% |
| Message K = 8 + bot groups (D-078) | 13 | 0.6530 | -0.0014 | +0.0022 | no | -1.8% |
| Message K = 4 + bot groups (D-078) | 9 | 0.6603 | +0.0058 | +0.0100 | no | -1.2% |

Bot group shares: 0: 39%, 1: 12%, 2: 13%, 3: 11%, 4: 11%, 5: 6%, 6: 8%.
Config hash: 9665c58310dd.
