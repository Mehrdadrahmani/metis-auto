# Metis-Auto v2: system design (v2)

**Status:** design agreed 2026-10-19. No code written yet. **Waiting for the full dataset.**
**Router specification:** [`UNIROUTE_PIPELINE.md`](../UNIROUTE_PIPELINE.md) is the source of truth for
the router (offline build S1–S12, online rule, maintenance). This document places that router inside
the gateway the course brief asks for, and records project-level decisions.
**How UniRoute works (one diagram):** [`uniroute-explained.md`](uniroute-explained.md), `diagrams/05-uniroute.drawio`.
**Primary research:** UniRoute (Jitkrittum et al., ICLR 2026), `papers/UniRoute-ICLR-2026.pdf`.
**Previous design (v1, 2026-10-17):** `../metis-v2/archive/v1-2026-10-17/`.

Labels used below: **[paper]** from UniRoute, **[spec]** from `UNIROUTE_PIPELINE.md`,
**[brief]** required by the course brief, **[ours]** our addition.

---

## 1. Goals

From the course brief (`docs/course-brief.pdf`):

| # | Goal | How we measure it |
|---|---|---|
| G1 | Pick the cheapest model that is good enough, per message | Deferral area, QNC, cost saved vs always-best at equal quality [spec §7] |
| G2 | Do not lose quality | Pass rate or win rate vs anchor (judge, human-checked) [spec]; semantic similarity to production's answer [brief] |
| G3 | Fast | p50 / p90 latency vs always-best and production |
| G4 | Reliable | Failover and escalation; 0 errors under a forced outage |
| G5 | Reuse answers when safe | Semantic-cache hit rate at a measured false-hit rate |
| G6 | Explainable and observable | A trace for every decision; dashboard |
| G7 | Generalize across usage types | Results per category and per cluster, on a locked test set |

**Success criteria**

- UniRoute's deferral area ≥ ZeroRouter's and K-NN's on the test set [spec §10].
- At least 40% cheaper than always-best at no more than 2 points lower quality.
- p90 latency no worse than always-best.
- Every number labeled measured or simulated, with confidence intervals.

---

## 2. What changed from v1, and why

