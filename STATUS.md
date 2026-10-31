# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-31 · by session WP-05b

## Now
- Current WP: **WP-05 Router core + evaluation library** (code done; one check open, Q-025)
- All steps 2–10 built and tested: 161 pass, 1 expected failure (K* = 3). Report:
  `work/reports/WP-05-report.md`; numbers: `results/wp05_router/synthetic_validation.md`.
- UniRoute beats ZeroRouter on planted data (+0.0845 [+0.0520, +0.1178]); no false gain without
  structure (-0.0057 [-0.0253, +0.0217]). Simulated, n_test = 300.
- K rule review: `results/wp05_router/k_rule_review.md`. Keep highest score (recommended); one-spread
  rule withdrawn; fixed K = 8 is the paper's other option.
- Full data is in `data/raw/metis/data/` (git-ignored). Loader `src/metis/data/load_parquet.py`;
  selection rules in `report/data_selection.md`.
- Candidates (D-056) not confirmed on Metis AI; prices from third parties. `PLAN §7` partly recomputed.
- `workflow` excluded (D-057). LLM judge only, pointwise vs pairwise in the pilot (D-059).
- Only 700 prompts reach paid models (2,800 generation + about 3,500–4,800 judge calls).
- **Exact next step:** owner answers Q-025. Highest score: replace the xfail in
  `tests/test_router_synthetic.py` with a routing-quality check, tick WP-05. Fixed K: also log DEV-10
  and change S9. Then WP-04.
  Order: WP-04 → 06 → 07 → 08.
- Model: default (Opus 5.5)

## Waiting on the owner
- Q-025: rule for choosing K (blocks ticking WP-05)
- Q-026: confirm split-validation and R = 20 (D-061; "go on" was taken as approval)
- Before WP-04: Q-017 (Metis AI reachable on your network?) + key in `.env`
- Before WP-06 step 4: review the judge prompt with the agent; DEV-5
- Before WP-11: DEV-4
- Replace the Hugging Face token: it was pasted in chat and is still valid
- Q-023 option 1 ($0) after WP-05; option 2 paid, after the full data
- Q-006 (`workflow / default`) no longer blocks; only useful for the report
- WP-08 decisions: balancing field (no category in the data); image rule; optional val 800 at Gate 1

## Blockers / open issues
- Metis AI unreachable from the planner's network (PLAN R17)
- GitHub secret scanning not available on the free private repo (Q-022); local pre-commit only
- HF "xet" downloads stall on this network; use `scripts/fetch_model.py` (plain HTTP, resumes)
- graphify graph has dangling edges (doc→code name mismatches); usable
- FarsEval-PKBETS, PEKA still gated (not requested)

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-063 `area()` bug fix; QNC shown exact and within 1 point
- D-062 WP-05a spec readings: K = 1 cannot win, sessions kept whole in halvings
- D-061 K by split-validation (Q-020), R = 20 (DEV-6)
- D-060 Intervals resample whole sessions
- D-059 LLM judge only; judge prompt reviewed by the owner before WP-06 step 4
- D-058 Parquet loader on DuckDB; fallback plan P4 retired

## Next WPs that can start
- WP-04 after Q-017; WP-06 after WP-04
