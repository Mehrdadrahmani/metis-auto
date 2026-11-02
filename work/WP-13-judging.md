# WP-13: Judge all validation and test answers (S7, chosen method)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-13-judging.md; follow the session
> protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 4 | default (Opus 5.5) | ~100k | **"go"** with the estimate | pointwise ~$10 / pairwise ~$20 (approved `judge_main`) | WP-12 | WP-14 |

## Context
Only the method chosen at Gate 2 is run (spec §P: "the full build runs only the chosen method's
judging"). **WP-11 updates this file** with the method, τ, call counts and estimate; if this note is
still here, WP-11 has not done so: stop and check.

> Method: `<set by WP-11>` · τ: `<set by WP-11>` · calls: `<set by WP-11>` · estimate: `<set by WP-11>`

## Read (only these)
- `work/reports/WP-11-report.md`, `work/reports/WP-12-report.md`, `configs/judge_config.yaml`.
- `ref/UNIROUTE_PIPELINE.md` §4 S7-PT or S7-PW (only the chosen one).

## Steps
1. Show the estimate and the approved amount. ⏸ **STOP:** owner says "go".
2. Pointwise: judge every (prompt, model) on val + test not already judged in the pilot
   (4 × 600 = 2,400 calls). Pairwise: every (prompt, non-anchor model) × 2 orders (3 × 600 × 2 =
   3,600 calls). Same judge config hash as the pilot (if the rubric was revised in WP-11, the pilot
   items were re-judged there; check the hash).
3. Re-judge a seeded 5% sample with a cache salt (noise estimate, PLAN M11).
4. Monitor after the first 100: parse failures < 2%, cost/call vs estimate. Anomaly → ⏸ stop.
5. Derive `labels` (ℓ per prompt × model) for **val only** into `runs/s7/labels_val.parquet`; test
   labels are written to `runs/s7/labels_test.sealed.parquet` and not opened (WP-19 opens them).

## Outputs
- Cached judgments; `runs/s7/*`; `results/s7_stats.md` (counts, parse failures, $, re-judge
  agreement; val-only score distributions per model; nothing from test).

## Acceptance checks
- [ ] All items judged (minus logged parse failures ≤ 2%); spend ≤ approval; rerun = 0 calls.
- [ ] No test metric computed or printed (grep the session log for "test" numbers: none).

## If blocked
- Judge model changed version mid-run (returned version differs) → stop, ⏸ owner decides (finish
  with the new version and note it, or re-judge).

## End of session
- `work/reports/WP-13-report.md`. Next: WP-14.

## If the context is getting full
Stop at a checkpoint, `/handoff` with "next: WP-13 step 2 (resume)", stop.

## Added by D-087
`scripts/s7_judge.py` has no 5% re-judge yet. Add it with its own `config_id` suffix, so the cache does not return the first answer.

## Added by D-101, D-102
Judge = Jev, pointwise and pairwise; no terra. Add chat history to the Jev form first (`render.py`, `{history}` slot, same turns as generation). New judge config id, so the cache starts fresh for judgments. Estimate about $1 for 500 new prompts. Set `approved_usd.judge_main` after Gate 2. Add cache-write cost to the estimate, or use a 7% margin.
