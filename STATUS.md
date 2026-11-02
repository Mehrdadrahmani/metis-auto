# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-02 · by session WP-07 dry run

## Now
- Current WP: **WP-08 Full data in, part B** (WP-07 done, all $0)
- WP-07 done: `scripts/pipeline.py` S1 to S12 on the sample, mock. Second run 0 new calls, identical hashes. Leak test 0 hits on 13,720 planted fake keys.
- Clusters redone on all train (D-088). K limit now 9 (D-089). Split rerun: same prompt sets.
- Gate 1 not passed. WP-07's cost check not met: estimate above PLAN high.
- Model: default (Opus 5.5)

## Exact next step
`/start`, then `work/WP-08-full-data-in.md` step 8: redo cluster names on the new clusters (`runs/cluster_view/index.html`, `configs/cluster_names.yaml`), then step 9 budget memo from `results/cost_estimate_v1.md`, then Gate 1.

## Models (D-080, D-082, D-083; `configs/models.yaml`)
- Candidates: deepseek-v4-flash, gpt-5.6-luna, gemini-2.5-flash-lite (holdout), claude-sonnet-5-5 (anchor)
- Pilot only: deepseek-v4-pro next to Sonnet. Judges in the pilot: gpt-5.6-terra and jev-latest. WP-11 decides both.

## Waiting on the owner
- Replace the Metis key: it was pasted in chat. Replace the Hugging Face token too (pasted, still valid)
- Check the Metis dashboard shows no charge for the list requests
- Share with colleagues: `qdrant/share/*.snapshot` (948 MB) + `docker-compose.yml`, `configs/pipeline.yaml`,
  `embed_full.json`. Never `runs/s1`, `runs/cluster_view`, `runs/bots`, sealed ids
- Cluster names now. Judge token cap at Gate 1. Budget: how to cut the over-estimate at Gate 1
- Val size: proposed to keep 400 and decide after the pilot (add sessions from train, never change `n_val`: that redraws test). Not confirmed
- Qwen 8B topic sample (500 per cluster, about 30 min, needs ~5 GB download): asked, not answered
- Chunking long messages over ~2,048 tokens (weighted mean of pieces): asked, not answered
- D-071 defaults to confirm: 11 long messages cut; hidden memory block left in place
- Before WP-11: DEV-4

## Blockers / open issues
- Not proven until the first paid call: chat through each Metis address, usage and cached-token reporting, rate limits. The Google and Grok wrapper addresses are not in the Metis docs
- **Budget:** simulated estimate pointwise $47.68 (over the $45 line), pairwise $62.12 (over the $60 cap), pilot $15.28. Decide at Gate 1 (WP-08, D-087). DeepSeek doubles at peak hours
- All temperature, thinking and reasoning params are unverified until WP-09; the Metis wrappers document none of them. Google route is undocumented
- Labeling tool: syntax checked only; the owner replied OK at step 8. Mock test answers show a model name, real ones do not
- Failed calls book $0, but a provider may bill them: compare the ledger with the invoice. Run one paid process at a time
- Val vs test differ on Persian share (0.132) and no-description bots (0.115), over the 0.1 limit: judged chance; no redraw
- Silhouette 0.05 to 0.12, clusters mixed; message-only routing may gain little (paper's Headlines case)
- Almost no code in the data (292 messages, 0.09%); router not tested on code
- New test prompts may have been in old train pages or samples; no labels used
- Short chat prompts may give the judge little to separate models: check pilot separability
- Dry run did not really exercise routing by cluster: sample train is 56 prompts, all val in one K = 3 cluster
- Docker Hub refused access. GPU runs out of memory on the longest messages: use `--device cpu`
- GitHub secret scanning not available (Q-022); HF "xet" stalls, use `scripts/fetch_model.py`

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4). List requests sent, no generation.

## Recent decisions (full list in MASTER_LOG.md §2)
- D-090 No S1 rules bug on record; names to redo; PLAN high exceeded
- D-089 K limit 9: stable to K = 9 only
- D-088 Near-duplicates kept: K-means on all train prompts
- D-087 WP-08, 09, 11, 12, 13 updated from WP-06 results
- D-086 Jev form approved; level mapped by 1 + 2.25 × level
- D-085 DEV-5 approved: judge prompts in `src/metis/judge/templates/`
