# WP-14: Fingerprints, K, λ, router ladder, freeze (S8–S10, S12) ⛔ Gate 3

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-14-fingerprints-freeze.md; follow
> the session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 4 | default (Opus 5.5) | ~250k | read the protocol before the freeze | $0 | WP-05, WP-13 | WP-18, WP-19 |

## Context
Everything here uses **validation labels only**. It produces the router that the gateway ships and
the evaluation protocol, then freezes both with a git tag before anyone opens the test set (PLAN M16).
Expect small K (3–5) and honest uncertainty (§8.2). **Every clustering and routing step follows the
paper** (PLAN M1, M14; DEV-7): UniRoute ships; the baselines are reported for comparison only.

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §4 S8 (chosen method), S9, S10, S11 (method table only), S12, §10, §12.
- `PLAN.md` §1.1 M1, M2, M4, M5, M13–M16; §8.
- `work/reports/WP-11-report.md`, `WP-13-report.md`, `results/clusters_full.md`.

## Steps
1. Propose; ⏸ wait for OK.
2. **S8** for K ∈ {3…8}: **Eq. 12, α = 0** (α = 2 only as a robustness row): Ψ table with counts and Wilson CIs;
   ceiling flags; cluster names from `configs/cluster_names.yaml`.
3. **S9** choose K* = the K with the largest **normalized area under the deferral curve** (paper App.
   G.2), using the K-selection data decided in **Q-020** (paper: report cards from graded train
   prompts, routed on validation; or spec: split-validation halvings of validation). Ties → smaller K.
   Plot area vs K.
4. **Baselines on validation (comparison only):** always-cheapest, always-best, ZeroRouter, K-NN
   (k tuned as in App. G.2: candidates 5 … N_val/3). Report area and QNC next to UniRoute's. UniRoute
   ships regardless (M1).
5. (removed: the instruction-traits test was withdrawn, DEV-1.)
6. **S10 λ:** quality mode with target = always-best's val quality minus 2 points (PLAN §8.2 target);
   also budget mode at 50% of always-best's cost. Record λ for both; the **primary** operating point
   is quality mode.
7. **Holdout demo (M4):** redo S9–S10 with gemini-3.5-flash-lite hidden (`dev` = the other 3); then add it
   back using only its validation fingerprint row; show its routing share and the val curve before/after.
8. Assemble the S12 **artifact v1** (`router/artifact.py`) incl. the λ
   values; copy it to `artifacts/router_v1/` (committed: centroids, Ψ, ĉ, configs, hashes; no text).
9. **Evaluation protocol** `results/eval_protocol.md`: primary comparison and success criteria from
   PLAN §8.2 (exact numbers), secondary analyses, the ladder, the λ to use, bootstrap settings,
   per-category/per-cluster tables, production similarity, length-controlled analysis if WP-11 asked
   for it, holdout demo, replay settings. ⏸ owner reads it (≤ 1 page) before the freeze.
10. **⛔ Gate 3:** commit, `git tag pre-test`, push the tag. From now on, any change to the artifact
    or protocol must be logged as a deviation in WP-19.

MLflow (D-044): log every K (step 2–3), baseline (4), λ choice (6) and the holdout demo (7) as an
MLflow run in experiment `router-selection` (params: method, K, α, λ, config ids; metrics: area,
QNC, quality, cost; plots as artifacts), so the owner can compare them in the UI. Validation only:
nothing from the test set is logged before `pre-test`.

## Outputs
- `results/{fingerprints,select_k,ladder_val,representation_test,holdout_demo}.md` + figures,
  `artifacts/router_v1/`, `results/eval_protocol.md`, tag `pre-test`.

## Acceptance checks
- [ ] Spec §10 (n_min check replaced by K ≤ N_val/50, D-054); method/τ chosen without test; α = 0 reproduces Eq. 12 (or BT
      closed form = fit); mock-model add touches one row; rerun = cache hits.
- [ ] No file under `runs/s7/*.sealed*` was opened (assert in code: the loader refuses sealed files
      unless called from `scripts/eval_test.py`).
- [ ] Tag `pre-test` exists on GitHub.

## If blocked
- All K > 1 invalid (clusters too small) → K = 1 only; UniRoute = ZeroRouter-like; report as a
  finding; still freeze.

## End of session
- `work/reports/WP-14-report.md` (Ψ table, K*, ladder table, λ, chosen router, holdout demo,
  baseline comparison). Update WP-15/16 config notes (artifact path), WP-18, WP-19.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-14 step n", stop. Never tag `pre-test` in a hurry:
it can wait for the next session.

## Notes from WP-05
- K: highest score, split-validation, R = 20, sessions kept whole (D-061, D-064, D-065). Do not
  present K* as the number of real topics.
- Decide in the evaluation protocol: QNC exact, or within 1 point (exact can read "never reached"
  over one prompt in 300). Report both until then.
- Logistic baseline is pointwise only.
