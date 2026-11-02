# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-02 · by session WP-09 pilot run

## Now
- Current WP: **WP-10 Owner labels** (human work). WP-09 done, $5.87 spent of the $10 pilot limit
- All stages except the pilot stay at $0 until Gate 2. K limit 9 (D-089). K = 8 names from Qwen3-8B (D-092). Val 400 until after the pilot (D-091).
- Model: default (Opus 5.5)

## Exact next step
Owner labels `runs/labeling/cal_2026-11-02.html` (100 items, ~3 h, `work/WP-10-*.md`), exports `runs/labeling/cal_labels.csv`. Not `cal_2026-11-01.html` (tool test). At least 2 days later: build and do the 20 re-labels with `labeling.build --relabel`. Then `/start`, `work/WP-11-pilot-decision.md` step 1.

## Models (D-080, D-082, D-083; `configs/models.yaml`)
- Candidates: deepseek-v4-flash, gpt-5.6-luna, gemini-2.5-flash-lite (holdout), claude-sonnet-5-5 (anchor)
- Pilot only: deepseek-v4-pro next to Sonnet. Judges in the pilot: gpt-5.6-terra and jev-latest (returned jev-1.14.0). WP-11 decides both.

## Pilot results to carry into WP-11 (`results/pilot_run_stats.md`)
- Jev pairwise position consistency 0.755 (n = 400), under the Gate 2 line of 0.80; B chosen 443, A 291
- Spearman terra against jev 0.709 (n = 499). Test-retest n = 20: terra exact 0.65, within 1 point 1.00; jev mean gap 0.108; jev pairwise same verdict 1.00
- Answers: 500 of 500, none cut after rising limits 1,024, 2,048, 4,096 (D-095)
- Costs differ over 25% from the memo: generation about $9.70 (up 37%), terra judging about $13.30 (down 45%), `results/cost_estimate_v2.md`

## Waiting on the owner
- Labels (WP-10)
- Replace the Metis key: the old one, pasted in chat, is still in use (D-096). Replace the Hugging Face token too
- Check the Metis dashboard and compare its charge with the ledger, $5.87
- Share with colleagues: `qdrant/share/*.snapshot` (948 MB) + `docker-compose.yml`, `configs/pipeline.yaml`, `embed_full.json`. Never `runs/s1`, `runs/cluster_view`, `runs/bots`, sealed ids
- Chunking long messages over ~2,048 tokens (weighted mean of pieces): asked, not answered
- D-071 defaults to confirm: 11 long messages cut; hidden memory block left in place
- Before WP-11: DEV-4

## Blockers / open issues
- `s6_generate.py` pre-check still prices cached work (D-097): fix before WP-12
- Reasoning tokens are not reported for Sonnet, DeepSeek and Gemini, so the guard cannot see them; Sonnet's chars per token fit its input ratio
- Failed calls book $0, but a provider may bill them. Run one paid process at a time
- Val vs test differ on Persian share (0.132) and no-description bots (0.115), over the 0.1 limit: judged chance; no redraw
- Silhouette 0.05 to 0.12, clusters mixed; message-only routing may gain little (paper's Headlines case)
- Almost no code in the data (292 messages, 0.09%); router not tested on code
- New test prompts may have been in old train pages or samples; no labels used
- Short chat prompts may give the judge little to separate models: check pilot separability
- Dry run did not really exercise routing by cluster: sample train is 56 prompts, all val in one K = 3 cluster
- Docker Hub refused access. GPU runs out of memory on the longest messages: use `--device cpu`
- GitHub secret scanning not available (Q-022); HF "xet" stalls, use `scripts/fetch_model.py`

## Money
- Spent $5.87 of cap $60.00 (ledger: MASTER_LOG.md §4). Approved so far: pilot $10.

## Recent decisions (full list in MASTER_LOG.md §2)
- D-097 s7 pre-check prices only work not yet done
- D-096 Pilot run on the old Metis key (owner)
- D-095 Rising answer limits on cut answers only, all models
- D-094 Gate 1 passed: pilot limit $10, the rest at Gate 2
- D-093 Pilot: terra pointwise only, jev both
- D-092 K = 8 names based on Qwen3-8B
