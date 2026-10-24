# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-24 · by session WP-03b (part 1)

## Now
- Current WP: **WP-03b Persian clustering test** (in progress, step 1–4 of 6; then WP-05)
- Owner asked (2026-10-24): test only S4 embedding + S5 K-means on public Persian data (no LLM calls,
  $0). WP file `work/WP-03b-persian-clustering.md`; sources in `ref/docs/persian-datasets.md`.
- Done: `scripts/ext_download.py` (HF parquet; chat sets via HTTP range reads of the `language`
  column, because the datasets-server /filter API failed); 9 sources in `data/external/*.parquet`
  (Global-MMLU fa 14,042; INCLUDE 548; Persian ARC 7,787; ParsiNLU MC 2,460; Persian BBH 4,511;
  PerCoR 4,000; legal QA 3,000; med QA 3,000; lmsys fa 5,431). `scripts/s4_persian_cluster.py`
  (T1 mix ≤ 4,000/source, T2 Global-MMLU, T3 chat; K-means on 60 %, NMI/ARI/purity on 40 %).
  Nano run on benchmarks done (interim, chat incomplete): T1 NMI vs source 0.42 at K = 6;
  T2 NMI vs 57 subjects 0.50 at K = 57. Embeddings cached in `data/external/emb/`.
- Stopped cleanly for the owner's break (both jobs resume from cache):
  small embedding 16/41 chunks; chat download: Arena-140k done (7 files), Arena-100k + WildChat not.
- **Exact next step (WP-03b step 1–4):**
  1. `uv run python scripts/ext_download.py --only arena,wildchat` (background; ~10–20 min)
  2. `HF_HUB_OFFLINE=1 TRANSFORMERS_VERBOSITY=error uv run python scripts/s4_persian_cluster.py small`
     (~25 min), then the same with `nano` (chat part only, ~2 min); both again after step 1 if
     step 1 finished later (cache keeps old chunks).
  3. Optional reference: `... nano --task text-matching`.
  4. Write `results/persian_clustering.md` from `results/persian_clustering_{small,nano}.json`;
     ⏸ owner opens `runs/s4/persian_clusters_{small,nano}.html` (WP-03b step 5).
- Khayyam: owner asked the authors, access pending → add later (`ext_download.py` needs a
  `khayyam` source + `HF_TOKEN`). FarsEval-PKBETS (`MatinaAI/pkbets`) and PEKA are gated too.
- Model: default (Opus 5.5)

## Waiting on the owner
- Q-020 K-selection data: owner wants K "exactly like the paper" → paper = graded train prompts
  (~$14, breaks fixed rule 6) vs spec split-validation ($0). Confirm explicitly before WP-14.
- Q-023 Persian benchmark test (`ref/docs/persian-datasets.md`): option 1 ($0, persian-llm-eval
  per-item scores) could run after WP-05; option 2 paid, after the full data
- Q-017 (VPN / Metis AI reachability) before WP-04
- Approve DEV-4, DEV-5, DEV-6 (MASTER_LOG §2) when convenient

## Blockers / open issues
- Full dataset not arrived (Q-001); WP-08 and everything paid wait for it
- Metis AI unreachable from the planner's network (PLAN R17)
- GitHub secret scanning not available on the free private repo (Q-022); local pre-commit only
- HF "xet" downloads stall on this network; use `scripts/fetch_model.py` (plain HTTP, resumes)
- graphify graph has 170 dangling edges (doc→code name mismatches); usable

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-052 keep jina v5 small + nano; choose in WP-08; cache uses text-matching; merge_adapter
- D-051 graphify knowledge graph for the whole project (local AST + session subagents, no API)
- D-050 models stored in `models/<short>_<rev12>/` (git-ignored), loaded by local path, revision pinned

## Next WPs that can start
- WP-05 (free, synthetic); WP-04 after Q-017; WP-06 after WP-04
