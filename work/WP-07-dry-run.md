# WP-07: End-to-end dry run on the sample (mock LLM, $0)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-07-dry-run.md; follow the session
> protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~150k | – | $0 | WP-02…WP-06 | WP-08 |

## Context
Proves the whole offline pipeline S1→S12 runs as one command sequence before the real data and the
first dollar. Uses the sample with scaled sizes and mock answers/judgments, so the **numbers mean
nothing**; only the plumbing is tested.

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §2 (overview), §10 (acceptance checklist).
- Reports of WP-02…WP-06 (only their "outputs" and "how to run" parts).

## Steps
1. Propose; ⏸ wait for OK.
2. `scripts/pipeline.py` (or a `Makefile`): stages `s1 s2 s4 s5 s6 s7 s8 s9 s10 s11 s12` with
   `--config configs/pipeline.yaml --sizes sample --mock`; each stage reads the previous stage's
   output from `runs/<stage>/` and writes a manifest (`inputs hash, config hash, seed, counts,
   duration, cost`).
3. Mock judge: scores drawn from a seeded distribution that depends on (cluster, model) so S8–S11 get
   *some* structure; mock pairwise from the same latent quality.
4. Run all stages on the sample (val 60, test 40, pilot 20, K ∈ {1, 3, 4}).
5. Run the whole pipeline a **second** time: assert 0 new mock calls (cache hits) and identical
   outputs (hashes).
6. Leak test: run S6/S7 with a recording transport; scan every recorded request with the redaction
   patterns; assert 0 hits.
7. Produce `results/dry_run_report.md`: stage table (counts, durations, $ = 0), a mock Ψ table (marked
   MOCK), mock deferral curves (marked MOCK), the artifact path, the spec §10 checklist with
   ✓/–/n.a.
8. Run `scripts/estimate_costs.py` for the **real** planned sizes (val 400, test 300, pilot 100, 4
   models) with the sample's token stats → `results/cost_estimate_v1.md` (updates the WP-06 one).

## Outputs
- `scripts/pipeline.py`, `results/dry_run_report.md`, `results/cost_estimate_v1.md`,
  `runs/**` (git-ignored), a mock artifact under `runs/s12/`.

## Acceptance checks
- [ ] One command runs S1→S12 on the sample in mock mode.
- [ ] Second run: 0 new calls, identical hashes.
- [ ] 0 secrets in recorded requests.
- [ ] Cost estimate for the real sizes ≤ PLAN §7 high estimate (else tell the owner now).

## If blocked
- A stage from an earlier WP is broken → fix it if small (< 30 min), otherwise log it in STATUS as a
  blocker and reopen that WP.

## End of session
- `work/reports/WP-07-report.md`. Update STATUS "next: WP-08 (waiting for data)" and, in parallel,
  "WP-15 can start". If the cost estimate moved, update PLAN §7 and MASTER_LOG §Budget.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-07 step n", stop.

## Note from WP-05a
`candidate_ks(n_val)` is empty for the 60-prompt sample (floor(60/50) = 1): pass explicit K values
in the dry run, for example {1, 2, 3}, and say so in its report.

## Added by D-080
Rerun the split (free): `runs/s2` and `results/split_manifest.json` still name gemini-3.5-flash-lite as a calibration model. Prompt sets should not change; check that with the manifest hashes. Do not open sealed test ids.
