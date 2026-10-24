# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-24 · by session WP-03 (part 2)

## Now
- Current WP: **WP-05 Router core + evaluation** (not started; WP-03 done, embedder choice → WP-08)
- WP-03 done: benchmark in `results/embedder_benchmark.md`, report `work/reports/WP-03-report.md`.
  Only nano meets 60 ms p95 at 512 tok (59 ms, MPS, `merge_adapter=True`; small 221 ms). Persian
  pair AUC weak with `clustering` (0.61 / 0.66); `text-matching` better (0.76 / 0.85) → cache
  adapter. Owner keeps **both** models; choice in WP-08 step 6 on train data (D-052).
  `configs/pipeline.yaml` `s4:` holds both candidates (`choice: pending`). 100 tests pass.
- graphify added for the whole project (D-051): query `graphify query "<q>"` before grepping;
  git hooks rebuild the code graph on commit. Docs part last rebuilt 2026-10-24 (before this
  handoff's doc edits): run `/graphify . --update` when docs changed a lot.
- **Exact next step:** `/start` WP-05 (`work/WP-05-router-core-eval.md` step 1: propose, ⏸ wait).
  WP-05 is $0, synthetic data only. Q-020 is not needed for WP-05's code (both K-selection data
  sources can be implemented); it is needed by WP-14.
- Model: default (Opus 5.5)

## Waiting on the owner
- Q-020 K-selection data: owner wants K "exactly like the paper" → paper = graded train prompts
  (~$14, breaks fixed rule 6) vs spec split-validation ($0). Confirm explicitly before WP-14.
- Q-023 Persian benchmark test (`ref/docs/persian-datasets.md`): option 1 ($0, persian-llm-eval
  per-item scores) could run after WP-05; option 2 paid, after the full data
- Q-017 (VPN / Metis AI reachability) before WP-04
- Approve DEV-4, DEV-5, DEV-6 (MASTER_LOG §2) when convenient

## Blockers / open issues
- Full dataset not arrived (Q-001); WP-08 and everything paid wait for it
- Metis AI unreachable from the planner's network (PLAN R17)
- GitHub secret scanning not available on the free private repo (Q-022); local pre-commit only
- HF "xet" downloads stall on this network; use `scripts/fetch_model.py` (plain HTTP, resumes)
- graphify graph has 170 dangling edges (doc→code name mismatches); usable

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-052 keep jina v5 small + nano; choose in WP-08; cache uses text-matching; merge_adapter
- D-051 graphify knowledge graph for the whole project (local AST + session subagents, no API)
- D-050 models stored in `models/<short>_<rev12>/` (git-ignored), loaded by local path, revision pinned

## Next WPs that can start
- WP-05 (free, synthetic); WP-04 after Q-017; WP-06 after WP-04
