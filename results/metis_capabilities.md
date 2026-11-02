# Metis AI capabilities

Checked 2026-11-02 with model-list requests (no generation).
Base URL: `https://api.metisai.ir`. Model ids listed: 213. HTTP by route: {'openai': 200, 'deepseek': 200, 'anthropic': 200, 'google': 200}.

| Wanted | Matching ids |
|---|---|
| deepseek-v4-flash | deepseek-v4-1-flash-1017, deepseek-v4-flash, deepseek-v4.1-flash |
| gpt-5.6-luna | gpt-5.6-luna |
| gemini-2.5-flash-lite | gemini-2.5-flash-lite |
| claude-sonnet-5-5 | claude-sonnet-4-5, claude-sonnet-5, claude-sonnet-5-5 |
| judge (GPT-5.x) | gpt-5, gpt-5-2025-08-07, gpt-5-chat-latest, gpt-5-codex, gpt-5-mini, gpt-5-mini-2025-08-07, gpt-5-nano, gpt-5-nano-2025-08-07, gpt-5-pro, gpt-5-pro-2025-10-06, gpt-5-search-api, gpt-5-search-api-2025-10-14, gpt-5.1, gpt-5.1-2025-11-13, gpt-5.1-chat-latest, gpt-5.1-codex, gpt-5.1-codex-max, gpt-5.1-codex-mini, gpt-5.2, gpt-5.2-2025-12-11, gpt-5.2-chat-latest, gpt-5.2-codex, gpt-5.2-pro, gpt-5.2-pro-2025-12-11, gpt-5.3-chat-latest, gpt-5.3-codex, gpt-5.4, gpt-5.4-2026-03-05, gpt-5.4-mini, gpt-5.4-mini-2026-03-17, gpt-5.4-nano, gpt-5.4-nano-2026-03-17, gpt-5.4-pro, gpt-5.4-pro-2026-03-05, gpt-5.5, gpt-5.5-2026-04-23, gpt-5.5-pro, gpt-5.5-pro-2026-04-23, gpt-5.6-luna, gpt-5.6-sol, gpt-5.6-terra |

## Prices (USD per 1M tokens, Metis AI)

| Model | Input | Output | Cached input |
|---|---:|---:|---:|
| deepseek-v4-flash | 0.165 | 0.66 | 0.0033 |
| gpt-5.6-luna | 0.22 | 1.32 | 0.022 |
| gemini-2.5-flash-lite | 0.11 | 0.44 | not listed |
| claude-sonnet-5-5 | 2.2 | 11 | 0.22 |
| jev-latest | 0.0462 | 0 | not listed |

DeepSeek costs double in peak hours (Mon-Fri 01:00-04:00, 06:00-10:00 UTC).
Not known yet: rate limits, and whether usage and cached tokens are returned for each
route (needs a first paid call).
