# WP-08: Full data in (S1–S5 on real data, splits locked, budget memo) ⛔ Gate 1

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-08-full-data-in.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 2 | default (Opus 5.5) | ~200k | provide the file; name clusters (~15 min); **approve the budget (Gate 1)** | $0 | full dataset, WP-07 | WP-09, WP-12, WP-17 (real pairs) |

## Context
The full dataset has arrived. Everything runs locally and free. The output decides the real sizes,
K range and budget (PLAN §6, first rows). The test set is created and **sealed** here: after this WP,
nobody looks at test prompts or test labels until WP-19.

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §4 S1, S2, S4, S5 (+ checks), §8.
- `PLAN.md` §2, §6 (rows "data size", "token counts", "huge prompts"), §7.
- `work/reports/WP-07-report.md`, `results/cost_estimate_v1.md`.

## Steps
> **Update 2026-11-01 (D-078, D-079):** step 8 draft names in `configs/cluster_names.yaml`, owner reviews after WP-07. Step 9 draft in `results/budget_memo.md`; redo with the WP-04 estimator. If the pointwise total stays above $45, PLAN §6 applies: decide a judge token cap at Gate 1.
> **Update 2026-11-01 (D-074, D-075, DEV-11):** part A's split redone: all traffic, random whole sessions, no dates, no RAG balancing. Step 3's recent-pool check and step 5's "recent traffic" comparison now mean all eligible prompts. Embeddings stay; near-duplicates and K-means rerun.
> **Update 2026-10-31 (D-068):** part A done early: steps 3 to 6 and K-means (step 7) on train, K = 3..20, after near-duplicates. Reports: `results/split_manifest.json`, `results/wp08_full_data/`. Part B after WP-07: rerun anything WP-07 changes, resolve Q-027/Q-028, then steps 8 to 10.
> **Update 2026-10-31:** steps 1–2 done early (D-058): data in `data/raw/metis/data/` (parquet, not `full.json`), loader `iter_sessions`, card `results/wp08_full_data/`. `load_with_report` accepts that folder. WP-08 still waits for WP-07.

1. ⏸ **STOP:** ask the owner where the file is; copy it to `data/raw/full.json` (never open it, never
   commit). Propose the steps; wait for OK.
2. Structure-only data card (`scripts/data_card.py`) → `results/data_card_full.md`. Compare with the
   sample's schema; adapt the loader for new fields (log them). Counts: sessions, messages, date
   range, categories, models, providers, widgets, attachments, RAG, redaction hits.
3. Before S1: extend `reply_image` to provider `imagination`; choose a balancing field (no category in the data); see `report/data_selection.md` §6. Add the counts to that report.
   S1 on the full data → exclusion table per reason (`workflow` excluded, D-057); eligible prompts; share of huge-prompt turns
   (if > 15%: ⏸ ask the owner: raise the threshold or truncate; PLAN §6).
   Report the share **among LLM replies** separately (on the sample all huge prompts were workflow
   turns, 0 of 375 LLM replies; WP-02 report). Check the recent pool capacity ≥ 3 × 700 and how many
   eligible prompts the 3-per-session cap leaves unused (81 on the sample).
4. Decide sizes from PLAN §6: eligible ≥ 3,000 → val 400 / test 300; 1,500–3,000 → same sizes, K ≤ 6;
   < 1,500 → reduced plan (val 300 / test 200, K ≤ 6). Log the decision.
5. S2 split (seed 20261020) → `results/split_manifest.json` (counts per split × category × language;
   sha256 of the id lists). Check val ≈ test ≈ recent traffic (language, length, category): report a
   table with standardized differences. **Seal the test set:** test ids go only to
   `runs/s2/test_ids.sealed` (git-ignored) + their hash in the manifest; later code may only *use* it
   through `scripts/eval_test.py` (WP-19).
