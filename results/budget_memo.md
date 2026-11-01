# Budget memo (DRAFT, not Gate 1)

Simulated from token statistics; no paid call made. Gate 1 needs the WP-04 estimator and confirmed
Metis AI prices. Candidate prices: public list prices (`configs/models.yaml`, `verified: false`).
Judge price: unknown; planning range $0.002 to $0.006 per call at 1,640 input tokens, scaled here by
input size because the judge sees instructions and context (DEV-5).

Token inputs (measured): val mean 2,781 estimated input tokens (n = 400, 3 chars per token);
planning value 1,640. Output mean 286, median 129 (billing, n = 254,048 replies, before the 1,024 cap).
Billing input mean 4,439 covers all traffic, including excluded workflow turns; used as the high case.
Test tokens were not opened; val stands in for them.

| Case | T_in | Judge $/call |
|---|---|---|
| Low | 1,640 | 0.0020 |
| Mid | 2,800 | 0.0068 |
| High | 4,439 | 0.0162 |

| Item | Calls | Low | Mid | High |
|---|---|---|---|---|
| Generation: deepseek-v4-flash | 700 | $0.22 | $0.33 | $0.49 |
| Generation: gpt-5.6-luna | 700 | $0.47 | $0.63 | $0.86 |
| Generation: gemini-3.5-flash-lite | 700 | $0.84 | $1.09 | $1.43 |
| Generation: claude-sonnet-5-5 | 700 | $4.30 | $5.92 | $8.22 |
| **Generation total** | 2,800 | **$5.8** | **$8.0** | **$11.0** |
| Pilot pairwise extra | 600 | $1.2 | $4.1 | $9.7 |
| Main judging, pointwise | 2,800 | $5.6 | $19.0 | $45.4 |
| Re-judge 5% | 140 | $0.3 | $1.0 | $2.3 |
| Cache labels (planning value) | ~300 | $0 | $1.0 | $1.8 |
| Live latency run (planning value) | ~250 | $0.8 | $1.5 | $2.5 |
| **Total, pointwise path** | ~7,100 | **$13** | **$35** | **$73** |

Pairwise path, mid case: about $43 (generation $8.0, pilot pointwise $2.7, 4,200 pairwise calls $28.6,
re-judge, cache labels and live run $3.5).

The high case passes the $60 cap. Before Gate 1: confirm the judge price; decide a cap on judge input
tokens. Generation is cached and paid once; the pilot's answers are reused.
