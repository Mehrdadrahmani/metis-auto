# WP-02: Prompt builder (S1), hard-rule detectors, splitter (S2)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-02-prompts-rules-splits.md;
> follow the session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~200k | – | $0 | WP-01 | WP-03, WP-07, WP-08, WP-15 |

## Context
Turns raw sessions into **routable prompts** (what the router sees) plus the **generation context**
(what a model needs to answer like production), and splits them by session. Decisions already made:
clustering uses user text only (PLAN M5); generation uses the chatbot's own system prompt, RAG
context and history (M6); turns with system prompt > 20,000 chars are excluded from labeled sets (M7);
categories only balance splits and reports (never routing).

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §3 (artifact `prompts`), §4 S1 and S2, §8 (defaults).
- `PLAN.md` §1.1 M5–M7, §1.2 E6. `work/reports/WP-01-report.md`.

## Steps
1. Propose; ⏸ wait for OK.
2. `src/metis/data/normalize.py`: Persian normalization for matching/embedding: `ي→ی`, `ك→ک`,
   `ة→ه` (only for matching), Arabic/Persian digits → ASCII, collapse repeated ZWNJ/whitespace,
   strip tatweel and diacritics. Keep the original text for generation. Tests with examples.
3. `src/metis/data/lang.py`: `lang_tag(text) ∈ {fa, en, mixed, other}` by letter-script ratios
   (fa ≥ 0.7 of letters → fa; Latin ≥ 0.7 → en; both ≥ 0.2 → mixed). Tests.
4. `src/metis/data/prompts.py` → table `prompts` (parquet in `runs/s1/`), one row per user message
   followed by a bot reply:
   - `prompt_id` = hash(session_id, message index); `session_id`, `category`, `timestamp`;
   - `text` = redacted original user text; `text_norm`; `embed_input` = the **current user message
     only** (normalized, redacted; no previous turns: D-045 / DEV-8, owner decision, as in the
     paper), truncated to **512 tokens** keeping the start (approximate tokens with the embedder
     tokenizer later; chars/3 for now); `context_turns` = up to **T = 2** previous turns
     (role-tagged, redacted) **for the judge templates only** (spec A1/A2 `{context_turns}`), never
     embedded;
   - generation context: `system_prompt_id` (hash of redacted instructions), `history` (all previous
     turns, keep the last 10 turns and ≤ 6,000 tokens), `rag_context` (from the reply's `rag.context`);
   - production reply: `prod_model`, `prod_provider`, `prod_answer` (redacted; for the similarity
     metric only), `prod_latency_s` (reply timestamp − user timestamp; may be noisy);
   - flags: `lang`, `has_image`, `is_widget_click`, `reply_is_workflow` (provider workflow / model
     default), `reply_is_image` (dalle), `reply_no_model`, `instr_chars`, `huge_prompt`
     (instr_chars > 20,000), `est_tokens_in`;
   - descriptive fields for reporting only (never used for routing): `uses_rag`, `demands_json`,
     `instr_len_bucket` ∈ {≤1k, 1–5k, 5–20k, >20k}.
   - `eligible_labeled` = LLM reply AND not widget click AND not image AND not huge AND text length ≥ 2
     AND not junk (only punctuation/emoji). Count every exclusion reason separately.
5. `src/metis/data/rules.py` (shared with the gateway, WP-15): `is_widget_click(prev_bot_msg,
   user_text)` (normalized equality with any `input.items[].choices`), `needs_vision(msg)`,
   `is_workflow_turn(...)`, `estimate_tokens(text)`, `fits_context(model, tokens)` (context windows
   from `configs/models.yaml`; create the file with the 4 candidates + judge, prices from PLAN §7 and
   a `price_date`). Tests.
6. Dedup helpers: exact duplicates (same `text_norm` within the same chatbot); near-duplicate
   function (cosine > 0.95) to be applied after embeddings in WP-08.
7. `src/metis/data/split.py` (S2): split **by session**. Sessions sorted by `created_at`; the
   **recent pool** = latest sessions holding ~3× the needed labeled prompts; from it draw val (400)
   and test (300) by sampling sessions **stratified by category**, with at most **3 eligible prompts
   per session** in val/test (sampled randomly); everything else → train (unlabeled). Then
   `pilot_val` = 100 prompts ⊂ val (stratified), `cal` = 100 items = each pilot prompt paired with one
   non-anchor model, round-robin over {deepseek-v4-flash, gpt-4o-mini, gemini-2.5-flash}. Seed
   **20261020**. Write `runs/s2/split.parquet` + `results/split_manifest.json` (counts per split ×
   category × language, sha256 of the sorted id lists). Sizes are parameters (`configs/pipeline.yaml`).
8. Run on the sample with scaled sizes (val 60, test 40, pilot 20) as a dry run; write the counts
   (no text) to `results/s1_s2_sample_counts.md`.

## Outputs
- `src/metis/data/{normalize,lang,prompts,rules,split}.py`, `configs/{models,pipeline}.yaml`, tests,
  `results/s1_s2_sample_counts.md`.

## Acceptance checks
- [ ] Tests green; no session appears in two splits (test asserts it).
- [ ] Exclusion counts on the sample add up; expected: ~377 usable LLM replies before other
      exclusions; huge-prompt exclusions reported as a share.
- [ ] Widget-click detector finds the user messages that follow the 29 widget bot messages (report
      how many matched exactly).
- [ ] Split manifest has hashes; rerun with the same seed gives identical ids.

## If blocked
- If widget clicks don't match choices exactly (e.g. extra spaces), use normalized matching and
  report the residue; don't guess beyond that.

## End of session
- `work/reports/WP-02-report.md`: exclusion table, language distribution, token estimates (mean,
  p50, p90 of `est_tokens_in`, with and without huge prompts), anything that changes the budget.
- If eligible share is much lower than expected, note it for WP-08 (PLAN §6 row "data size").

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-02 step n", stop.
