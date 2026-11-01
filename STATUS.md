# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-01 · by session WP-08 part A review

## Now
- Current WP: **WP-08 part A: redo the split (all traffic), then K-means**
- Order (D-068): finish WP-08 part A → WP-04 → 06 → 07 → WP-08 part B (cluster names, budget, Gate 1).
- Kept: S1 (`runs/s1/`), nano vectors (`runs/s4/full/nano/`, 105 parts), Qdrant Docker (209,162 points).
- To be replaced: current split (RAG-balanced, recent pool), near-duplicates, K-means pages. Their
  numbers show the problem: val is 90.2% company support and 53.8% `b_1724`; all eligible prompts
  are 15.8% support. Gap val vs train 0.43.
- Owner chose the target: **all traffic** (D-074), the paper's random approach. No dates (owner rule).
- Router K candidates 3..20 (DEV-10, D-072). `k_max` is in config; pass it to `candidate_ks` in WP-14.
- Model: default (Opus 5.5)

## Exact next step (needs the owner's "go"; nothing has run)
Plan shown to the owner, not yet approved. Settings: random whole sessions from all eligible prompts,
val 400 (pilot 100), test 300, rest train, max 3 per session, no RAG balancing, near-duplicates
removed from train at 0.95, seed 20261020. If the owner says go:
1. Log DEV-11 (spec S2 says "most recent period"), update WP-08, `PLAN.md §11`.
2. `src/metis/data/split.py` `make_splits`: remove the recent pool (draw from all sessions), drop
   balancing, keep `max_per_session`; add tests. Config `s2.recent_pool_factor`, `balance_field`.
3. Move `runs/s2` to `runs/s2_old`; run `scripts/s2_split.py`; reseal test. Add bot purpose
   (`runs/bots/purpose.parquet`) to the similarity check.
4. Update the Qdrant `split` payload (`set_payload`), no re-embedding; prompts outside val and train
   stay `unassigned` so test is not labelled.
5. `scripts/s4_embed_full.py near-dups`, then `scripts/s5_cluster_view.py` (delete the old
   `clusters_by_k.json` first or it skips finished K). About 15 minutes, $0.
6. Report gap, val per cluster, stability. Then Qdrant snapshot for the owner's colleagues.
After that: `/start`, `work/WP-04-*.md` step 2 (mock mode).

## Waiting on the owner
- "Go" for the plan above, including its 3 defaults (limit 3, no RAG balancing, near-duplicates)
- Share with colleagues: Qdrant snapshot + `docker-compose.yml`, `configs/pipeline.yaml`,
  `embed_full.json`, after the new split. Never `runs/s1`, `runs/cluster_view`, `runs/bots`, sealed ids
- Chunking long messages over ~2,048 tokens (weighted mean of pieces): asked, not answered
- D-071 defaults to confirm: 11 long messages cut; hidden memory block left in place
- Rule for clusters with 0 val at K ≥ 16 (Q-028); val 400, 600 or 800 at Gate 1
- Before WP-04 Metis steps: Q-017 + key in `.env`. Before WP-06 step 4: judge prompt review; DEV-5
- Before WP-11: DEV-4. Replace the Hugging Face token (pasted in chat, still valid)

## Blockers / open issues
- With all traffic, support-only results will be noisy (about 63 val, 47 test); RAG about 19%
- Short chat prompts may give the judge little to separate models: check pilot separability
- A WP-07 bug in S1 rules means a free rerun (D-068); sample outputs are in `runs/sample/`
- Metis AI unreachable from the planner's network (PLAN R17); Docker Hub refused access
- GPU runs out of memory on the longest messages and hangs: use `--device cpu`
- Keep `bot purpose` counts approximate: keyword rules; 1,023 bots have no description
- GitHub secret scanning not available (Q-022); HF "xet" stalls, use `scripts/fetch_model.py`

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-074 Split target: all traffic, no dates; settings await "go"
- D-073 Agent may read redacted bot descriptions; `instructions` stays closed
- D-072 K candidates 3..20 (DEV-10)
- D-071 Embedder nano; long-message and hidden-block defaults
- D-069 Embedding input stays the current user message; options compared in WP-14
- D-068 New work order
