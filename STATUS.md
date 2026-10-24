# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-25 · by session WP-03b (part 2, overnight)

## Now
- Current WP: **WP-03b Persian clustering test** (steps 1–5 done; waiting at the step-5 ⏸; then WP-05)
- Owner asked (2026-10-24/25): do what the UniRoute paper does for embedding + clustering, with Jina
  instead of Gecko; $0, no LLM calls. Done overnight (D-053).
- Done: HF login works (`hf auth login`, user MehrdadRahmanigermi; token only in the user's HF cache);
  `ext_download.py` sends it to huggingface.co only. Khayyam downloaded (20,805; 38 categories).
  Arena + WildChat finished. All 12 sources in `data/external/*.parquet`.
- `scripts/s4_persian_cluster.py` = paper protocol (train 60 % / val 400 / test, 10 repeats, K-means on
  train, K = 3..8 + reference K; Khayyam human-difficulty gap); embeddings in
  `data/external/emb/<model>_<task>/store/` (text-hash keyed). `scripts/s4_cluster_plots.py` = figures.
- Results: `results/persian_clustering.md` (+ JSON, `results/figures/persian_*.png`). Headlines:
  mix clusters well, one topic not (paper's EmbedLLM vs Headlines reproduced); small ≈ nano (nano 2.5×
  faster); clusters cut the human-error gap ~5–6 %; val 400 limits K.
- **Exact next step (WP-03b step 5 ⏸ → 6):**
  1. Owner reads `results/persian_clustering.md` and opens `runs/s4/persian_map_{nano,small}.html`
     (interactive, hover = text) and `runs/s4/persian_clusters_{nano,small}.html` (8 prompts/cluster).
  2. Owner answers Q-024 (S5 cluster-size rule) and says what changes; log decisions; update Q-023;
     write `work/reports/WP-03b-report.md`; tick ROADMAP; `/handoff`. Then WP-05.
- Model: default (Opus 5.5)

## Waiting on the owner
- WP-03b step-5 review (above) and **Q-024**: every val cluster ≥ 50 (spec; leaves K = 3–4 at val 400)
  vs paper's K ≤ N_val/50 + α-smoothing. Needed by WP-14.
- Q-020 K-selection data: owner wants K "exactly like the paper" → paper = graded train prompts
  (~$14, breaks fixed rule 6) vs spec split-validation ($0). Confirm explicitly before WP-14.
- Q-023 Persian benchmark test option 1 ($0, persian-llm-eval per-item scores) after WP-05;
  option 2 paid, after the full data
- Q-017 (VPN / Metis AI reachability) before WP-04
- Approve DEV-4, DEV-5, DEV-6 (MASTER_LOG §2) when convenient

## Blockers / open issues
- Full dataset not arrived (Q-001); WP-08 and everything paid wait for it
- Metis AI unreachable from the planner's network (PLAN R17)
- GitHub secret scanning not available on the free private repo (Q-022); local pre-commit only
- HF "xet" downloads stall on this network; use `scripts/fetch_model.py` (plain HTTP, resumes)
- graphify graph has dangling edges (doc→code name mismatches); usable
- FarsEval-PKBETS, PEKA still gated (not requested)

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-053 WP-03b follows the paper's embedding + K-means protocol (Jina for Gecko); HF login for Khayyam
- D-052 keep jina v5 small + nano; choose in WP-08; cache uses text-matching; merge_adapter
- D-051 graphify knowledge graph for the whole project (local AST + session subagents, no API)

## Next WPs that can start
- WP-05 (free, synthetic); WP-04 after Q-017; WP-06 after WP-04
