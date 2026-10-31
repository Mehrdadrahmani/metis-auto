# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-31 · by session full-data intake

## Now
- Current WP: **WP-05 Router core + evaluation library** (not started; propose at step 1)
- **Full data is in** `data/raw/metis/data/` (git-ignored): parquet tables, 710,640 messages, 80,179
  sessions, 2026-03-01..10-11. Private HF repo `poriniki/metis`; the owner's account has no access, the
  pasted token worked and is not stored anywhere in the project. Owner: data is theirs, no licence conflict.
- Done: `src/metis/data/load_parquet.py` (`iter_sessions`, streaming; 12 s, peak 3.4 GB; `load_with_report`
  accepts the folder), `scripts/data_card_full.py`, `results/wp08_full_data/` (WP-08 steps 1–2).
  Secret scan: 1,544 rows hit, 0 left after redaction.
- Candidates changed (D-056): deepseek-v4-flash, gpt-5.6-luna, gemini-3.5-flash-lite, claude-sonnet-5-5
  (anchor). Not confirmed on Metis AI; prices from third parties. `PLAN §7` only partly recomputed.
- `workflow` excluded everywhere (D-057). Selection rules and limits: `report/data_selection.md`.
- Judging: LLM judge only, pointwise vs pairwise in the pilot (D-059). Judge prompt review pending.
- Only 700 prompts reach paid models (2,800 generation + about 3,500–4,800 judge calls).
- **Exact next step:** `/start`, then `work/WP-05-router-core-eval.md` step 1. Order: WP-05 → 04 → 06 → 07 → 08.
- Model: default (Opus 5.5)

## Waiting on the owner
- Before WP-05: Q-020 K-selection data (recommended: split-validation, $0) and DEV-6 (R = 20)
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
- D-060 Intervals resample whole sessions
- D-059 LLM judge only; judge prompt reviewed by the owner before WP-06 step 4
- D-058 Parquet loader on DuckDB; fallback plan P4 retired
- D-057 `workflow` excluded from train, val and test
- D-056 Candidates updated to current models

## Next WPs that can start
- WP-05 (free, synthetic); WP-04 after Q-017; WP-06 after WP-04
