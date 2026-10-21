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
1. ⏸ **STOP:** ask the owner where the file is; copy it to `data/raw/full.json` (never open it, never
   commit). Propose the steps; wait for OK.
2. Structure-only data card (`scripts/data_card.py`) → `results/data_card_full.md`. Compare with the
   sample's schema; adapt the loader for new fields (log them). Counts: sessions, messages, date
   range, categories, models, providers, widgets, attachments, RAG, redaction hits.
3. S1 on the full data → exclusion table per reason; eligible prompts; share of huge-prompt turns
   (if > 15%: ⏸ ask the owner: raise the threshold or truncate; PLAN §6).
4. Decide sizes from PLAN §6: eligible ≥ 3,000 → val 400 / test 300; 1,500–3,000 → same sizes, K ≤ 6;
   < 1,500 → reduced plan (val 300 / test 200, K ≤ 6). Log the decision.
5. S2 split (seed 20261020) → `results/split_manifest.json` (counts per split × category × language;
   sha256 of the id lists). Check val ≈ test ≈ recent traffic (language, length, category): report a
   table with standardized differences. **Seal the test set:** test ids go only to
   `runs/s2/test_ids.sealed` (git-ignored) + their hash in the manifest; later code may only *use* it
   through `scripts/eval_test.py` (WP-19).
6. S4: embed train + val + test (`embed_input`) with jina-embeddings-v5-text-small (`clustering`
   adapter, D-048) → `runs/s4/` + Qdrant collection (payload ids/numbers only). Near-duplicate
   removal inside train via Qdrant search (cosine > 0.95, keep one); report counts.
7. S5: K-means on train for K ∈ {3…8} (+ K = 1); assign val and test to the nearest centroid; report
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
- [ ] At least K = 3 valid (each cluster ≥ 50 val prompts).
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
