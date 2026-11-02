# WP-07 report: end-to-end dry run

Date 2026-11-02. Cost $0.00 (mock mode, sample only). Tests 262 pass. Every quality number in the dry run is mock.

## Built
`scripts/pipeline.py` (stages s1, s2, s4 to s12 in `runs/dry/`, own cache), mock-only cache and recording
hooks in `src/metis/llm/{callcache,client}.py`, `tests/test_dry_run_hooks.py`, `results/dry_run_report.md`.
S6 and S7 now sort their output, because threads finish in any order.

Run: `uv run python scripts/pipeline.py --config configs/pipeline.yaml --sizes sample --mock --check`

## Acceptance
- [x] One command runs S1 to S12 on the sample in mock mode.
- [x] Second run: 0 new calls, identical hashes for all 11 stages.
- [x] 0 secrets in 4,802 recorded requests, with 13,720 fake key values planted in 343 eligible prompts.
- [ ] Cost estimate within the PLAN section 7 high: **not met.** Pointwise $47.68 vs high $39, pairwise $62.12 vs high $54. Owner told; decide at Gate 1.

## Also done this session
- D-088: near-duplicate step removed; K-means and stability rerun on all 179,185 train prompts.
- D-089: K limit 9. Mean ARI 0.99 or higher to K = 9, 0.89 at K = 10, 0.85 at K = 11 (three fits each).
- Split rerun (D-080): train, val, test and pilot hashes unchanged; sealed file byte-identical; only 33 calibration rows changed name, gemini-3.5 to gemini-2.5. Qdrant needs no update.
- D-090: no S1 rules bug is recorded anywhere; the note came from the D-068 risk line.

## What did not work first
- The first leak test used the pilot, which holds no key patterns, so it proved nothing. The stored prompts hold none at all, so fake keys are planted now.
- Prompts over 20,000 characters are refused by the request builder, as designed; the leak test uses eligible prompts only.

## Limits
- Train is only 56 prompts on the sample, and all 60 val prompts fall in one cluster at K = 3. K* = 3 is therefore the same as K = 1 here, so routing by cluster was not really exercised; S11 shows UniRoute equal to ZeroRouter. Unit tests and WP-05 cover that logic.
- K-NN used an in-memory search, not Qdrant. The holdout demo and real calls are not covered.
- `results/wp08_full_data/embed_full.json` still holds the old near_dups block, kept as a record of the removed step.
