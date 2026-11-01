# WP-12: Generate answers for all validation and test prompts (S6)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-12-generation.md; follow the session
> protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 4 | default (Opus 5.5) | ~100k | **"go"** with the estimate | ~$7 (approved `gen_main`) | Gate 2 | WP-13 |

## Context
Every candidate answers every val and test prompt **once** (spec golden rule 3). Pilot answers
(100 val prompts) are reused from the cache, so this stage generates 4 × (300 val + 300 test) = 2,400
calls (adjust if WP-08 changed sizes). Generating the test answers is allowed (no choice is made with
them); **nobody looks at test answers or computes test metrics** until WP-19.

## Read (only these)
- `work/reports/WP-11-report.md` (decision; any gen changes), `results/cost_estimate_v2.md`.
- `ref/UNIROUTE_PIPELINE.md` §4 S6.

## Steps
1. Show the estimate and the approved amount. ⏸ **STOP:** owner says "go".
2. Run `scripts/s6_generate.py --split val,test --stage gen_main`, models in order deepseek-v4-flash →
   gpt-5.6-luna → gemini-2.5-flash-lite → claude-sonnet-5-5. Generate each model within one short time
   window (model versions; record the returned version string).
3. Monitor per model after 50 calls: failure rate, cost/call vs estimate, `finish_reason=length`
   share, reasoning tokens. Anomaly → ⏸ stop and report (PLAN P3).
4. Failed calls after retries: `status=failed` (worst label later). Report counts per model.
5. Record measured latency per call (used by the replay simulator, WP-18).

## Outputs
- Cached responses; `runs/s6/responses.parquet` (ids, tokens, latency, status; text stays in SQLite),
  `results/s6_stats.md` (counts, failures, tokens and $ per model, latency p50/p90 per model; no text).

## Acceptance checks
- [ ] 4 × (val + test) answers present (minus logged failures ≤ 2%).
- [ ] Spend ≤ approval; ledger updated; rerun = 0 calls.

## If blocked
- Rate limits → lower concurrency, resume. Model unavailable → ⏸ owner decides (wait / drop the model
  and adjust PLAN; log it).

## End of session
- `work/reports/WP-12-report.md`. Update the WP-13 estimate with real answer lengths (judge input size).

## If the context is getting full
The runner checkpoints every 25 items: stop, `/handoff` with "next: WP-12 step 2 (resume)", stop.

## Added by D-087
`scripts/s6_generate.py` cannot select the test set (`metis.llm.stage.SETS`). Add it here, reading the sealed ids only inside the batch and never printing them.