| Topic | v1 (2026-10-17) | v2 (now) | Why |
|---|---|---|---|
| Data | 377 sample turns, all labeled | **Full dataset**: large unlabeled train split, labeled val (400–800) and test (200–500) | The paper clusters a large *unlabeled* set and labels only a small validation set. With 377 turns we clustered and labeled the same data, which overfits. |
| Which data is labeled | Everything | **Only val and test**; train is unlabeled [spec rule 6] | Report cards come only from validation labels [spec rule 7] |
| Choosing K, λ | Cross-validation on the same folds we report | **Split-validation on val; test locked** [spec rule 1, S9] | v1 tuned and reported on the same data |
| Labels | Judge vs production's answer + 0–4 rubric | **Pointwise** (1–10, pass ≥ τ) **or pairwise vs a frozen anchor model** (Bradley–Terry per cluster); a **pilot** decides [spec §P] | Production answers come from 18 different models, so they are not a stable reference |
| Report-card value | Plain average | Fail rate with smoothing α = 2 (α = 0 is the paper's eq. 12), or P(lose to anchor) [spec S8] | Stabilizes small clusters |
| Cost in the router | Per message, cache-aware, + escalation cost | **One number per model, normalized to [0, 1]** [spec S3] | Faithful to the paper; the cache-aware cost becomes an optional experiment |
| K | 1…5 | {3 … ⌊N_val / 50⌋} plus K = 1 as baseline [spec S5] | Paper App. G.2 |
| New-model test | Not done | **Experiment mode:** hold out ~1/3 of models as "unseen" [spec S3.4, S11] | Tests UniRoute's actual claim |
| Phase 1 | ~$1 gpt-4o-mini check on sample data | **Label-method pilot** on the full data [spec §P] | Decides pointwise vs pairwise with evidence |

---

## 3. Architecture

Diagram: `diagrams/01-overview.drawio`.

- **Offline build** (spec S1–S12) produces a versioned **router artifact**: embedder id, centroids,
  cluster names, fingerprint table Ψ (K × models), normalized costs, λ.
- **Online gateway** wraps the spec's routing rule (spec §5) with the parts the brief requires:
  rules, semantic cache, failover, escalation, traces.
- **Maintenance** (spec §6): add or remove a model, price change, recluster, drift check.

---

## 4. Offline build

Diagram: `diagrams/02-offline-build.drawio`. Full procedure: spec §4. Project-specific choices:

### Data and splits (spec S1–S2)

- **Routable unit:** last user message + up to 2 previous turns, truncated [spec]. Excluded: `default`
  workflow turns, `dalle` image turns, turns with no model, empty and junk messages.
- **Redact secrets first:** the workflow configs in the dataset contain live API keys. Nothing leaves
  the machine before redaction. **[ours]**
- **Split by conversation (or user / time)**, never by turn:
  S_tr (unlabeled, ideally ≥ 5,000), S_val (400), S_te (300), S_cal (100 items from S_val).
- **Pilot sets are subsets of the full sets:** pilot val (200) ⊂ S_val, pilot test (150) ⊂ S_te, so
  every pilot call is reused by the full build. **[ours]**
- **Stratify** val and test by the dataset's four usage categories. **[ours]**

### Models (spec S3)

| Role | Model |
|---|---|
| Candidates (5) | gemini-2.5-flash-lite, deepseek-v4-flash, gpt-4o-mini, gemini-2.5-flash, claude-sonnet-4-6 |
| Anchor (pairwise only) | claude-sonnet-4-6, the strongest candidate; its answers are frozen |
| Pilot models (4) | anchor + gemini-2.5-flash-lite, gpt-4o-mini, gemini-2.5-flash |
| Judge | A strong Persian-capable model outside the pool (e.g. a gpt-5.x-class model), temperature 0, blind |

Experiment mode with 5 models leaves only ~2 held-out models; **6–8 candidates** would make that test
meaningful (open question, §9).

### Embedding and clustering (spec S4–S5)

- One frozen **multilingual embedder run locally** (BGE-M3 or multilingual-E5 class). Chosen before
  the full data arrives by a $0 check on the sample data: are the clusters nameable, are Persian
  paraphrases close.
- K-means (k-means++, ≥ 10 restarts, fixed seed) on S_tr for each K; every cluster must hold ≥ 50
  validation prompts.

### Generation (spec S6)

- One `gen_config` per model run: same temperature and max output tokens for every model.
- **Each turn keeps its own chatbot's full system prompt, retrieved context and history**, exactly as
  production had it. The data contains 68 different chatbots, so one global system prompt would not
  reflect real traffic. **[ours]**
- Every call is cached by (`prompt_id`, `model_id`, `gen_config_id`) and never repeated.
- Failed responses count as the worst label.

### Judging (spec S7) and the pilot (spec §P)

- The pilot runs **both** methods on the same answers and picks one by: (A) cross-evaluation,
  (B) agreement with humans, (C) fingerprint stability, (D) separability. Ties → pointwise (cheaper).
- **Human calibration:** 100 items, labeled blind by Persian speakers: `human_pass` and `human_pref`.
  Gate: judge–human agreement ≥ 75%, otherwise revise the rubric. τ (pointwise) is chosen here.
- Judge prompts: spec Appendix A1 (pairwise) and A2 (pointwise).

### Fingerprints, K and λ (spec S8–S10)

- S8: fail rate with α = 2, or Bradley–Terry vs anchor.
- S9: K by split-validation on S_val (5 random halvings), ties → smaller K.
- S10: λ on S_val; **quality mode** (largest λ meeting a target quality) or **budget mode**.

### Evaluation (spec S11), on the locked test set only

| Method | Source |
|---|---|
| Always-best (the brief's "premium-model baseline") | [spec] [brief] |
| Always-cheapest | [spec] |
| ZeroRouter | [paper App. D] |
| K-NN | [paper eq. 4] |
| **UniRoute (K-means)** | [paper] [spec] |
| Production (cost and similarity only) | [brief] **[ours]** |

**Metrics:** deferral area, QNC, cost saved at quality parity with always-best, per-cluster quality,
routing share per model [spec]; semantic similarity to production's answer, cost per 1,000 queries,
latency [brief]. **Experiment mode:** K and λ tuned with `dev` models only, then routing among
`holdout` models only.

**Overfitting checks** (all $0): locked test set; split-validation for K; K = 1 baseline; fingerprint
stability (pilot C); separability (pilot D); val-vs-test gap (spec §12).

---

## 5. Online gateway (every message)

Diagram: `diagrams/03-online-path.drawio`.

| Stage | What it does | Source |
|---|---|---|
| G1 Hard rules | Menu clicks and widgets → workflow step, no model. Image request → image model. Remove from the available set A: models without vision for attachments, models whose context window is too small, providers with an open circuit breaker | [brief] [ours] |
| G2 Preprocess + embed | Same preprocessing as S1; local embedder; one vector reused by G3 and G4 | [spec §5] |
| G3 Semantic cache | Namespaced per chatbot, language and retrieved-context hash. Never cached: follow-ups, time-sensitive, personal or sensitive content, attachments. Threshold set for ≤ 2% false hits | [brief] [ours] |
| G4 Router | Nearest centroid k; score s(h) = Ψ_k(h) + λ·ĉ(h) for every h in A; pick the lowest; ties → cheaper | [spec §5] |
| G5 Call + failover | Call the chosen model. On error or timeout → next-lowest s(h) (prefer another provider). Circuit breaker: 3 failures → 30 s pause → one probe | [spec §5] [brief] |
| G6 Checks + escalation | Free code checks: empty, truncated, wrong language, invalid JSON. Fail → one repair → escalate to the model with the next-lower Ψ_k | [brief] (cascade) [ours] |
| G7 Trace | prompt id, cluster, chosen model, all scores, artifact version, cost, latency, cache hit, checks | [spec §5] [brief] |

**Switching providers mid-conversation:** every message is routed separately; we measure how often the
provider changes and whether it hurts (lost prompt-cache discount, style changes). **[ours]**

**Later upgrades (not in the first build):** safety-net judge on uncertain or sensitive cases;
cache-aware per-message cost; LearnedMap (spec §11); attribute-based clusters (paper App. G.4);
2–3 answers per (prompt, model); a second judge; shared cache and breaker state (Redis).

---

## 6. Maintenance

As in spec §6: add a model (only its row is computed, then λ), remove a model, price change, change τ,
recluster, refresh validation set, weekly drift check (compare live cluster shares with S_val).

---

## 7. Data stored

As in spec §3: `prompts`, `models`, `gen_config`, `responses`, `point_judgments`, `pair_judgments`,
`human_labels`, `labels`, `embeddings`, `clusterings`, `fingerprints`, `router_artifact`.
All generated data is git-ignored. Plus `traces` for the online gateway.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Full dataset late, or smaller than the spec needs (S_tr < 5,000; val + test < 700) | Smaller val/test with fewer clusters (K ≤ N_val/50); say so in the report |
| Judge unreliable in Persian | Human calibration gate ≥ 75%; pilot criterion B |
| Labels can't tell models apart (everyone passes) | Pilot criterion D; raise τ or use pairwise (spec §12) |
| UniRoute no better than ZeroRouter / K-NN | Reported honestly; troubleshooting in spec §12; keep the winner in the gateway |
| Only 5 models makes experiment mode weak | Add 1–3 candidates (decision needed) |
| Estimated prices and token counts | Recompute the budget from the full data before any paid call |
| Credentials in the dataset | Redact before any API call; never commit data or generated answers |
| Model drift | Pin versions; record the returned version; drift check |

---

## 9. Open questions

1. When does the full dataset arrive, and how large is it?
2. API access: OpenRouter, direct keys, AvalAI, or Google Cloud?
3. Budget approval: ~$17–50 estimated, $60 planned (proposal §8).
4. Who does the human calibration (100 items in the pilot)?
5. Keep 5 candidates, or add 1–3 so experiment mode has enough held-out models?
6. What is the `default` model in the data (ask the course team)?
7. Deadline and deliverable format?
