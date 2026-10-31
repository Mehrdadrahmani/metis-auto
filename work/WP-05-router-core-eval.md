# WP-05: Router core and evaluation library (S5, S8–S11), tested on synthetic data

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-05-router-core-eval.md; follow
> the session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~250k (split into 05a/05b if it grows) | – | $0 | WP-00 | WP-07, WP-14, WP-19 |

**Split 2026-10-31:** steps 2–6 are done (WP-05a); steps 7–10 run from
`work/WP-05b-baselines-stats-synthetic.md`. WP-05 is ticked when 05b finishes.

## Context
All the "free" math of UniRoute plus the baselines and statistics. It is written and **proven on
synthetic data where the right answer is known** before any real label exists, so the paid labels
are never wasted on buggy code. Decisions: ladder of routers (PLAN M1), R = 20 halvings (M13),
K ∈ {3…8} (+ K = 1 comparison), Eq. 12 with α = 0, nearest-centroid assignment (paper-faithful, DEV-7), bootstrap/McNemar/κ (§8).

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §1 (notation), §4 S5, S8-PT, S8-PW, S9, S10, S11, §5, §7, §8, §10,
  App. B (worked example).
- `PLAN.md` §1.1 M1, M2, M9, M13, M14; §8.

## Steps
1. Propose (say whether you'll split into 05a = steps 2–6, 05b = steps 7–10); ⏸ wait for OK.
2. `router/kmeans.py` (S5): K-means on train embeddings for each K (k-means++, `n_init` ≥ 10,
   seed); assign every prompt to its **nearest centroid** (Euclidean, = K-means assignment, paper
   §5.1); report per-cluster val counts (no K is dropped; empty cluster → model's overall error
   rate, logged); K = 1 comparison.
3. `router/fingerprints.py` (S8-PT): fail rate per cluster = **paper Eq. 12 (α = 0, default)**; α > 0 smoothing only as an option for robustness checks, per-cluster
   counts, SE; ceiling flag. `router/bt.py` (S8-PW): per-cluster Bradley–Terry vs anchor with α virtual
   ties (L-BFGS on the log-likelihood); **closed form** check (spec S8-PW); anchor row = 0.5.
4. `router/route.py` (§5): `route(x_emb, available, artifact, λ)` → model, all scores, k*; ties →
   cheaper; `next_best()` for failover/escalation.
5. `eval/metrics.py` (§7): Cost(λ), Quality(λ) for any router; upper Pareto envelope with linear
   interpolation; normalized **area**; **QNC**; operating point at a given λ.
6. `router/select_k.py` (S9, R = 20) and `router/select_lambda.py` (S10: grid {0} ∪ 60 log-spaced in
   [1e-3, 1e2]; quality mode and budget mode). Experiment mode: `dev`/`holdout` roles.
7. `eval/baselines.py`: always-best, always-cheapest, **ZeroRouter** (convex hull of (ĉ, val loss),
   randomized mixing per spec S11), **K-NN** (via `metis.embed.store` Qdrant exact search, D-048; k tuned by split-validation, candidate k ∈ {5, 10, 20,
   40, 80} capped by N_val/3), **logistic** per model on embeddings (C tuned by 5-fold CV on val;
   nice). All expose the same `predict_loss(x, h)` / routing interface.
8. `eval/stats.py`: paired bootstrap (10,000, seeded, **resampling whole sessions**, D-060; test it on correlated synthetic sessions) for differences of quality, cost and area;
   exact McNemar; Wilson CI; Cohen's κ; balanced accuracy; Spearman; criteria C (stability over
   halvings) and D (separability) from spec §P.
9. **Synthetic test bed** `tests/synthetic.py`: 3 well-separated Gaussian "prompt types" in 64-d,
   4 models with known fail rates per type (e.g. cheap fails 0.6 on type 2, 0.05 elsewhere; strong
   0.05 everywhere; costs 0.03, 0.05, 0.13, 1.0); 5,000 train, 400 val, 300 test. Tests:
   - K* = 3 is chosen; Ψ recovers the planted rates within 2 SE;
   - UniRoute area > ZeroRouter area (bootstrap CI excludes 0);
   - on a "no structure" variant (same rates in every type), UniRoute ≈ ZeroRouter (CI includes 0)
     and K* = 1 or the smallest K;
   - BT fit = closed form (|Δ| < 1e-6); α = 0 equals Eq. 12; anchor row 0.5;
   - spec App. B worked example reproduces the routing choices (C for chat, S for literature);
   - adding a mock model changes only its row and the λ choice.
10. `router/artifact.py` (S12): save/load a versioned artifact (JSON + `.npy`): method, τ/anchor,
    embedder_id, K*, centroids, cluster names, Ψ + counts, ĉ + price snapshot, λ + mode + target,
    chosen router type from the ladder, hashes (val set, gen_config, judge_config), build date.

## Outputs
- `src/metis/router/*`, `src/metis/eval/*`, `tests/test_router_*.py`, `tests/synthetic.py`,
  `results/synthetic_validation.md` (the curves and numbers of step 9).

## Acceptance checks
- [ ] All step-9 tests green.
- [ ] Every spec §10 item that can be tested without real data has a test.
- [ ] Runtime of S9 with R = 20, K ≤ 8, 60 λ values < 2 min on the Mac.

## If blocked
- BT optimizer unstable → use the closed form (anchor-only design is all we have) and log it.

## End of session
- `work/reports/WP-05-report.md` (what's implemented, any spec ambiguity resolved, test summary).
  Spec ambiguities → log as decisions for the owner (deviation IDs if they change behavior).

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-05 step n" (or create `WP-05b` with steps 7–10), stop.
