# WP-04: LLM client, call cache, budget guard, Metis AI check

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-04-llm-client-cache-budget.md;
> follow the session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~180k | put the Metis AI key in `.env`; OK for one free model-list call | $0 | WP-00 | WP-06, WP-09, WP-15 |

## Context
Every paid call in the project goes through this layer. It must make money mistakes impossible:
every call is cached and never repeated (spec golden rule 2), a hard cap stops spending, every stage
needs an approved amount, long runs resume from checkpoints, and nothing unredacted leaves the
machine. Access is through **Metis AI** (owner's choice), assumed OpenAI-compatible; verify it.

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §0.3 (golden rules), §4 S6 (cache key, failures), §9.
- `PLAN.md` §1.2 E2, E11, E12, E13; §7.1 formulas.

## Steps
1. Propose; ⏸ wait for OK.
2. Deps: `litellm`, `httpx`, `tenacity` (if LiteLLM retries are not enough), `python-dotenv`,
   `mlflow` (D-044).
3. `.env` (git-ignored): `METIS_API_KEY=…`, `METIS_BASE_URL=…`. ⏸ **STOP:** ask the owner to create
   it (never print it; read it only via `os.environ`).
4. `src/metis/llm/client.py`: `complete(model_id, messages, gen_params) -> Response` via LiteLLM
   with `api_base=METIS_BASE_URL`; maps our `model_id` → provider name from `configs/models.yaml`;
   returns text, `tokens_in`, `tokens_out`, cached-token count if reported, `finish_reason`,
   `latency_ms`, returned model version, raw usage. Timeouts and retries per PLAN E4.
   **Outgoing guard:** before sending, run `redact` on every message; if anything is still detected,
   refuse the call (raise) and log the prompt id only.
5. `src/metis/llm/callcache.py`: SQLite at `cache/llm_calls.sqlite`; key = sha256 of canonical JSON
   (`model_id`, provider model name, messages, gen params, `config_id`); stores response + usage +
   cost + timestamp; `get_or_call()`; failed calls stored with status and retried only by explicit
   flag.
6. `src/metis/llm/budget.py`: `configs/budget.yaml` (`hard_cap_usd: 60`, per-stage
   `approved_usd: {pilot: 0, gen_main: 0, judge_main: 0, cache_labels: 0, live: 0}`, all 0 until the
   owner approves); `estimate(stage, plan) -> usd` from token estimates × prices; `guard(stage,
   estimate)` refuses if `spent_total + estimate > hard_cap` or `stage_spent + estimate >
   approved_usd`; ledger table in the same SQLite; `ledger_report()` → markdown for MASTER_LOG.
   Cost per call = real usage × price from `models.yaml` (Metis AI prices once known).
7. `src/metis/llm/runner.py`: `run_batch(stage, items, fn, concurrency=4, checkpoint_every=25)`:
   async, resumable (skips cached items), stops after **5% failures** or if the running cost per
   call exceeds **2×** the estimate, prints progress (counts and $ only, never content).
8. **Mock mode:** `METIS_MOCK=1` → deterministic fake responses (length drawn from a seeded
   distribution matching ~174 output tokens) and fake usage, so WP-06/07/15 can run for $0.
8b. **MLflow tracing (D-044)** `src/metis/obs/tracking.py`: local only, tracking URI
   `sqlite:///mlflow/mlflow.db`, artifacts in `mlflow/artifacts/` (git-ignored `/mlflow/`); UI via
   `uv run mlflow ui --host 127.0.0.1` (never `0.0.0.0`, never a remote/cloud server). Switch off
   MLflow usage telemetry (check the current env var name in the installed version's docs and set it
   in `tracking.py` before import). `mlflow.litellm.autolog()` (or manual spans) in `client.py` **after**
   the redaction guard, so traces contain only redacted text. Each `run_batch` = one MLflow run
   (params: stage, config ids, seed; metrics: calls, cache hits, failures, cost). `METIS_TRACING=0`
   turns it off. The agent never opens the UI or reads trace content; checks are counts only (e.g.
   key-pattern scan of the MLflow db = 0 hits).
9. **Reachability first:** `curl -sS -m 15 -o /dev/null -w '%{http_code}' https://api.metisai.ir` from the
   session's shell. On 2026-10-20 the planner got a TLS reset from metisai.ir (probably a network/VPN
   split, PLAN R17). If unreachable: ask the owner whether to (a) run paid scripts from a terminal
   outside the VPN (scripts must then work without Claude, reading/writing only the cache and
   ledger), or (b) use a fallback route for the same models. Log the decision.
   **Metis AI capability check** (`scripts/metis_check.py`): ⏸ **STOP:** ask the owner before the
   first real request (a model-list/metadata request; no generation). Record in
   `results/metis_capabilities.md`: base URL format, available ids for the 4 candidates + the judge
   (GPT-5.x class), whether `usage` is returned, prices and currency (from Metis AI's docs/pricing
   page, ask the owner if behind login), rate limits, whether provider prompt caching is reported
   (cached tokens). If any candidate or the judge is missing, ⏸ **STOP** and ask the owner
   (alternative model or a second provider such as OpenRouter for that model).
10. Update `configs/models.yaml` with provider model names, context windows, prices + `price_date`
    and `price_source`.
11. Tests (incl. a mock run with a planted fake key → MLflow store has 0 key hits): cache hit/miss, key stability, guard refusals (cap and stage), resume after a simulated
    crash at item 37, outgoing guard blocks a fake key, mock mode end-to-end.

## Outputs
- `src/metis/llm/{client,callcache,budget,runner}.py`, `configs/{budget,models}.yaml`,
  `scripts/metis_check.py`, `results/metis_capabilities.md`, tests.

## Acceptance checks
- [ ] Tests green; a second run of a mock batch makes 0 new calls.
- [ ] With all stage approvals at 0, any real call is refused.
- [ ] `results/metis_capabilities.md` lists the 5 model ids and prices (or the gaps, escalated).

## If blocked
- Metis AI not OpenAI-compatible → write a thin adapter in `client.py`; keep the same interface.
- Owner unavailable for the key → finish everything in mock mode; leave step 9 for the next session.

## End of session
- `work/reports/WP-04-report.md`. Log the judge model id and prices as decisions. If prices differ
  from PLAN §7 by > 25%, recompute §7 and tell the owner. If prompt-cache info is not reported, mark
  E9 "estimate only" in WP-16.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-04 step n", stop.
