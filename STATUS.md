# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-02 · by session WP-07 dry run

## Now
- Current WP: **WP-09 Pilot run** (first paid stage). WP-07 and WP-08 done, Gate 1 passed
- Pilot limit $10, estimate $6.71 (D-094): 5 models × 100 prompts; terra pointwise only, jev both methods (D-093, DEV-13). All other stages $0 until Gate 2.
- K limit 9 (D-089). K = 8 names from Qwen3-8B (D-092). Val 400 until after the pilot (D-091).
- Model: default (Opus 5.5)

## Exact next step
Owner replaces the Metis key first. Then `/start`, `work/WP-09-pilot-run.md` step 1, the one-call-per-route check (D-087 section), after the owner's "go".

## Models (D-080, D-082, D-083; `configs/models.yaml`)
- Candidates: deepseek-v4-flash, gpt-5.6-luna, gemini-2.5-flash-lite (holdout), claude-sonnet-5-5 (anchor)
- Pilot only: deepseek-v4-pro next to Sonnet. Judges in the pilot: gpt-5.6-terra and jev-latest. WP-11 decides both.

## Waiting on the owner
- Replace the Metis key: it was pasted in chat. Replace the Hugging Face token too (pasted, still valid)
- Check the Metis dashboard shows no charge for the list requests
- Share with colleagues: `qdrant/share/*.snapshot` (948 MB) + `docker-compose.yml`, `configs/pipeline.yaml`,
  `embed_full.json`. Never `runs/s1`, `runs/cluster_view`, `runs/bots`, sealed ids
- Before WP-09: the owner says "go" for the paid run
- Chunking long messages over ~2,048 tokens (weighted mean of pieces): asked, not answered
- D-071 defaults to confirm: 11 long messages cut; hidden memory block left in place
- Before WP-11: DEV-4

## Blockers / open issues
- Not proven until the first paid call: chat through each Metis address, usage and cached-token reporting, rate limits. The Google and Grok wrapper addresses are not in the Metis docs
- **Budget:** simulated mid case pointwise $41.61, pairwise $56.05; high $59.49, $78.08 (`results/budget_memo.md`). DeepSeek doubles at peak hours
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
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4). Approved so far: pilot $10.

## Recent decisions (full list in MASTER_LOG.md §2)
- D-094 Gate 1 passed: pilot limit $10, the rest at Gate 2
- D-093 Pilot: terra pointwise only, jev both
- D-092 K = 8 names based on Qwen3-8B
- D-091 Val 400 until after the pilot; Qwen3-8B topic sample per cluster
- D-090 No S1 rules bug on record; names to redo; PLAN high exceeded
- D-089 K limit 9: stable to K = 9 only
- D-088 Near-duplicates kept: K-means on all train prompts
