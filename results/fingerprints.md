# Fingerprints

Measured on validation, n = 798. Pointwise jev, pass mark 7, Eq. 12, α = 0. Fail rate per cluster with 95% Wilson interval.
Names are drafts from configs/cluster_names.yaml. Ceiling means every model fails under 5% in the cluster.

## K* = 4

| Cluster | Name | n | deepseek-v4-flash | gpt-5.6-luna | gemini-2.5-flash-lite | claude-sonnet-5-5 |
|---:|---|---:|---:|---:|---:|---:|
| 0 | Everyday knowledge (health, products, study) | 141 | 22% (16% to 30%) | 30% (23% to 39%) | 40% (32% to 48%) | 23% (17% to 30%) |
| 1 | Short fragments and follow-ups | 191 | 45% (38% to 52%) | 50% (43% to 57%) | 66% (60% to 73%) | 50% (43% to 57%) |
| 2 | Practical requests and support | 153 | 31% (24% to 38%) | 31% (25% to 39%) | 34% (27% to 42%) | 30% (23% to 38%) |
| 3 | Personal chat and role-play | 313 | 36% (31% to 42%) | 39% (33% to 44%) | 43% (38% to 49%) | 31% (26% to 36%) |

Largest change from α = 2 smoothing: 0.002.

## Every K

| K | Smallest cluster | Median cluster | Empty | Ceiling clusters | Can ship |
|---:|---:|---:|---:|---:|---|
| 3 | 189 | 253 | 0 | 0 | yes |
| 4 | 141 | 172 | 0 | 0 | yes |
| 5 | 64 | 145 | 0 | 0 | yes |
| 6 | 58 | 131 | 0 | 0 | yes |
| 7 | 58 | 115 | 0 | 0 | yes |
| 8 | 58 | 96 | 0 | 0 | yes |
| 9 | 45 | 78 | 0 | 0 | yes |
| 10 | 43 | 70 | 0 | 0 | no |
| 11 | 23 | 63 | 0 | 0 | no |
| 12 | 23 | 62 | 0 | 0 | no |
| 13 | 22 | 60 | 0 | 0 | no |
| 14 | 21 | 56 | 0 | 0 | no |
| 15 | 13 | 44 | 0 | 0 | no |
| 16 | 15 | 45 | 0 | 0 | no |
| 17 | 21 | 41 | 0 | 0 | no |
| 18 | 20 | 40 | 0 | 0 | no |
| 19 | 13 | 39 | 0 | 0 | no |
| 20 | 14 | 36 | 0 | 0 | no |
