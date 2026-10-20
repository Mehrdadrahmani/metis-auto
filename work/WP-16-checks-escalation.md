# WP-16: Quality checks, escalation (cascade), stickiness, latency

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-16-checks-escalation.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 5 | default (Opus 5.5) | ~150k | – | $0 | WP-15 | WP-18 |

## Context
The brief's cascade: if a cheap model's answer is clearly bad, retry once, then escalate to a
stronger model. We use **free code checks**, not a judge per message (PLAN E7). Also: a stickiness
option to keep provider prompt-cache discounts within a conversation (E9), and a latency breakdown.

## Read (only these)
- `PLAN.md` §1.2 E7, E9; `work/reports/WP-15-report.md`; `results/metis_capabilities.md`
  (prompt-cache reporting).

## Steps
1. Propose; ⏸ wait for OK.
2. `gateway/checks.py`: `empty` (no non-space text), `truncated` (`finish_reason == length`),
   `wrong_language` (user `lang` = fa but answer < 50% Persian letters, unless the instructions ask
   for another language), `bad_json` (instructions demand JSON and `json.loads` fails), `refusal`
   (pattern list in Persian + English, e.g. «متأسفم، نمی‌توانم», "I can't help"). Each check returns
   a reason code.
3. Escalation policy: fail → 1 repair retry on the same model with a short system hint for that
   reason (e.g. "Answer in Persian.", "Return valid JSON only.") → fail again → next model with lower
   Ψ_k* (stronger in this cluster) → at most 2 escalations; trace every step.
4. **Stickiness option** (`gateway.yaml: stickiness: {enabled, delta}`): within a session, keep the
   previous turn's model if its score s(h) ≤ best score + δ (δ grid {0, 0.02, 0.05, 0.1} for replay).
   Cost model for prompt caching: per-provider discount rules in `models.yaml` (cached input price;
   minimum prefix length); `estimate_cost(tokens_in, cached_tokens, …)`. If Metis AI doesn't report
   cached tokens, mark costs "estimated" (owner informed via report).
5. Latency: per-stage timing already in traces; add a benchmark script with the real embedder:
   1,000 synthetic Persian messages of mixed lengths → p50/p95/p99 per stage →
   `results/gateway_latency.md`.
6. Tests: each check with fixtures (synthetic text, not data); escalation path order; max-escalation
   cap; stickiness decisions; cost with and without cache discount.

## Outputs
- `src/metis/gateway/checks.py`, escalation logic in the pipeline, stickiness + cost model,
  `results/gateway_latency.md`, tests.

## Acceptance checks
- [ ] All checks unit-tested; escalation never loops; trace shows every attempt.
- [ ] Overhead p95 ≤ 100 ms (or documented exception with the reason).

## If blocked
- Language detection too noisy on short answers → apply `wrong_language` only to answers ≥ 20 chars.

## End of session
- `work/reports/WP-16-report.md`; note the check thresholds to re-examine in WP-18 replay.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-16 step n", stop.
