# WP-15: Gateway core (rules, router, calls, failover, traces)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-15-gateway-core.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 5 | default (Opus 5.5) | ~250k (split 15a/15b if needed) | – | $0 (mock providers) | WP-02, WP-03, WP-04 | WP-16, WP-17, WP-18 |

## Context
The brief's gateway around the router: OpenAI-compatible API, hard rules, routing, model calls with
failover and circuit breakers, and a trace for every request. Built and tested with **mock providers
and a mock router artifact** (from WP-07) until `artifacts/router_v1/` exists (WP-14). Provider calls
use LiteLLM via Metis AI (PLAN E1–E4). Failover is model-to-model and tested by fault injection;
we don't claim a second aggregator unless one is configured (E3).

## Read (only these)
- `PLAN.md` §1.2 E1–E6, E10; `ref/docs/design.md` §5 (G1–G7 table only);
  `ref/UNIROUTE_PIPELINE.md` §5 (online rule).
- Reports of WP-02 (rules), WP-03 (embedder + latency), WP-04 (client).

## Steps
1. Propose (say whether you'll split: 15a = steps 2–5, 15b = steps 6–9); ⏸ wait for OK.
2. Deps: `fastapi`, `uvicorn`, `pydantic`. `src/metis/gateway/app.py`: `POST /v1/chat/completions`
   (OpenAI request/response schema; `model: "metis-auto"` routes, a concrete model id bypasses the
   router), `GET /health`, `GET /metrics` (JSON). Request metadata (chatbot id, session id) via
   `metadata` field or headers `X-Metis-Chatbot`, `X-Metis-Session`. Non-streaming first.
3. **Pipeline per request** (each stage timed): G1 rules (`metis.data.rules`: widget click → return a
   workflow marker, image → vision-capable models only, context fit, breaker state → available set
   A) → G2 normalize + embed (the same code as offline S1/S4; one vector reused) → G3 cache hook (a
   no-op until WP-17) → G4 route (`router.route` with the artifact; λ from config) → G5 call with
   failover → G6 checks hook (no-op until WP-16) → G7 trace.
4. `gateway/failover.py`: on error/timeout → next-lowest s(h), preferring a different upstream
   provider; per-model **circuit breaker** (3 failures in 60 s → open 30 s → half-open, 1 probe);
   timeouts and retries per PLAN E4; per-model concurrency semaphore.
5. `gateway/traces.py`: SQLite `traces` table (one row per request: ids, chatbot, lang, cluster k*,
   all scores, chosen model, fallbacks tried, escalations, cache hit, tokens in/out, cost, latency per
   stage and total, artifact version, status). No message text stored by default (flag for local
   debugging only, off).
6. Config `configs/gateway.yaml`: artifact path, λ, mode, timeouts, breaker params, model list,
   `mock: true|false`.
7. **Mock provider** (`gateway/mock_provider.py`): configurable latency distribution per model (later:
   measured from WP-12), error injection (rate, 5xx, timeouts, model "down" windows).
8. Tests: OpenAI-client compatibility (the `openai` SDK pointed at the gateway works); rules
   (widget, image, context); routing matches `router.route` exactly for the same input; fault
   injection: one model down → 0 failed requests, breaker opens/closes; all models down → clean
   503 with a trace; latency of gateway overhead with mocks (p50/p95) logged.
9. `scripts/gateway_smoke.py`: 20 sample prompts through the gateway in mock mode; print the trace
   summary (counts, latency, routing share; no text).

## Outputs
- `src/metis/gateway/{app,failover,traces,mock_provider}.py`, `configs/gateway.yaml`, tests,
  `results/gateway_smoke.md`.

## Acceptance checks
- [ ] Fault injection: 0 failed requests with any single model down; breaker behavior tested.
- [ ] Gateway overhead p95 (excluding the model call) ≤ 100 ms on the Mac with the real embedder.
- [ ] Router decisions identical to the offline router for the same inputs.

## If blocked
- The real artifact isn't ready → keep the mock artifact; WP-18 switches to v1.

## End of session
- `work/reports/WP-15-report.md` (endpoints, how to run, latency numbers). If the overhead budget is
  missed, note the slow stage and propose a fix (smaller embedder input, batching) for the owner.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-15 step n" (or WP-15b), stop.
