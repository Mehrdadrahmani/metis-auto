# WP-16 report: checks, escalation, latency

Checks: empty, truncated, wrong language, bad JSON, refusal. One repair retry, then up to 2 escalations to lower Ψ. Stickiness option built; on validation δ 0.02 to 0.1 changed nothing, so it ships off. Cached-input prices added to `models.yaml`; cost uses them only when usage reports cached tokens. Overhead with the real embedder on this Mac: p50 23.4 ms, p95 72.2 ms, budget met (`results/gateway_latency.md`).
