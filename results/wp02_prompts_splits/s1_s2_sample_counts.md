# S1 + S2 counts on the sample (WP-02 dry run)

Aggregates only. Sizes scaled for the sample (val 60 / test 40 / pilot 20).
S1 config `49ec93224327`, seed 20261020, input sha256 e0f56a2f2340b2ac70bf273e05ee2e9b56126cd3874c0c58659f46b4983549e1.

## S1: prompt rows

| item | n |
|---|---|
| user messages | 465 |
| user messages without a bot reply right after | 31 |
| prompt rows (user message + reply) | 434 |
| rows with an LLM reply (not workflow / no model / image) | 375 |
| eligible for val/test | 343 |
| eligible for train (clustering) | 371 |

## Exclusions (labeled sets)

`flag` = rows with this reason (a row may have several); `waterfall` = rows removed by
this reason after the reasons above it.

| reason | flag | waterfall |
|---|---|---|
| reply_workflow | 32 | 32 |
| reply_image | 0 | 0 |
| reply_no_model | 27 | 27 |
| widget_click | 14 | 0 |
| has_image | 11 | 3 |
| huge_prompt | 29 | 0 |
| too_short | 0 | 0 |
| junk | 2 | 2 |
| dup_exact | 27 | 27 |

Huge system prompts (> 20k chars): 29 of 434 rows (6.7%); among LLM replies: 0 of 375 (0.0%). All huge prompts belong to workflow turns (model `default`): True.

## Widget clicks

- User messages right after a bot message with choices: 19 (the other widget messages are last in the session or followed by a bot message).
- Matched a choice exactly: 14; after normalization: 14; free text instead of a choice: 5.
- Widget clicks answered by a workflow step: 14 of 14.

## Language

| lang | all rows | eligible val/test | eligible train |
|---|---|---|---|
| fa | 398 | 321 | 341 |
| en | 24 | 15 | 21 |
| mixed | 10 | 7 | 9 |
| other | 2 | 0 | 0 |

## Size estimates (chars / 3)

| set | mean | p50 | p90 | max | n |
|---|---|---|---|---|---|
| est_tokens_in, eligible val/test | 1675 | 1656 | 2755 | 7841 | 343 |
| est_tokens_in, LLM replies incl. huge | 1652 | 1608 | 2753 | 7841 | 375 |
| est_tokens_in, LLM replies without huge | 1652 | 1608 | 2753 | 7841 | 375 |
| user text chars, eligible | 161 | 35 | 182 | 4666 | 343 |
| system prompt chars, eligible | 3170 | 3486 | 4984 | 10412 | 343 |
| production latency s, eligible | 3 | 2 | 5 | 118 | 343 |

Eligible rows using RAG: 65; system prompt mentions JSON: 20. Instruction length buckets (eligible): {'1-5k': 226, '5-20k': 31, '<=1k': 86}.

## S2: split (by session)

Sessions with prompt rows: 99; recent pool: 99 sessions, capacity 205 prompts (≤ 3 per session); val sessions 29, test sessions 16. Shortfall: none.

| split | prompts |
|---|---|
| train | 190 |
| val | 60 |
| test | 40 |
| none | 144 |

`none` = 144: in a val/test session but not drawn (cap 3 or not eligible): 97 (of which eligible: 81); in a train session but not eligible for train: 47.
Pilot 20 (⊂ val); cal per model {'deepseek-v4-flash': 7, 'gemini-2.5-flash': 6, 'gpt-4o-mini': 7}.

| split × category | n |
|---|---|
| none × developer_pegahdev | 21 |
| none × general_athena | 30 |
| none × operator_gapify | 39 |
| none × other_other | 54 |
| test × developer_pegahdev | 10 |
| test × general_athena | 11 |
| test × operator_gapify | 8 |
| test × other_other | 11 |
| train × developer_pegahdev | 42 |
| train × general_athena | 66 |
| train × operator_gapify | 22 |
| train × other_other | 60 |
| val × developer_pegahdev | 15 |
| val × general_athena | 16 |
| val × operator_gapify | 13 |
| val × other_other | 16 |

Hashes of the sorted id lists (rerun with the same seed reproduces them):

- train: a5993ee5254f1a626996a0d004e0dacafaee1a32e554eff9d30a4159d0414c74
- val: f95effa1434e4c02268e9a2307f6c67c48094f0ce041547686cd72fd5d0ce26e
- test: c9ef9639e4b330ad5c274d4707e9ca23d7ee308f96279d759c02208fff15afb1
- pilot: 6681a0c333b91e4df3348dd9e6553361bcf243a2577290b90c36edc708db8d7a
- cal: e3313de0a03d6ab32efba38b70af02794c9ac95deb666172f7ed3acbb55d6b20
