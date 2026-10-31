# WP-05b: Baselines, statistics, synthetic proof, artifact (steps 7–10 of WP-05)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-05b-baselines-stats-synthetic.md;
> follow the session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~150k | – | $0 | WP-05 steps 2–6 (done) | WP-07, WP-14, WP-19 |

## Context
Split from `WP-05-router-core-eval.md` at a clean step (owner OK, 2026-10-31). Steps 2–6 are done:
`router/kmeans.py`, `fingerprints.py`, `bt.py`, `route.py`, `select_k.py`, `select_lambda.py`,
`eval/metrics.py`, tests `tests/test_router_core.py`, `tests/test_router_select.py`.
Decided: split-validation (Q-020), R = 20 (DEV-6), K = 1 comparison only, halvings keep sessions
whole (D-061, D-062).

## Read (only these)
- `work/WP-05-router-core-eval.md` steps 7–10, Outputs, Acceptance checks.
- `ref/UNIROUTE_PIPELINE.md` §P (criteria C, D), S11, S12.
- `PLAN.md` §8.3. `src/metis/embed/store.py` (K-NN, Qdrant exact search).
- Function signatures in `src/metis/eval/metrics.py`, `src/metis/router/select_k.py`.

## Steps
Do steps 7–10 of the WP-05 file: `eval/baselines.py`, `eval/stats.py`, `tests/synthetic.py`,
`router/artifact.py`.

## Must check in step 9 (found in WP-05a)
- **Lucky-envelope effect.** The area keeps the best points of the scored half, so extra clusters
  get extra chances of a lucky score even with no real structure. On 5 no-structure datasets
  (400 prompts, K = 3 random labels) K = 3 beat K = 1 once (seed 1: 0.7557 vs 0.7488). Run the
  "no structure" variant on many seeds and report how often K* is the smallest K and how large the
  false gain in area is. If the bias is material, log it for the owner: do not change the rule alone.
- `test_s9_runtime_under_two_minutes` passes at 0.05 s; keep it in the acceptance list.
- In the planted-data helpers, never draw the labels with the same seed as the data: the "random"
  labels then equal the true groups.

## End of session
`work/reports/WP-05-report.md` covering both parts, `results/synthetic_validation.md`, tick WP-05
in `ROADMAP.md`.
