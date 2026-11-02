# PROJECT: Metis-Auto v2 in one file

For a newcomer (a person or a new Claude session). Read this once; afterwards `STATUS.md` + `/start`
is enough.

## 1. The idea

Chatbot platforms pay very different prices for different AI models: a strong model (here
claude-sonnet-5-5) costs ~20–30× a cheap one, while most messages are simple. **Metis-Auto** is a
"virtual model": a gateway that sends each message to the **cheapest model that is good enough for
this kind of message**, without losing quality. Around it: a semantic cache, a backup when a model
fails, a step up to a stronger model when an answer looks bad, and traces plus a dashboard. This is
the Rahnema College 2026 course project (`ref/docs/course-brief.pdf`). Traffic is mostly **Persian**.

## 2. The method (UniRoute, ICLR 2026)

1. **Prompt types (free):** embed a large set of **unlabeled** real user messages with a local
   multilingual model and group them with K-means into K types.
2. **Report cards (paid once):** every candidate model answers ~400 labeled **validation** prompts;
   an AI judge, checked against the owner's labels, grades each answer; a model's **fingerprint** Ψ
   = its failure rate in each prompt type.
3. **Route (online):** embed the new message → nearest type k → choose the model with the lowest
   `Ψ_k(model) + λ · cost(model)`. λ sets how much price matters.
4. **New model later:** it answers the same 400 prompts → one new row. No retraining.

Spec: `ref/UNIROUTE_PIPELINE.md` (source of truth). Plain walkthrough: `ref/docs/uniroute-explained.md`.

**What we changed on purpose** (`PLAN.md §1`): the same labels also build simpler routers, and the
best one on validation ships (UniRoute's edge is adding models, not beating simple routers on a
fixed pool); the router sees only the user's text, while the models answer with the chatbot's own
instructions; a slim pilot picks the grading method; strict statistics with a pre-registered test.

## 3. The gateway (one message)

```
message → G1 hard rules (menu click, image, context size, broken model)
        → G2 embed (same as offline) → G3 semantic cache (same chatbot, safe messages only)
        → G4 router (nearest type, lowest Ψ + λ·cost) → G5 call model (failover: next best)
        → G6 free checks (empty, cut off, wrong language, bad JSON) → repair or escalate
        → G7 trace (cluster, scores, model, cost, latency, cache, checks) → answer
```

FastAPI, OpenAI-compatible API, LiteLLM for provider calls through Metis AI.

## 4. How we know it works

- Data split **by session**: train (unlabeled, clustering only), validation 400 (all choices),
  **test 300 (locked; opened once at the end)**.
- Primary result: the shipped router vs always-sonnet: ≥ 40% cheaper, quality not worse than
  5 points (95% CI), p90 latency not worse. Secondary: UniRoute vs simpler routers, per-type results,
  similarity to production answers (the brief's metric, with a caveat), cache hit rate, latency.
- The router and the evaluation plan are frozen with a git tag (`pre-test`) before the test set opens.

## 5. The plan

| Phase | What | Cost |
|---|---|---|
| 0 | Setup: folder, git + GitHub, session mechanism | $0 |
| 1 | Build and test everything free before the data (WP-01…07) | $0 |
| 2 | Full data in: clean, split, cluster, real budget ⛔ Gate 1 | $0 |
| 3 | Slim pilot + owner labels 100 items ⛔ Gate 2 | ~$6 |
| 4 | Main build: answers, grades, fingerprints, freeze ⛔ Gate 3 | ~$17–27 |
| 5 | Gateway, cache, replay, dashboard (in parallel) | $0–1 |
| 6 | Final evaluation on the locked test set | ~$1.5 |
| 7 | Report and release | $0 |

Total ~$25–35, cap $60, ~4 weeks. Details: `PLAN.md`; work packages: `ROADMAP.md`.

## 6. How work is organized

Many short Claude Code sessions, no memory between them. Each session: open `metis-auto/` → the
status loads automatically → `/start` (proposes, waits for OK) → work on one work package →
`/handoff` (updates STATUS, log, plan, commits, pushes). Details: `CONTINUITY.md`.

## 7. File map

| File / folder | What |
|---|---|
| `STATUS.md` | Where we are (≤ 60 lines; auto-loaded) |
| `ROADMAP.md` | All work packages, ticks, dependencies, gates |
| `work/WP-xx-*.md` | Instructions per work package; `work/reports/` results per WP |
| `PLAN.md` | Design decisions, phases, results → changes, budget, statistics, risks, repo layout |
| `MASTER_LOG.md` | Decisions, open questions, budget ledger, dated log |
| `CONTINUITY.md` | The session mechanism and why |
| `AGENTS.md`, `CLAUDE.md` | Rules for agents |
| `ref/` | Inputs: spec, proposal, docs, paper, original diagrams |
| `configs/`, `src/metis/`, `scripts/`, `tests/` | Code and settings |
| `artifacts/router_v1/` | The frozen router (centroids, Ψ, costs, λ) |
| `results/` | Aggregate numbers and figures (no message text) |
| `data/`, `cache/`, `runs/` | Git-ignored: raw data, call cache, stage outputs |

## 8. What to read first

1. `STATUS.md` (where we are) → 2. `ROADMAP.md` (the route) → 3. this file →
4. `ref/proposal/proposal.md` §1, §5–§8 (what we promised and why; its plan and budget are superseded
by `PLAN.md`) → 5. `ref/docs/uniroute-explained.md` (the method with one diagram) →
6. `PLAN.md §1` (what we changed and why). Read the spec and the paper **only by section**, when a WP
asks.

## 9. Glossary

| Term | Meaning |
|---|---|
| Anchor | The strong model (claude-sonnet-5-5) whose answers are the reference in pairwise grading |
| Calibration set (cal) | 100 (prompt, model) items labeled by the owner to check the judge and choose τ |
| Cascade / escalation | Retry or move to a stronger model when an answer fails the checks |
| Circuit breaker | Temporarily stop calling a model that keeps failing |
| ĉ(h) | A model's cost per prompt divided by the most expensive model's cost (0–1) |
| Deferral curve / area | Quality vs cost as λ varies; the area under it summarizes a router |
| Fingerprint Ψ_k(h) | Model h's average loss (fail rate) in prompt type k, from validation only |
| Gate | A checkpoint where the owner must approve before continuing (budget, judge quality, freeze) |
| K | Number of prompt types (clusters) |
| κ (kappa) | Agreement corrected for chance (judge vs human) |
| λ | Price weight in the routing score |
| Ladder | Simpler routers built from the same labels (always-best/cheapest, ZeroRouter, K-NN, …) |
| Pointwise / pairwise | Judge scores one answer 1–10 / compares it with the anchor's answer |
| QNC | Cheapest cost at which routing matches the best single model's quality |
| Replay | Re-running real messages through the gateway using stored answers (no new cost) |
| Semantic cache | Reuse a saved answer for a message that means the same, in the same chatbot |
| τ (tau) | Pass threshold on the judge's 1–10 score |
| WP | Work package: one unit of work, usually one session |
