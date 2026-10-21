# WP-02 report: prompts (S1), hard rules, splits (S2) (2026-10-21)

## Built
- `src/metis/data/normalize.py` (ي→ی, ك→ک, ة→ه, digits → ASCII, NFKC, tatweel, diacritics,
  ZWNJ, spaces; `match_key` = normalized + case-folded), `lang.py` (fa / en / mixed / other by
  letter-script ratios; redaction markers ignored), `rules.py` (widget click, vision, workflow,
  image model, token estimate, context fit; plain-value API for the gateway), `prompts.py` (S1
  table, exclusion flags, exact duplicates), `split.py` (S2), `src/metis/config.py` (config id = hash).
- `configs/models.yaml` (4 candidates + judge; list prices dated 2026-10-20, context windows and
  vision `verified: false` until WP-04), `configs/pipeline.yaml` (S1/S2 settings, sample sizes).
- Scripts: `s1_ingest.py`, `s2_split.py`, `s1_s2_counts.py`. Tests: 90 pass in total.

## Decisions taken with the owner this session
D-045 (embed current message only), D-046 / DEV-9 (judge also current message only), D-047 (embed
the whole message, no cut), D-048 (Jina v5-text-small + Qdrant local). Light normalization kept.

## Sample results (`results/s1_s2_sample_counts.md`)
| item | n |
|---|---|
| prompt rows (user message + bot reply) | 434 (31 user messages had no reply right after) |
| LLM replies (not workflow / no-model / image) | 375 (expected ~377) |
| eligible val/test | 343 |
| eligible train | 371 |

Exclusion waterfall: workflow 32, no model 27, image 3, junk 2, exact duplicate 27 (adds up to 91).
- **Huge system prompts (> 20k chars): 29 rows, all workflow turns (model `default`); 0 of 375 LLM
  replies.** PLAN M7 expected ~8% of turns; on the sample the rule removes nothing extra.
- Widget clicks: 19 user messages follow a choice widget; 14 match a choice exactly (normalization
  adds none); 5 are free text; all 14 clicks go to workflow replies.
- Language (eligible val/test): fa 321, en 15, mixed 7.
- `est_tokens_in` (chars/3), eligible: mean 1,675, p50 1,656, p90 2,755, max 7,841 (PLAN §7
  assumed T_in = 1,640: consistent). Without huge prompts: same (none among LLM replies).
- Dry-run split (val 60 / test 40 / pilot 20): 99 sessions, recent pool = all (capacity 205 < 300);
  no shortfall; 81 eligible prompts unused because of the 3-per-session cap (long sessions). Cal
  7/7/6 per model. Same seed → identical hashes. Test ids only in `runs/s2/test_ids.sealed`.

## Notes for later WPs
- WP-08: check the huge-prompt share among **LLM** replies on the full data (likely low); the cap
  of 3 per session wastes many eligible prompts when sessions are long; check pool capacity ≥ 3×700.
- The `opaque_value` redaction rule also matches sha256 hashes after ":" in our own reports
  (harmless false positive).
- Exact duplicates are per category (used as the chatbot id; no bot id field in the data).
- PII (phones, emails) is not masked in `embed_input` (local only; owner asked for the exact
  message). Secrets are redacted everywhere.

## Acceptance checks
- [x] Tests green; no session in two splits (asserted).
- [x] Exclusion counts add up; ~377 → 375 LLM replies; huge-prompt share reported.
- [x] Widget detector: 14 of 19 matched exactly, 5 free text.
- [x] Split manifest has hashes; rerun with the same seed identical.
