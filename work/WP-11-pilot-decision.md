# WP-11: Pilot decision (method, τ, bias and noise) ⛔ Gate 2

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-11-pilot-decision.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 3 | default (Opus 5.5) | ~150k | **Gate 2** approval; labels from WP-10 | $0 (≈ $2 only if one rubric revision) | WP-10 | WP-12, WP-13 |

## Context
Decide pointwise vs pairwise with evidence, set τ, and decide whether the grader is trustworthy
enough to spend the main budget. Rules agreed: method chosen by human agreement (spec criterion B)
**and** separability (D); ties → pointwise; τ by balanced accuracy; gate = agreement ≥ 75% and
κ ≥ 0.40 (PLAN M8, M9; DEV-3, DEV-4). Criteria A and C are computed and reported but not decisive.
All analysis uses numbers only; Claude does not read prompts or answers.

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §P (criteria A–D, decision rule), §4 S7-PT (τ), S8, §12.
- `PLAN.md` §1.1 M8–M11, §6 rows "pilot", "τ", "separability", "bias"; `work/reports/WP-09-report.md`.

## Steps
1. Propose; ⏸ wait for OK. Ingest `runs/labeling/cal_labels.csv` → `human_labels` (counts only).
2. **Pointwise:** for τ ∈ {4…9}: accuracy, balanced accuracy, κ vs `human_pass`; choose τ* by
   balanced accuracy (ties → higher τ). Report the pass rate of each model at τ*.
3. **Pairwise:** accuracy and κ of the judge verdict vs `human_pref` on non-tie items; position
   consistency (both orders agree) rate; tie rate.
4. **Separability (D)** and **stability (C)** for each method on the pilot val (K = 1 and K = 3 using
   the train clustering): fraction of separable (cluster, model-pair) cells; mean halving correlation.
   Cross-evaluation (A) on pilot val only, labeled "informative, underpowered".
5. **Bias and noise checks:** length bias (Spearman of score vs answer tokens within prompt; pairwise:
   win rate of the longer answer); self-preference (judge–human disagreement for gpt-5.6-luna vs the
   others, with counts); test–retest agreement from WP-09 step 5; owner intra-rater consistency if the
   re-label file is already done (otherwise add it later; it does not block the gate).
6. **Decide** with the rule: method with higher agreement (κ-based) that also has D ≥ 0.2; if both
   are close (κ difference < 0.05) → pointwise. Ceiling check: if > 90% pass for every model at τ*,
   try τ* + 1 (free, from stored scores) and report separability again.
7. ⏸ **⛔ Gate 2:** present a 10-line decision table to the owner (method, τ*, agreement, κ, D,
   position consistency, bias flags, cost of the main judging stage for that method).
   - Pass → owner approves; record.
   - Fail → one rubric revision (edit the template; DEV-5 note), re-judge the pilot only (needs a "go",
     ~$2), redo steps 2–6. Fail again → owner decides (another judge model / proceed with a documented
     weaker gate).
8. Write the choice into `configs/judge_config.yaml` (`method`, `tau`, anchor) and update
   `work/WP-13-judging.md` (which judging to run, call counts, estimate) and `work/WP-14-*.md`
   (method-specific S8).

## Outputs
- `results/pilot_decision.md` (all tables), updated configs and WP-13/14 files.

## Acceptance checks
- [ ] Decision follows the agreed rule; numbers reproducible from cached data (script, seed).
- [ ] Gate 2 outcome recorded in MASTER_LOG §Decisions with the numbers.

## If blocked
- Labels missing or incomplete (< 80 items) → wait; STATUS "waiting on owner".

## End of session
- `work/reports/WP-11-report.md`. If length bias |ρ| > 0.3 → add a length-controlled analysis to
  WP-19. If self-preference is visible → flag gpt-5.6-luna in WP-19 reporting.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-11 step n", stop.
