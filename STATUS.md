# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-31 · by session WP-08 part A

## Now
- Current WP: **WP-08 part A review, then WP-04 LLM client, call cache, budget** (mock mode allowed)
- New order (D-068): WP-08 part A → WP-04 → 06 → 07 → WP-08 part B (cluster names, budget, Gate 1).
- WP-08 part A done on the full data: S1, S2, test sealed, embedder = nano, all eligible embedded,
  near-duplicates marked, K-means K = 3..20 on train.
- S1: 338,325 prompts; eligible labeled 206,729, eligible train 209,109. `results/split_manifest.json`.
- S2: train 208,163 / val 400 (pilot 100) / test 300 / unused 129,462. Balanced by RAG (D-070).
  Val vs test differences < 0.1; test vs pool RAG 0.136 (accepted, cause not proven).
- Vectors: `runs/s4/full/nano/` (105 parts) and Qdrant Docker (209,162 points, `docker compose up -d`).
  Run the longest messages with `--device cpu`: the GPU ran out of memory.
- Pages for the owner: `runs/cluster_view/index.html`, `k_03.html`..`k_20.html` (git-ignored).
  Numbers: `results/wp08_full_data/clusters_by_k.json`.
- Router K candidates now 3..20 (DEV-10, D-072). `k_max` is in config; pass it to `candidate_ks` in WP-14.
- Model: default (Opus 5.5)

## Exact next step
1. Owner reviews `runs/cluster_view/` and answers Q-027 and Q-028 below.
2. Then `/start`, `work/WP-04-*.md` step 2 (mock mode; Metis steps 3, 9, 10 wait for the key).

## Waiting on the owner
- Q-027: near-duplicate removal took 29% of train (61,242 of 208,163). Keep 0.95, or raise it?
- Q-028: val is uneven across clusters at K ≥ 9 (K = 16+ has clusters with 0 val). Keep K up to 20?
- D-071 defaults to confirm: 11 long messages cut at 32,768 tokens; hidden memory block left in place.
- Val 400, 600 or 800: decide at Gate 1 after real prices.
- Before WP-04 Metis steps: Q-017 (Metis AI reachable?) + key in `.env`
- Before WP-06 step 4: review the judge prompt with the agent; DEV-5
- Before WP-11: DEV-4
- Replace the Hugging Face token: it was pasted in chat and is still valid
- Q-023 option 1 ($0) after WP-05; option 2 paid, after the full data
- WP-14 compares input options on val: A, T = 2, chatbot as router input, hybrid (D-069)

## Blockers / open issues
- Metis AI unreachable from the planner's network (PLAN R17)
- Docker Hub registry refused access this session; Qdrant v1.19.1 was already on the machine
- Train is older and about 19% RAG; val and test are recent and about 86% RAG. Likely cause of the
  uneven val counts; not yet proven
- A WP-07 bug in the S1 rules would mean a free rerun of S1, S2, S4 (accepted, D-068); sample
  outputs moved to `runs/sample/`, so point WP-07 there
- GitHub secret scanning not available on the free private repo (Q-022); local pre-commit only
- HF "xet" downloads stall on this network; use `scripts/fetch_model.py`
- graphify graph has dangling edges (doc→code name mismatches); usable

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-072 K candidates 3..20 (DEV-10)
- D-071 Embedder nano; long-message and hidden-block defaults
- D-070 Image rule, balance by RAG, repeats per bot
- D-069 Embedding input stays the current user message; options compared in WP-14
- D-068 New work order
- D-067 Agent may read small redacted user prompt samples (train, val)
- D-066 Qdrant as a Docker server

## Next WPs that can start
- WP-04 in mock mode now; WP-06 after WP-04; Q-023 option 1 ($0)
