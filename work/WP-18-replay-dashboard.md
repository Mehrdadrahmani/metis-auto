# WP-18: Replay simulator and dashboard

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-18-replay-dashboard.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 5 | default (Opus 5.5) | ~200k | – | $0 | WP-14, WP-16, WP-17 | WP-19 |

## Context
The brief's cost, latency and cache metrics need traffic. We **replay** a set of real messages in
time order through the gateway in simulation mode: the "model call" returns the **stored** answer of
the chosen model (WP-12), its **measured** latency and real token usage, and the stored judge label
gives the quality. So the replay costs $0 and is consistent with the offline evaluation. In this WP
the replay runs on **validation** traffic only (development); WP-19 runs it once on test.

## Read (only these)
- `PLAN.md` §1.2 E7–E10, §8.1; reports of WP-14, WP-15, WP-16, WP-17; `results/eval_protocol.md`
  (replay settings).

## Steps
1. Propose; ⏸ wait for OK.
2. `sim/replay.py`: input = a split's prompts in timestamp order (session order preserved); gateway
   with `provider: replay` (stored answer + latency + usage; missing → treated as failure);
   optional fault schedule (a model "down" for a window); cache warm-start = empty; outputs traces.
3. Metrics from traces (`eval/report.py`): cost per query and per 1,000 queries (with and without
   prompt-cache discounts), savings vs always-best and vs production's actual model mix, quality
   (pass/win rate from stored labels), routing share per model and per cluster, cache hit rate and
   cached-answer quality (judge label of the cached answer for the new message where available,
   else "unmeasured"), escalation rate and its cost, failover count, latency p50/p90/p99 (gateway
   overhead + measured model latency; cache hits use cache latency).
4. Runs on **val**: (i) shipped router, (ii) always-best, (iii) always-cheapest, (iv) stickiness
   δ grid, (v) with a 10-minute outage of the chosen model. Check: replay quality/cost = offline
   router numbers on the same set (± rounding) when cache/escalation are off.
5. Dashboard `dashboard/` (Streamlit or a static HTML generated from results; pick the faster to
   build): KPI tiles (cost/1k queries, % saved vs premium, quality vs premium with CI, p50/p90 latency,
   cache hit rate, tokens saved), routing share by cluster, cost–quality curve with the operating
   point, recent traces table (ids and numbers only). Brief Action 3 "value created" view.
   Single requests and router-selection runs are browsed in the local MLflow UI (D-044); the
   dashboard is for the aggregate results.
6. Tests: replay determinism (same seed → same traces), fault schedule, metric formulas on a tiny
   hand-computed example.

## Outputs
- `src/metis/sim/replay.py`, `src/metis/eval/report.py`, `dashboard/`, `results/replay_val.md`,
  screenshots in `results/figures/`.

## Acceptance checks
- [ ] Replay = offline numbers when extras are off; outage run has 0 failed requests.
- [ ] Dashboard runs locally with one command (documented in the report).

## If blocked
- Some (prompt, model) answers missing → count as failures, report the share.

## End of session
- `work/reports/WP-18-report.md`; if escalation or stickiness change costs a lot, note it for the
  protocol (changes after `pre-test` must be logged as deviations).

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-18 step n", stop.