6. S4 **embedder choice first (D-052):** rerun `scripts/s4_embed_bench.py small` and `... nano` on
   **train only** (never test): latency with `merge_adapter: true`, token stats, K-means readability;
   write `runs/s4/cluster_samples_<model>.html` from train prompts. ⏸ **STOP:** owner opens both
   pages (sample verdict was "partly", too small to judge) and picks small or nano (nano meets the
   60 ms budget, small ≈ 220 ms at 512 tokens; Persian pair AUC: nano ≥ small; WP-03b public Persian
   clustering: small ≈ nano within 0.015 NMI, nano 2.5× faster → clustering alone favours nano). Set
   `configs/pipeline.yaml` `s4.choice`; log D-xxx. Then embed train + val + test (`embed_input`) with
   the chosen model (`clustering` adapter, merged) → `runs/s4/` + Qdrant collection (payload
   ids/numbers only). Near-duplicate
   removal inside train via Qdrant search (cosine > 0.95, keep one); report counts. **Dropped by D-088: near-duplicates are kept.**
7. S5: K-means on train for K ∈ {3…20} (+ K = 1; DEV-10, D-072); assign val and test to the nearest centroid; report
   cluster sizes (train/val/test) per K (paper-faithful: no K is dropped; small clusters flagged).
8. Cluster naming: write `runs/s5/clusters_K<k>.html` (10 random redacted **train** prompts per
   cluster, for K = 3…6). ⏸ **STOP:** the owner opens it and types a short name per cluster
   (~15 min) into `configs/cluster_names.yaml`. Claude does not read the prompts.
9. Budget memo (`scripts/estimate_costs.py` with real token stats + Metis AI prices): per stage
   (pilot, gen_main, judge_main point **and** pair, re-judge, cache labels, live run), low/mid/high,
   assumptions, comparison with PLAN §7. Recommend per-stage approved amounts.
   ⏸ **⛔ Gate 1:** the owner approves; write the approved amounts into `configs/budget.yaml` and
   MASTER_LOG §Budget.
10. If any PLAN §6 row is triggered (sizes, budget, huge prompts), edit WP-09…WP-14 and WP-19 now.

## Outputs
- `results/data_card_full.md`, `results/split_manifest.json`, `results/s1_full_counts.md`,
  `results/clusters_full.md` (sizes + owner names; no text), `results/budget_memo.md`,
  `configs/{pipeline,budget,cluster_names}.yaml`.

## Acceptance checks
- [ ] No session in two splits (assert); val/test standardized differences < 0.1 on language,
      length, category (or explained).
- [ ] K candidates {3…20} computed (DEV-10); val cluster sizes recorded (no per-cluster minimum, D-054); any cluster with 0 val prompts logged.
- [ ] Gate 1 approved and recorded; approvals in `budget.yaml`.

## If blocked
- Data schema very different → stop after step 2, write what changed, ask the owner; update WP-01/02.
- Data much smaller than expected → reduced plan (PLAN P4), tell the owner before continuing.

## End of session
- `work/reports/WP-08-report.md` (data card summary, sizes decision, split table, clusters, budget).
  Log decisions: sizes, K range, approved budget. STATUS next: WP-09, owner to book ~3 h
  for WP-10 within a day of WP-09.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-08 step n", stop. Never leave the split half-written
(rerun step 5 from scratch instead).

## Added by D-087 (WP-06 cost estimate)
`results/cost_estimate_v1.md` (simulated, T_in 2,871): pointwise $47.68, pairwise $62.12, pilot with both judges $15.28. Pointwise is above $45, so PLAN §6 applies. Before Gate 1, rerun `scripts/estimate_costs.py` with the 6,000-token cut applied, then choose from: shorter judge input, drop the re-judge, use one judge in the pilot, smaller val.

## Added by D-090
Step 8: the draft names were made on the old clusters. Redo them on `runs/cluster_view/`. Only K <= 9 can ship (D-089).
