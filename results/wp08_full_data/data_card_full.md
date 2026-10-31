# Data card: full dataset (structure only)

Measured. Counts, lengths and shares only; no message text.

## Tables

| file | rows | columns |
|---|---|---|
| chat_bot.parquet | 1,830 | 27 |
| chat_message-00000-of-00013.parquet | 55,823 | 14 |
| chat_message-00001-of-00013.parquet | 55,823 | 14 |
| chat_message-00002-of-00013.parquet | 55,823 | 14 |
| chat_message-00003-of-00013.parquet | 55,823 | 14 |
| chat_message-00004-of-00013.parquet | 55,823 | 14 |
| chat_message-00005-of-00013.parquet | 55,823 | 14 |
| chat_message-00006-of-00013.parquet | 55,823 | 14 |
| chat_message-00007-of-00013.parquet | 55,823 | 14 |
| chat_message-00008-of-00013.parquet | 55,823 | 14 |
| chat_message-00009-of-00013.parquet | 55,823 | 14 |
| chat_message-00010-of-00013.parquet | 55,823 | 14 |
| chat_message-00011-of-00013.parquet | 55,823 | 14 |
| chat_message-00012-of-00013.parquet | 40,764 | 14 |
| chat_session.parquet | 80,179 | 7 |
| derived/chat_message_actions.parquet | 3,635 | 3 |
| derived/chat_message_billing.parquet | 350,529 | 30 |
| derived/chat_message_input.parquet | 70,375 | 2 |
| derived/chat_message_rag.parquet | 192,245 | 2 |
| derived/chat_message_rag_chunks-00000-of-00010.parquet | 108,261 | 11 |
| derived/chat_message_rag_chunks-00001-of-00010.parquet | 108,261 | 11 |
| derived/chat_message_rag_chunks-00002-of-00010.parquet | 108,261 | 11 |
| derived/chat_message_rag_chunks-00003-of-00010.parquet | 108,261 | 11 |
| derived/chat_message_rag_chunks-00004-of-00010.parquet | 108,261 | 11 |
| derived/chat_message_rag_chunks-00005-of-00010.parquet | 108,261 | 11 |
| derived/chat_message_rag_chunks-00006-of-00010.parquet | 108,261 | 11 |
| derived/chat_message_rag_chunks-00007-of-00010.parquet | 108,261 | 11 |
| derived/chat_message_rag_chunks-00008-of-00010.parquet | 108,261 | 11 |
| derived/chat_message_rag_chunks-00009-of-00010.parquet | 19,682 | 11 |
| derived/chat_message_tool_calls.parquet | 439 | 37 |
| users.parquet | 448 | 4 |

## Message types (length in characters)

| type | rows | p50 | p99 | max | empty |
|---|---|---|---|---|---|
| USER | 355,965 | 27 | 1,001 | 956,185 | 0 |
| AI | 349,079 | 225 | 3,136 | 510,561 | 488 |
| SYSTEM | 5,453 | 125 | 640 | 696 | 0 |
| TOOL | 143 | 5,318 | 5,345 | 5,345 | 0 |

## Messages per month

| month | messages | sessions |
|---|---|---|
| 2026-03 | 101,908 | 12,888 |
| 2026-04 | 218,022 | 24,250 |
| 2026-05 | 126,921 | 13,378 |
| 2026-06 | 53,466 | 6,384 |
| 2026-07 | 54,894 | 6,804 |
| 2026-08 | 48,452 | 6,567 |
| 2026-09 | 75,841 | 9,272 |
| 2026-10 | 31,134 | 3,949 |
| no timestamp | 2 | 2 |

## Finish reasons

| reason | rows |
|---|---|
| STOP | 709,199 |
| LENGTH | 1,422 |
| CONTENT_FILTER | 8 |
| ASYNC_TASK_RUNNING | 7 |
| TOOL_CALL | 4 |

## User messages by the bot's current model (top 15)

| provider | model | user messages | share % | bots | users |
|---|---|---|---|---|---|
| google | gemini-2.5-flash-lite | 97,177 | 27.3 | 37 | 13 |
| workflow | default | 96,669 | 27.2 | 38 | 12 |
| openai_chat_completion | gpt-4o-mini | 67,849 | 19.1 | 78 | 21 |
| google | gemini-2.5-flash | 46,081 | 12.9 | 89 | 11 |
| deepseek | deepseek-v4-flash | 27,561 | 7.7 | 153 | 8 |
| openai_chat_completion | gpt-5.4-nano | 3,070 | 0.9 | 2 | 2 |
| openai_chat_completion | gpt-4.1-mini | 2,925 | 0.8 | 6 | 6 |
| grok | grok-4-1-fast | 2,524 | 0.7 | 106 | 5 |
| openai_chat_completion | gpt-5.1 | 2,000 | 0.6 | 3 | 3 |
| openai_chat_completion | gpt-5.2 | 1,898 | 0.5 | 8 | 7 |
| google | gemini-2.0-flash | 1,654 | 0.5 | 7 | 5 |
| openai_chat_completion | gpt-5-mini | 979 | 0.3 | 6 | 6 |
| openai_chat_completion | gpt-4.1-nano | 580 | 0.2 | 3 | 3 |
| imagination | Flux-Schnell | 556 | 0.2 | 2 | 2 |
| openai_chat_completion | gpt-5.4-mini | 430 | 0.1 | 10 | 10 |

## Integrity

| orphan messages | orphan sessions | dup ids | empty sessions |
|---|---|---|---|
| 0 | 0 | 0 | 0 |

## Billing (currency not stated)

| rows | total cost | input tokens | output tokens |
|---|---|---|---|
| 350,529 | 506.7 | 1,127,643,614 | 72,555,413 |

## Secret scan (`metis.data.redact`, may include false positives)

| column | rows hit | api_key | bearer | credential | google | long_token | opaque_value | openai | password | url_param | left after redaction |
|---|---|---|---|---|---|---|---|---|---|---|---|
| chat_bot.description | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| chat_bot.functions | 3 | 2 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| chat_bot.instructions | 3 | 0 | 0 | 0 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| chat_message.content | 389 | 95 | 2 | 8 | 0 | 45 | 138 | 2 | 257 | 1 | 0 |
| chat_message.rag | 1,124 | 1 | 20 | 0 | 0 | 0 | 474 | 0 | 1,666 | 0 | 0 |
| chat_message.tool_calls | 24 | 0 | 0 | 0 | 0 | 24 | 0 | 0 | 0 | 0 | 0 |
