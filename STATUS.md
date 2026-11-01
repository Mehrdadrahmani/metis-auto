# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-01 · by session WP-08 redo and part B start

## Now
- Current WP: **WP-04 LLM client, call cache, budget** (WP-08 stays open, part B paused)
- WP-08 part A done: new split (DEV-11, D-075, D-076), near-duplicates, K-means 3..20, stability, Qdrant updated.
- WP-08 part B: step 8 names are a draft until after WP-07 (owner). Step 9 is a draft, `results/budget_memo.md`; it needs the WP-04 estimator and Metis prices. Gate 1 not passed.
- Order: WP-04 → 06 → 07 → finish WP-08 part B (names, memo, Gate 1). WP-07's S1 fix may mean a free rerun of split and clusters.
- Bot clusters kept for a free WP-14 test (D-078, `experiments/bot_clusters/`, section in WP-14 file).
- Model: default (Opus 5.5)

## Exact next step
`/start`, then `work/WP-04-*.md` step 2 (deps), step 3 needs the owner's Metis key, then steps 4 to 8 with mock mode. `configs/budget.yaml` does not exist yet.

## Waiting on the owner
- Before WP-04 Metis steps: Q-017 + key in `.env`. Before WP-06 step 4: judge prompt review; DEV-5
- Share with colleagues: `qdrant/share/*.snapshot` (948 MB) + `docker-compose.yml`, `configs/pipeline.yaml`,
  `embed_full.json`. Never `runs/s1`, `runs/cluster_view`, `runs/bots`, sealed ids
- Cluster names, after WP-07. Val 400, 600 or 800 at Gate 1. Judge token cap at Gate 1
- Chunking long messages over ~2,048 tokens (weighted mean of pieces): asked, not answered
- D-071 defaults to confirm: 11 long messages cut; hidden memory block left in place
- Before WP-11: DEV-4. Replace the Hugging Face token (pasted in chat, still valid)

## Blockers / open issues
- Draft budget: pointwise low $13, mid $35, high $73 (over cap). Judge price is a guess. Above $45 triggers PLAN §6
- Val vs test differ on Persian share (0.132) and no-description bots (0.115), over the 0.1 limit: judged chance; no redraw
- Silhouette 0.05 to 0.12, clusters mixed; message-only routing may gain little (paper's Headlines case)
- Almost no code in the data (292 messages, 0.09%); router not tested on code
- New test prompts may have been in old train pages or samples; no labels used
- Short chat prompts may give the judge little to separate models: check pilot separability
- A WP-07 bug in S1 rules means a free rerun (D-068); sample outputs are in `runs/sample/`
- Metis AI unreachable from the planner's network (PLAN R17); Docker Hub refused access
- GPU runs out of memory on the longest messages and hangs: use `--device cpu`
- GitHub secret scanning not available (Q-022); HF "xet" stalls, use `scripts/fetch_model.py`

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-079 D-076 confirmed; near-duplicates stay 0.95; K 3..20 scored, only K ≤ 11 can win
- D-078 Bot clusters kept as a later WP-14 test; part B started early
- D-077 Agent may read any data and results, through redaction; test stays sealed
- D-076 Val and test: each eligible prompt equally likely; sessions in one split
- D-075 Go for new split (DEV-11)
- D-074 Split target: all traffic, no dates
