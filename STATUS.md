# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-03 · WP-14 mid (handoff 2)

## Now
- Current WP: **WP-14 Fingerprints, settings, freeze**. Val grown to 800 (D-115). Test answers and labels sealed, unread. About $28.07 spent
- Branch `TakRoute`, remotes `origin` (owner) and `team`
- Judge: pointwise jev with history, τ = 7. Pairwise on val 800 is a second view only (D-116)
- Router: K = 8 by owner (D-117), K = 4 by the rule as comparison. λ open (D-118 proposal). Nothing frozen, no `pre-test` tag
- Model: default (Opus 5.5)

## Exact next step
`/start`, then WP-14: run `uv run python scripts/s12_input_test.py` (D-069; written, stopped before it finished, slow on CPU). Then sealed-file guard, artifact (`router/artifact.py`, `artifacts/router_v1/`), draft `results/eval_protocol.md`, charts. **Stop before `git tag pre-test`: owner approves.** Owner's overnight list: all free WPs, visuals, pitch deck. Khayyam run waits for "go khayyam" (no Sonnet; Gemini, DeepSeek flash, Luna, deepseek-v4-pro; 400 val + 1,100 test, $2 to $4, limit $5; true answers, no judge).

## Validation results (`results/router_check_val.md`, `select_k.md`, `ladder_val.md`, `lambda_val.md`; n = 798)
- Pass at 7: Sonnet 66.2%, DeepSeek 65.4%, Luna 61.5%, Gemini 53.5%. Perfect router 79.4%
- Area: K = 4 0.6634, K = 3 0.6629, K = 1 and ZeroRouter 0.6545, K = 8 0.6522, K-NN 0.6636, logistic 0.6532
- Cheap setting, unseen: K = 8 65.4% at cost 0.042; DeepSeek 65.4% at 0.041. K = 4 at λ 0.03: 66.9% at 0.417
- K = 8 fitted on old 400, scored on new 400: -2.0 points vs DeepSeek (-4.2 to 0.0)
- Signals (`results/signal_tests.md`): bot groups, RAG, language, length: none clearly beats K = 1 or chance; none beats DeepSeek at low cost. D-078 not shipped
- Pairwise, 0.5 = equal to Sonnet: DeepSeek 0.403, Luna 0.409, Gemini 0.176; Sonnet wins 40% to 21% over DeepSeek. Position consistency 0.753
- 2 prompts refused by Jev, 1 Sonnet answer failed. Repeat check n = 160, mean gap 0.119

## Models (D-080, D-082, D-107; `configs/models.yaml`)
- Candidates: deepseek-v4-flash, gpt-5.6-luna, gemini-2.5-flash-lite (holdout), claude-sonnet-5-5 (anchor)
- Judge: jev-latest. Keep judge config id 356e63e52245: do not edit `judge_config.yaml` or the templates

## Gate 2 numbers (`results/pilot_decision.md`; n = 100, Opus labels, not human)
- Pointwise: agreement 0.74 (line 0.75), kappa 0.431, AUC 0.79. Pairwise: kappa 0.285
- Report must state the miss, the Opus labels, and that the wrong-prompt test and 20 re-labels were not done

## Waiting on the owner
- Gate 3: approve router (K, λ, DEV-16), protocol with always-DeepSeek as a main comparison, then `pre-test`
- Replace all Metis keys: both spares were pasted in chat. One spare is in `.env`, the original ran out. Replace the Hugging Face token too
- "go" for WP-17 cache labels (≤ $1) and WP-19 live run (~$1.50)
- Share with colleagues: `qdrant/share/*.snapshot` + `docker-compose.yml`, `configs/pipeline.yaml`, `embed_full.json`. Never `runs/s1`, `runs/cluster_view`, `runs/bots`, sealed ids
- K = 4 cluster names stale (D-088) if K = 4 ships. D-071 defaults to confirm

## Blockers / open issues
- `graphify update .` refuses to overwrite (saved semantic nodes missing): graph is behind the code
- Qdrant still has the old train/val payload for 391 moved sessions: refresh before K-NN or gateway use
- Failed calls book $0, but a provider may bill them. Run one paid process at a time
- Router on val shows no gain over DeepSeek at low cost: report plainly (P6)
- Val vs test differ on Persian share and no-description bots; judged chance. Almost no code in the data
- Length bias not tested on pairwise at 800
- GPU runs out of memory on the longest messages: use `--device cpu`. HF "xet" stalls: use `scripts/fetch_model.py`

## Money
- Spent about $28.07 of cap $60. Approved: pilot $10, gen_main $21.50, judge_main $3
- Rest planned: about $2.50 (cache labels, live run). Each stage needs a "go"

## Recent decisions (full list in MASTER_LOG.md §2)
- D-118 λ out of fold, proposed (DEV-16)
- D-117 K = 8 by owner, K = 4 comparison
- D-116 Pairwise on val 800, second view
- D-115 Val 800 from train sessions (DEV-15)
- D-114 WP-14 protocol notes
- D-113 Team branch `TakRoute`
- D-112 Val labels, refused prompt unlabeled
