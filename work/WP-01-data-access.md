# WP-01: Data access and redaction

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-01-data-access.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~120k | – | $0 | WP-00 | WP-02, WP-06, WP-08 |

## Context
The dataset contains live API keys (found inside bot messages' `instructions`). Every later step reads
data through this module, so it must be safe by construction: load → typed objects → redaction before
anything can be printed, logged or sent. The full dataset will use the same schema (assume so; verify
in WP-08).

## Read (only these)
- `AGENTS.md §Secrets` (already in context).
- Known schema (from the planner's structure-only inspection; don't re-derive by printing):
  top level `[{category, sessions[]}]`; session: `session_id, created_at, user_turns, bot_turns,
  session_len, messages[]`; message: `role ∈ {user, bot}, content, timestamp`; bot: `model, provider,
  instructions, rag {query, context[]}, input {items[] {type=SINGLE_CHOICE, label, name, choices[],
  required, default, placeholder}}`; user: `attachments[] {contentType=IMAGE, content}`.
- `PLAN.md` §1.2 E13 (secrets).

## Steps
1. Propose; ⏸ wait for OK.
2. `src/metis/data/schema.py`: dataclasses (or pydantic) `Category, Session, Message, Rag,
   InputWidget, Attachment`; unknown fields kept in `extra: dict` and counted (the full data may add
   fields).
3. `src/metis/data/load.py`: `load_dataset(path) -> list[Session]` with category attached to each
   session; never prints content; validates counts against the session's `user_turns`/`bot_turns`.
4. `src/metis/data/redact.py`: `redact(text) -> (text, n_hits)` with the patterns of `AGENTS.md
   §Secrets` plus generic `api[_-]?key\s*[:=]\s*\S+`, `password\s*[:=]\s*\S+`, long hex/base64
   runs (≥ 32 chars) inside quotes; replace with `[REDACTED:<kind>]`. `redact_message(m)` applies it to
   `content`, `instructions`, `rag.context[]`, `rag.query`, attachment `content` (URLs).
5. `src/metis/data/inspect.py` (CLI `scripts/data_card.py`): structure-only report: key paths, types,
   counts, length percentiles, value sets for short categorical fields (model, provider, role,
   widget type, attachment type), number of redaction hits per field. **No message text.**
6. Tests (`tests/test_redact.py`, `tests/test_load.py`): synthetic messages with each key kind;
   idempotence; no false positive on normal Persian text with numbers; loader on a tiny synthetic
   fixture (write it by hand, not from the real data).
7. Run the data card on `data/raw/sample.json` → `results/wp01_data/data_card_sample.md` (aggregates only; safe
   to commit). Expected numbers to verify: 100 sessions, 907 messages (465 user / 442 bot), 18 models,
   7 providers, 14 attachment messages, 29 widget messages, 71 RAG messages, 408 non-empty
   instructions (78 distinct), 33 instructions > 20k chars.

## Outputs
- `src/metis/data/{schema,load,redact,inspect}.py`, `scripts/data_card.py`, tests,
  `results/wp01_data/data_card_sample.md`.

## Acceptance checks
- [ ] Tests green; every key kind redacted; zero hits remain after redaction on the sample
      (re-scan reports 0).
- [ ] The data card matches the expected counts above (differences explained).
- [ ] No content printed in the session transcript (only counts).

## If blocked
- Schema differs from the description → adapt the loader with `extra`, log it, continue.

## End of session
- `work/reports/WP-01-report.md`: data card summary, redaction hits per field, any schema surprise.
- If redaction hits appear in `content` or `rag.context` (not only `instructions`), note it in
  `MASTER_LOG.md` and in WP-06 (judge prompts must use redacted text too).

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-01 step n", stop.
