# TakRouter (project Metis-Auto v2)

An OpenAI-compatible LLM gateway for Persian-first chatbots. For each message it picks a model with the **UniRoute** method (ICLR 2026), then adds a semantic cache, quality checks with escalation, failover and traces. Rahnema College 2026 course project.

**New here?** Read [The result](#the-result), run [Quick start](#quick-start), then open the site at `http://localhost:8000`. Live project status: [`STATUS.md`](STATUS.md). Full results: [`report/REPORT.md`](report/REPORT.md).

## The result

Final test: 299 sealed prompts, opened once after the router and protocol were frozen with tag `pre-test`. Each answer was scored 1 to 10 by the Jev judge; 7 or above is a pass. Costs are measured from tokens at list prices.

| Setup | Pass | $ per 1,000 messages |
|---|---:|---:|
| **TakRouter K = 8 (shipped)** | **66.9%** | **0.69** |
| TakRouter K = 4 (comparison) | 70.2% | 5.55 |
| Always DeepSeek v4 Flash | 68.6% | 0.68 |
| Always Sonnet 5.5 (premium) | 64.9% | 16.32 |
| Always Luna | 61.9% | 0.84 |
| Always Gemini 2.5 Flash Lite | 51.8% | 0.41 |

- **Against Sonnet, all 3 pre-registered criteria were met:** 95.8% cheaper; quality difference +2.0 points (95% CI -3.0 to +7.1, limit -5); simulated p90 latency 4.4 s vs 8.8 s.
- **Against always-DeepSeek, the shipped router adds no value:** -1.7 points (95% CI -3.8 to +0.3) at about the same cost. Most of the saving comes from one good cheap model. This is the most important limit of the result.
- Judge labels are noisy (5% of 60 repeats flipped pass or fail) and pilot agreement missed its line (0.74 vs 0.75, Opus labels, not human).
- **Semantic cache:** no threshold met the 2% wrong-hit target. At 0.97 about 10% of meaning hits were judged wrong (95% CI 5.5% to 17.4%). See `results/cache_threshold.md`.

**Check on true answers (Khayyam, n = 1,100):** UniRoute beat ZeroRouter on area by 0.020 (95% CI 0.001 to 0.044), but at the chosen λ scored 55.0% vs 56.2% for the best single model. See `results/khayyam/README.md`.

## How it works

```text
request → G1 rules → G2 embed → G3 cache → G4 UniRoute → G5 call + failover → G6 checks + escalation → G7 trace
```

**Offline:** cluster train prompts with no labels (K-means on Jina nano vectors), generate answers on validation, judge them, and build Ψ, the fail rate of each model in each cluster.
**Online:** assign the message to its nearest cluster k and pick the model with the lowest `s(h) = Ψ_k(h) + λ·ĉ(h)`. Adding a model only adds one row to Ψ.

The router artifact is `artifacts/router_v1/` (K = 8, λ = 0.5151). Secrets are redacted before any model call, and traces hold no message text.

| Measured | Value |
|---|---:|
| Gateway overhead, real embedder | p50 23 ms, p95 72 ms |
| One model down | 0 failed requests in tests and replay |
| Real latency, 50 messages | TakRouter p90 10.6 s, Sonnet 18.1 s |

## Quick start

Needs [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
uv sync
uv run pytest                                  # no keys or data needed
TAKROUTER_FAKE_EMBED=1 uv run uvicorn metis.gateway.app:app --port 8000
```

Open `http://localhost:8000` for the site. That command needs no keys or model files: the provider is a mock, answers are placeholders, and a fake embedder replaces Jina, so **routing in this mode is not real**. For real routing, download the embedder (`scripts/fetch_model.py`) and drop `TAKROUTER_FAKE_EMBED`. For real answers, set `provider: live` in `configs/gateway.yaml` and put `METIS_BASE_URL` and `METIS_API_KEY` in `.env`, with an approved `live` budget.

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="local")
reply = client.chat.completions.create(model="takrouter", messages=[{"role": "user", "content": "سلام"}])
print(reply.model, reply.takrouter)
```

Use `model="takrouter"` to route, or a concrete id such as `deepseek-v4-flash` to skip the router. Optional headers: `X-Metis-Chatbot`, `X-Metis-Session`.

| Task | Command |
|---|---|
| Replay on validation ($0, needs `runs/`) | `PYTHONPATH=scripts uv run python scripts/s18_replay.py` |
| Refresh site numbers | `PYTHONPATH=scripts uv run python scripts/build_web_data.py` |
| Latency benchmark | `uv run python scripts/gateway_latency.py` |

## Pitch deck

Persian slides: see `deck/README.md`.

## Repository map

| Path | What it holds |
|---|---|
| `src/metis/` | Package: `data`, `embed`, `llm`, `judge`, `router`, `gateway`, `eval`, `sim`, `labeling`, `obs` |
| `scripts/` | One script per stage: `s1_` ingest to `s7_` judge, plus reports |
| `web/` | The TakRouter site, served by the gateway at `/` |
| `artifacts/` | Frozen routers: `router_v1` (shipped), `router_v1_k4` |
| `configs/` | YAML settings. `budget.yaml` holds the money limits, `models.yaml` the prices |
| `tests/` | pytest suite |
| `results/`, `report/` | Aggregates only, no prompt or answer text |
| `work/` | One instruction file per work package, reports in `work/reports/` |
| `ref/` | Spec, papers, course brief, diagrams |
| `AGENTS.md` | Project rules, for agents and people |
| `STATUS.md` | Where we are and the exact next step |
| `MASTER_LOG.md` | Decisions (D-numbers), budget ledger, dated log |
| `graphify-out/` | Knowledge graph of the code |

## What is not in this repo

These are git-ignored and stay local:

| Folder | Holds | Why |
|---|---|---|
| `data/` | Raw chatbot data | Contains live API keys and user text |
| `runs/` | Prompts, splits, answers, labels, sealed test ids | Same text, and test ids must stay sealed |
| `cache/` | Paid call cache and spending ledger | Holds answer text |
| `qdrant/`, `models/`, `mlflow/` | Vector store, model weights, traces | Large or derived |

Sharing the embeddings: use the Qdrant snapshot from the owner, not `runs/`. Never pass on `runs/s1`,
`runs/cluster_view`, `runs/bots` or the sealed ids.

## Rules for everyone

The full list is in [`AGENTS.md`](AGENTS.md). The ones that matter most:

- **Never commit** `data/`, `runs/`, `cache/` or `.env`, or paste a key in chat.
- **The test set stays sealed.** No method, K, λ, threshold or other choice may use test prompts or
  labels. Only `scripts/eval_test.py` opens them. That one look is done, so results must not lead to new tuning on the same test set.
- **Paid calls need the owner's "go"** with an estimate. All go through `metis.llm.runner`, which adds
  the cache, the budget limit and automatic stops. The hard cap is $60.
- **Prompts and answers stay out of** git, `results/` and `report/`.
- **Every reported number** says measured or simulated, n, and a confidence interval.
- **Secrets:** everything sent to an API passes `metis.data.redact` and the outgoing key guard.

## For AI agents

Read in this order, and stop when you have enough:

1. [`AGENTS.md`](AGENTS.md): rules and session protocol. These override your defaults.
2. [`STATUS.md`](STATUS.md): current state and the exact next step.
3. [`ROADMAP.md`](ROADMAP.md) table, then the current `work/WP-xx-*.md`.

Machine-readable facts:

- **Run:** `uv run pytest -q` · `uv run ruff check src scripts tests`
- **Add packages:** `uv add`, never `pip install`.
- **Code search:** run `graphify query "<question>"` before grepping, and `graphify update .` after
  code changes.
- **Claude Code:** `CLAUDE.md`, `.claude/settings.json` and the `/start` and `/handoff` skills load
  automatically. Other agents should follow `AGENTS.md` §1 by hand.

Hard stops. Ask a human first:

- Any paid call, or raising a limit in `configs/budget.yaml`.
- Anything that opens `*.sealed*` files, or any test metric.
- Changing `configs/judge_config.yaml` or the judge templates, which changes the judge config id.
- Deviating from `ref/UNIROUTE_PIPELINE.md`.

If you touch a stage script, keep it resumable: a rerun must pay only for missing work, and a stopped
run must never write the final table that later stages read.
