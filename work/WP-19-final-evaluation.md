# WP-19: Final evaluation on the locked test set (S11, once)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-19-final-evaluation.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 6 | default (Opus 5.5) | ~250k | "go" for the live latency run (~$1.5) | ~$1.5 | Gate 3 (`pre-test` tag), WP-18 | WP-20 |

## Context
The single, pre-registered look at the test set (spec golden rule 1; PLAN M16, §8). The protocol in
`results/eval_protocol.md` (tagged `pre-test`) says exactly what to compute. Anything not in the
protocol is labeled **exploratory**. Any change to the artifact or protocol since the tag is a
deviation that must be written down.

## Read (only these)
- `results/eval_protocol.md` (all of it), `PLAN.md` §8, `work/reports/WP-14-report.md`,
  `WP-18-report.md`; `ref/UNIROUTE_PIPELINE.md` §7, §10.

## Steps
1. Propose; ⏸ wait for OK. Verify: `git tag --contains` shows `pre-test`; `git diff pre-test --stat`
   for `artifacts/` and `results/eval_protocol.md` is empty (else list the deviations).
2. Open the sealed test labels **only** through `scripts/eval_test.py` (logs that it ran, with time
   and commit).
3. **Primary analysis:** shipped router at the protocol's λ vs always-best: cost reduction; quality
   difference with paired bootstrap 95% CI (10,000, seed 20261020) and exact McNemar; p90 latency from
   the replay. Verdict against the three success criteria (PLAN §8.2), stated plainly: met / not met.
4. **Secondary:** deferral curves, areas (with paired-bootstrap CIs of differences) and QNC for the
   whole ladder; per-cluster and per-category quality and cost; routing share; α = 2 robustness row;
   val-vs-test gap; holdout demo on test; length-controlled analysis if required by WP-11;
   gpt-4o-mini self-preference flag if raised.
5. **Production comparison:** cost of what production actually used on the same test prompts (list
   prices; models without a price are listed separately) and **similarity to production's answers**
   (same embedder, cosine) for each router, with the M15 caveat.
6. **Replay on test** through the gateway (cache, checks/escalation, stickiness as configured):
   cost/1k queries, hit rate, escalation rate, latency p50/p90; outage scenario.
7. **Live latency run:** ⏸ "go" (stage `live`). ~50 test-like messages from **val** (not test) per
   model through the real gateway → real end-to-end latency p50/p90 per model and for the router
   (overhead included). Compare with the replay's measured latencies.
8. Write `results/final/` tables and figures (numbers only) and `work/reports/WP-19-report.md`: every
   number labeled measured / simulated, with CI and n.

## Outputs
- `results/final/*`, `work/reports/WP-19-report.md`, updated dashboard data.

## Acceptance checks
- [ ] Protocol followed; deviations listed; every number has a CI or an n.
- [ ] Test labels were opened once (one `eval_test.py` run log; reruns only reproduce the same
      numbers from cache, no new choices).

## If blocked
- A bug found after opening the test set → fix it, rerun the **same** protocol, and report both the
  bug and the effect; never change λ, K, τ or the shipped router based on test results.

## End of session
- Log the headline results in MASTER_LOG; STATUS next: WP-20.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-19 step n", stop (results are reproducible from
cache).
