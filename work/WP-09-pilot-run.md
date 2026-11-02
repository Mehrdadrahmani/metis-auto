# WP-09: Pilot run (first paid stage, ~$7, limit $10)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-09-pilot-run.md; follow the session
> protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 3 | default (Opus 5.5) | ~120k | **"go"** with the estimate | ~$7 (limit $10, Gate 1) | Gate 1 | WP-10 |

## Context
The slim pilot (PLAN M8, DEV-3): the 4 candidates answer the 100 pilot val prompts; the judge grades
every answer **both** ways (pointwise 400 calls; pairwise vs claude-sonnet-5-5 in both orders, 600
calls). All of it is cached and reused by the main build (pilot ⊂ val). Then the labeling sheet for
the owner is built.

## Read (only these)
- `work/reports/WP-08-report.md` (sizes, budget approvals), `results/cost_estimate_v1.md`.
- `ref/UNIROUTE_PIPELINE.md` §P (procedure only), `PLAN.md` §1.1 M8–M11, P3.

## Steps
1. Show the estimate for this stage (`scripts/estimate_costs.py --stage pilot`) and the approved
   amount. ⏸ **STOP:** owner says "go".
2. S6 on `pilot_val` (100 prompts × 4 models = 400 calls), order: deepseek-v4-flash, gpt-5.6-luna,
   gemini-2.5-flash-lite, claude-sonnet-5-5. After the first 20 calls of each model: check failure rate,
   cost per call vs estimate, finish_reason=length share, reasoning tokens (should be ~0). Any anomaly
   (failures > 5%, cost/call > 2× estimate, length cut > 10%) → ⏸ stop and report.
3. S7-PT: 400 pointwise judgments. Check parse-failure rate (< 2%) after the first 40.
4. S7-PW: 300 pairs × 2 orders = 600 judgments (anchor = sonnet).
5. Noise sample: re-judge 20 pointwise + 20 pairwise items with a different cache salt (true repeat)
   → test–retest agreement.
6. Build the labeling HTML (`labeling/build.py`) for the 100 `cal` items (each pilot prompt paired
   with one non-anchor model, round-robin) + a separate 20-item re-label file to be done ≥ 2 days later.
   Put them in `runs/labeling/` (git-ignored). Tell the owner the path and the guideline.
7. Ledger: record real spend per model and per judge type in MASTER_LOG §Budget.

## Outputs
- Cached answers and judgments (SQLite), `runs/pilot/*` tables, `results/pilot_run_stats.md`
  (counts, failures, parse failures, $ per stage, tokens per call; no text),
  `runs/labeling/cal_*.html`.

## Acceptance checks
- [ ] 400 answers, 400 pointwise, 600 pairwise judgments (minus logged failures).
- [ ] Spend ≤ approved amount; ledger updated.
- [ ] Labeling files ready; owner informed.

## If blocked
- Metis AI errors/rate limits → lower concurrency to 2, resume (cache). A model unavailable for > 1 h
  → ⏸ ask the owner (wait / substitute).
- Spend approaching the approval before finishing → stop; ask for a top-up with numbers.

## End of session
- `work/reports/WP-09-report.md`. STATUS: waiting on owner (WP-10 labeling, ~3 h), next session WP-11
  after labels are in. Update cost assumptions (real tokens/call) in `results/cost_estimate_v2.md`
  and, if they differ > 25% from the memo, tell the owner before WP-12.

## If the context is getting full
Runs resume from the cache: stop at a checkpoint, `/handoff` with "next: WP-09 step n", stop.

## Added by D-082, D-083
- Also generate deepseek-v4-pro on the 100 pilot prompts (off-peak: not Mon-Fri 01:00-04:00, 06:00-10:00 UTC).
- Judge all pilot answers with both gpt-5.6-terra and jev-latest. Update the estimate before the go.

## Added by D-087
Before the batch, with the owner's "go", send one call per model and judge, including Jev. Check that each route answers, that `reasoning_tokens` is 0 or small, that usage is returned, and that Sonnet accepts `thinking: between_tools`. All params in `configs/gen_config.yaml` and `judge_config.yaml` are unverified. Commands: `scripts/s6_generate.py --set pilot --stage pilot`, `scripts/s7_judge.py --set pilot --stage pilot --judge judge`, then `--judge jev`. Set `approved_usd.pilot` in `configs/budget.yaml` first. The pilot estimate is $15.28, not ~$6.

## Added by D-093
Owner: gpt-5.6-terra judges the pilot **pointwise only**; jev-latest does pointwise and pairwise. Run `s7_judge.py --judge judge --method pointwise` and `--judge jev --method both`. Calls: 500 terra, 1,300 jev. Limit from Gate 1; estimate $6.71 (`results/budget_memo.md`). Lines above about "both ways" and the ~$6 are replaced by this. The noise sample's pairwise items use jev. Terra pairwise can be added later for about $8.57; the answers are cached.
