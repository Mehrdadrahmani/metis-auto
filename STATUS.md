# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-02 · by session WP-09/10 close

## Now
- Current WP: **WP-11 Pilot decision**. WP-10 done with Opus labels, not human (D-098, DEV-14). $6.29 spent (dashboard)
- All stages except the pilot stay at $0 until Gate 2. K limit 9 (D-089). K = 8 names from Qwen3-8B (D-092). Val 400 until after the pilot (D-091).
- Model: default (Opus 5.5)

## Exact next step
Owner replaces the Metis key. Then `/start`, `work/WP-11-pilot-decision.md` step 1, with `runs/labeling/opus/opus_labels.parquet` as reference. Start from the items where Jev and the labels disagree. Both judges are under the Gate 2 line against those labels.

## Models (D-080, D-082, D-083; `configs/models.yaml`)
- Candidates: deepseek-v4-flash, gpt-5.6-luna, gemini-2.5-flash-lite (holdout), claude-sonnet-5-5 (anchor)
- Pilot only: deepseek-v4-pro next to Sonnet. Main judge: jev-latest (returned jev-1.14.0), pointwise and pairwise; terra dropped (D-101).

## Pilot results to carry into WP-11 (`results/pilot_run_stats.md`)
- Jev pairwise position consistency 0.755 (n = 400), under the Gate 2 line of 0.80; B chosen 443, A 291
- Spearman terra against jev 0.709 (n = 499). Test-retest n = 20: terra exact 0.65, within 1 point 1.00; jev mean gap 0.108; jev pairwise same verdict 1.00
- Answers: 500 of 500, none cut after rising limits 1,024, 2,048, 4,096 (D-095)
- Costs differ over 25% from the memo: generation about $9.70 (up 37%), terra judging about $13.30 (down 45%), `results/cost_estimate_v2.md`

## Waiting on the owner
- Replace the Metis key: the old one, pasted in chat, is still in use (D-096). Replace the Hugging Face token too
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
- Spent $6.29 of cap $60.00 (dashboard; ledger $5.87, formula misses about 7%, D-100). Approved so far: pilot $10.
- Rest with Jev only: about $13 (generation $9.70, Jev about $1, cache labels and live run $2.50).

## Recent decisions (full list in MASTER_LOG.md §2)
- D-102 Chat history to the judge from now on; pilot re-judge if money allows, about $0.25
- D-101 Terra dropped; Jev keeps pointwise and pairwise
- D-100 Real pilot spend $6.29
- D-098 Opus labels, not human (DEV-14)
- D-097 s7 pre-check prices only work not yet done
- D-096 Pilot run on the old Metis key (owner)
- D-095 Rising answer limits on cut answers only, all models
- D-094 Gate 1 passed: pilot limit $10, the rest at Gate 2
- D-093 Pilot: terra pointwise only, jev both
- D-092 K = 8 names based on Qwen3-8B
