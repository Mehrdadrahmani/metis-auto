# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-22 · by session WP-03 (part 1)

## Now
- Current WP: **WP-03 Embedder + Qdrant** (in progress, step 5 of 7)
- Done: steps 2–4b. Deps added (sentence-transformers, torch, qdrant-client, peft, scikit-learn,
  psutil). `src/metis/embed/embedder.py` (L2-norm float32, `task="clustering"`,
  `prompt_name="document"` = "Document: " as the model card, token-budget batching
  `max_batch_tokens=8192`, `embedder_id`), `src/metis/embed/store.py` (Qdrant local, payload
  ids/numbers only, exact search == numpy). Models downloaded to `models/` (git-ignored) by
  `scripts/fetch_model.py` (resumable curl): small `dd76d535f544`, nano `8a7f00aac812`.
  `scripts/s4_embed_bench.py` + 40 synthetic Persian pairs `scripts/data/persian_pairs.yaml`.
  99 tests pass.
- Not done: **step 5 benchmark has no valid numbers yet.** Run 1 was killed by memory (11 GB
  peak, batch 64 of long messages; fixed by token-budget batching). Run 2 was stopped because the
  Mac was on battery with **Low Power Mode on** (CPU p95 193/373/644 ms at 30/200/512 tok:
  throttled, not usable). MPS not measured yet. Nano not run yet.
- **Exact next step:** ask the owner to plug in + turn off Low Power Mode (`pmset -g | grep
  lowpowermode` must show 0), then run
  `HF_HUB_OFFLINE=1 TRANSFORMERS_VERBOSITY=error uv run python scripts/s4_embed_bench.py small`
  (~15–20 min; progress on stderr), then `... nano`; then write `results/embedder_benchmark.md`
  from the two JSONs and ⏸ ask the owner to open `runs/s4/cluster_samples_<model>.html` (WP-03 step 5).
- Model: default (Opus 5.5)

## Waiting on the owner
- Plug in / Low Power Mode off before the WP-03 benchmark
- Q-017 (VPN / Metis AI reachability) before WP-04; Q-020 (K selection) before WP-05
- Approve DEV-4, DEV-5, DEV-6 (MASTER_LOG §2) when convenient

## Blockers / open issues
- Full dataset not arrived (Q-001); WP-08 and everything paid wait for it
- Metis AI unreachable from the planner's network (PLAN R17)
- GitHub secret scanning not available on the free private repo (Q-022); local pre-commit only
- Nano is built on EuroBERT (Persian likely not in its training languages): weak latency fallback
  for Persian; if small misses 60 ms on MPS, ⏸ ask the owner (bge-m3 as reference)
- HF "xet" downloads stall on this network; use `scripts/fetch_model.py` (plain HTTP, resumes)

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-050 models stored in `models/<short>_<rev12>/` (git-ignored), loaded by local path, revision pinned
- D-049 Jina clustering input = "Document: " + message (model-card default, set explicitly)
- D-048 Jina v5-text-small (local, clustering adapter; nano fallback) + Qdrant local mode

## Next WPs that can start
- WP-03 continues; WP-04 and WP-05 in parallel (depend only on WP-00); WP-06 after WP-04
