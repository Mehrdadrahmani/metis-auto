# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-01 · by session WP-04 LLM client, cache, budget

## Now
- Current WP: **WP-06 Generation + judge pipeline (mocked)** (WP-08 stays open, part B paused)
- WP-04 done: client with key guard, SQLite cache, budget guard (all stages $0), runner, mock mode, MLflow, Metis check, real prices.
- WP-08 part B: step 8 names are a draft until after WP-07 (owner). Step 9 is a draft, `results/budget_memo.md`; recompute it with the Metis prices. Gate 1 not passed.
- Order: WP-06 → 07 → finish WP-08 part B (names, memo, Gate 1). WP-07 also reruns the split (D-080) and fixes the S1 rules bug.
- Model: default (Opus 5.5)

## Exact next step
`/start`, then `work/WP-06-*.md` step 1 (propose). Include the added section: Jev adapter, and `redact_messages` when building requests.

## Models (D-080, D-082, D-083; `configs/models.yaml`)
- Candidates: deepseek-v4-flash, gpt-5.6-luna, gemini-2.5-flash-lite (holdout), claude-sonnet-5-5 (anchor)
- Pilot only: deepseek-v4-pro next to Sonnet. Judges in the pilot: gpt-5.6-terra and jev-latest. WP-11 decides both.

## Waiting on the owner
- Replace the Metis key: it was pasted in chat. Replace the Hugging Face token too (pasted, still valid)
- Check the Metis dashboard shows no charge for the list requests
- Before WP-06 step 4: judge prompt review; DEV-5
- Share with colleagues: `qdrant/share/*.snapshot` (948 MB) + `docker-compose.yml`, `configs/pipeline.yaml`,
  `embed_full.json`. Never `runs/s1`, `runs/cluster_view`, `runs/bots`, sealed ids
- Cluster names, after WP-07. Val 400, 600 or 800 at Gate 1. Judge token cap at Gate 1
- Chunking long messages over ~2,048 tokens (weighted mean of pieces): asked, not answered
- D-071 defaults to confirm: 11 long messages cut; hidden memory block left in place
- Before WP-11: DEV-4

## Blockers / open issues
- Not proven until the first paid call: chat through each Metis address, usage and cached-token reporting, rate limits. The Google and Grok wrapper addresses are not in the Metis docs
- `runs/s2` and `results/split_manifest.json` still name gemini-3.5-flash-lite for calibration: free rerun in WP-07
- Draft budget memo predates Metis prices and the swap. Above $45 triggers PLAN §6. DeepSeek doubles at peak hours
- Failed calls book $0, but a provider may bill them: compare the ledger with the invoice. Run one paid process at a time
- Val vs test differ on Persian share (0.132) and no-description bots (0.115), over the 0.1 limit: judged chance; no redraw
- Silhouette 0.05 to 0.12, clusters mixed; message-only routing may gain little (paper's Headlines case)
- Almost no code in the data (292 messages, 0.09%); router not tested on code
- New test prompts may have been in old train pages or samples; no labels used
- Short chat prompts may give the judge little to separate models: check pilot separability
- A WP-07 bug in S1 rules means a free rerun (D-068); sample outputs are in `runs/sample/`
- Docker Hub refused access. GPU runs out of memory on the longest messages: use `--device cpu`
- GitHub secret scanning not available (Q-022); HF "xet" stalls, use `scripts/fetch_model.py`

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4). List requests sent, no generation.

## Recent decisions (full list in MASTER_LOG.md §2)
- D-083 Pilot judges: gpt-5.6-terra and jev-latest side by side
- D-082 deepseek-v4-pro compared with Sonnet in the pilot
- D-081 Jev kept as a judge option
- D-080 gemini-2.5-flash-lite replaces gemini-3.5-flash-lite
- D-079 D-076 confirmed; near-duplicates stay 0.95; K 3..20 scored, only K ≤ 11 can win
