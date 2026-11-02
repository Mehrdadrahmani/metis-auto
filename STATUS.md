# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-02 · validation done, team branch

## Now
- WP-12 done. WP-13: **validation done, test left** (D-109). Gate 2 failed by one item, owner went ahead (D-105). About $18.76 spent
- Branch `TakRoute` holds this work, for the team. Team repo push waits for the owner
- Judge: pointwise jev with history, τ = 7, `configs/judge_choice.yaml`. Val stays 400 (D-108). K limit 9 (D-089). K = 8 names from Qwen3-8B (D-092)
- Model: default (Opus 5.5)

## Exact next step
WP-13 test judging: let `s7_judge.py` take the test set with `.sealed` outputs, write `labels_test.sealed.parquet`, show about $0.30, wait for "go". Then WP-14, starting with the free router check on validation.

## Validation results (`results/s6_stats.md`, `results/s7_stats.md`; n = 400)
- Pass at 7: Sonnet 65.2%, DeepSeek 64.9%, Luna 61.2%, Gemini 53.9%. All pass 41%, all fail 21%, best possible 79%
- 1 Sonnet answer failed, 1 prompt refused by Jev. Repeat check n = 80, mean gap 0.147

## Models (D-080, D-082, D-107; `configs/models.yaml`)
- Candidates: deepseek-v4-flash, gpt-5.6-luna, gemini-2.5-flash-lite (holdout), claude-sonnet-5-5 (anchor)
- Judge: jev-latest (returned jev-1.14.0), pointwise only (D-106). Keep judge config id 356e63e52245: do not edit `judge_config.yaml` or the templates

## Gate 2 numbers (`results/pilot_decision.md`; n = 100, Opus labels, not human)
- Pointwise: agreement 0.74 (line 0.75), kappa 0.431, AUC 0.79. Pairwise: kappa 0.285, position consistency 0.738
- Separability 0.333 at K = 1, 0.111 at K = 3. No length bias. Gemini over-passed 8 to 3
- Report must state the miss, the Opus labels, and that the wrong-prompt test and 20 re-labels were not done

## Waiting on the owner
- Replace the Metis key again when possible: the new one was pasted in chat too (D-104). Replace the Hugging Face token too
- Share with colleagues: `qdrant/share/*.snapshot` (948 MB) + `docker-compose.yml`, `configs/pipeline.yaml`, `embed_full.json`. Never `runs/s1`, `runs/cluster_view`, `runs/bots`, sealed ids
- Chunking long messages over ~2,048 tokens: owner says no new token limit yet (2026-11-02); revisit later
- D-071 defaults to confirm: 11 long messages cut; hidden memory block left in place

## Blockers / open issues
- `graphify update .` refuses to overwrite (saved semantic nodes missing): graph is behind the code
- The exact Metis error for an empty balance is unknown; generic failure stop is the backup (D-110)
- Reasoning tokens are not reported for Sonnet, DeepSeek and Gemini, so the guard cannot see them; Sonnet's chars per token fit its input ratio
- Failed calls book $0, but a provider may bill them. Run one paid process at a time
- Val vs test differ on Persian share (0.132) and no-description bots (0.115), over the 0.1 limit: judged chance; no redraw
- Silhouette 0.05 to 0.12, clusters mixed; message-only routing may gain little (paper's Headlines case)
- Almost no code in the data (292 messages, 0.09%); router not tested on code
- New test prompts may have been in old train pages or samples; no labels used
- Pilot separability is weak (0.111 at K = 3): compare with ZeroRouter early in WP-14; report the negative case plainly if needed (P6)
- Dry run did not really exercise routing by cluster: sample train is 56 prompts, all val in one K = 3 cluster
- Docker Hub refused access. GPU runs out of memory on the longest messages: use `--device cpu`
- GitHub secret scanning not available (Q-022); HF "xet" stalls, use `scripts/fetch_model.py`

## Money
- Spent about $18.76 of cap $60.00. Approved: pilot $10, gen_main $14, judge_main $1
- Rest: about $3 (Jev test $0.30, cache labels and live run $2.50). Total about $21.60. Each stage needs a "go"

## Recent decisions (full list in MASTER_LOG.md §2)
- D-113 Team branch `TakRoute`
- D-112 Val labels, refused prompt unlabeled
- D-111 Sonnet estimate from measured price
- D-110 Account stop and resume
- D-109 Validation first, test waits
- D-108 Val stays 400
- D-107 Sonnet stays; no deepseek-v4-pro, no Qwen
- D-106 Main judging pointwise only; terra out
- D-105 Gate 2 failed by one item, owner went ahead on record
- D-104 `tpsg-` key pattern; new key in `.env`
