# WP-04 report: LLM client, call cache, budget

Date 2026-11-01. Cost $0.00 (model-list and price requests only, no generation).

## Built
`src/metis/llm/{client,callcache,budget,runner}.py`, `src/metis/obs/tracking.py`,
`configs/budget.yaml`, `scripts/metis_check.py`, `results/metis_capabilities.md`, `tests/test_llm.py` (39 tests).

## Acceptance
- Tests green (208); a second mock batch makes 0 new calls.
- All stage approvals are 0, and any real call is refused. A real call also needs a budget Permit.
- `results/metis_capabilities.md` lists the model ids and prices for 4 candidates and Jev.

## Differences from the WP
- pyarrow pinned to 25: MLflow 3.17 needs below 26.
- `complete()` refuses key patterns; callers redact first with `redact_messages`.
- Metis has one address per provider, so each model has an `api_path`.
- Runner also stops on truncation and reasoning tokens (AGENTS.md §5).
- MLflow uses manual spans. Mock answers have their own file and keys.

## Metis findings
- Reachable from this network (Q-017 closed). Margin about 10% over list prices. Prices in USD.
- DeepSeek costs double in peak hours. Generation for 700 calls per model is about $5.92 at planned sizes.

## Not proven
Chat through each address, usage and cached-token reporting, rate limits. E9 stays "estimate only"
in WP-16 until the first paid call shows otherwise. These are checked in WP-09.
