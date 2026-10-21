# WP-01 report: data access and redaction (2026-10-21)

## Built
- `src/metis/data/schema.py`: dataclasses `Category, Session, Message, Rag, InputWidget,
  Attachment`; all text fields `repr=False` (printing an object shows no content); unknown fields in
  `extra`.
- `src/metis/data/load.py`: `load_dataset(path)`, `load_with_report(path)` (counts unknown fields
  and `user_turns`/`bot_turns`/`session_len` mismatches; `strict=True` raises `SchemaError` that
  names the session id, never content).
- `src/metis/data/redact.py`: `redact(text) -> (text, n_hits)`, `redact_counts`, `redact_obj`,
  `redact_message(m) -> (copy, hits per field)`. Covers content, instructions, `rag.query`,
  `rag.context[]`, attachment URLs, widget text and `extra`. Idempotent. Kinds: D-042.
- `src/metis/data/inspect.py` + `scripts/data_card.py`: structure-only card + manifest.
- Tests: `tests/test_redact.py` (each kind, idempotence, Persian/number false positives, UUIDs,
  message fields), `tests/test_load.py` (hand-written fixture, report, strict mode, no output, card
  has no content). 48 passed.

## Data card summary (`results/data_card_sample.md`)
All expected counts match: 4 categories × 25 sessions, 907 messages (465 user / 442 bot),
18 models, 7 providers, 14 attachment messages (15 images), 29 widget messages (all SINGLE_CHOICE),
71 RAG messages (3–5 context chunks), 408 non-empty instructions (78 distinct), 33 > 20k chars
(9 distinct). 27 bot messages have no model/provider/instructions (null).

## Redaction hits per field
| field | hits | kinds |
|---|---|---|
| instructions | 27 | opaque_value 9, url_param 6, credential 5, long_token 4, jwt 3 |
| attachments (URLs) | 13 | url_param 13 |
| content | 4 | api_key 4 |
| rag.query / rag.context / input / extra | 0 | – |

29 messages in 10 sessions have hits. Re-scan after redaction: 0. Cross-check with the pre-commit
regex: 3 raw hits → 0 after. A residual scan (shapes only) of long high-entropy strings found one
unknown format (9× after `:`), now covered by `opaque_value`; only 3 hyphenated slugs remain.

## Schema surprises
- None: no unknown fields, no turn-count mismatches. `session_len` = number of messages.
- Hits in `content` and attachment URLs, not only in `instructions` → WP-06 updated (D-043).

## Acceptance checks
- [x] Tests green; every key kind redacted; re-scan 0 on the sample.
- [x] Data card matches the expected counts.
- [x] No content printed in the session (counts, masked shapes, hashes only).
