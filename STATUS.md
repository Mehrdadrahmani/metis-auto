# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-30 · by session WP-03b (close)

## Now
- Current WP: **WP-05 Router core + evaluation library** (not started; WP-03b finished 2026-10-30)
- WP-03b closed: owner judged cluster quality good (D-055). Report `work/reports/WP-03b-report.md`.
- Q-024 closed (D-054): follow the paper: K ≤ N_val/50, no per-cluster minimum, α = 0 (Eq. 12).
- Embedder still open: small and nano both stay until WP-08 (D-052); WP-03b did not separate them
  (quality about equal, nano 2.5× faster).
- Private study PDFs stay **outside the repo** (`../uniroute-math/`; never commit).
- **Exact next step:** `/start`, then WP-05 step 1 (`work/WP-05-router-core-eval.md`). Free, synthetic data.
- Model: default (Opus 5.5)

## Waiting on the owner
- **Data deadline:** PLAN P4 trigger is **2026-11-01**. If no data by then: reduced plan (N_val 300 /
  N_te 200, K ≤ 6, pilot merged). By 2026-11-08: sample-only demo. Owner decides at the trigger.
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
- D-055 WP-03b closed, cluster quality good; small vs nano stays open until WP-08
- D-054 Cluster size follows the paper: K ≤ N_val/50, no per-cluster minimum, α = 0
- D-053 WP-03b follows the paper's embedding + K-means protocol (Jina for Gecko); HF login for Khayyam
- D-052 keep jina v5 small + nano; choose in WP-08; cache uses text-matching; merge_adapter

## Next WPs that can start
- WP-05 (free, synthetic); WP-04 after Q-017; WP-06 after WP-04
