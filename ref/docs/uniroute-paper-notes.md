# UniRoute paper notes: how we apply it (v2)

**Paper:** Jitkrittum et al., *Universal Model Routing for Efficient LLM Inference*, ICLR 2026
(`papers/UniRoute-ICLR-2026.pdf`). Primary research.
**Router spec:** [`UNIROUTE_PIPELINE.md`](../UNIROUTE_PIPELINE.md). **Updated:** 2026-10-19.
v1 notes: `../metis-v2/archive/v1-2026-10-17/docs/uniroute-paper-notes.md`.

## What the paper does

- **Problem:** routing when **new, unseen models** appear at test time ("dynamic pool").
- **Prompt representation:** frozen embedder (Gecko 1B, 768 dims) → K-means on a **large training
  set**, no labels needed (§5.1).
- **Model representation ("fingerprint"):** each model's error rate in each cluster, measured on a
  **small labeled validation set** (eq. 12). A new model only needs to answer the validation set.
- **Routing rule:** lowest `error + λ·cost` (eq. 8), a plug-in estimate of the optimal rule
  (Proposition 1).
- **No LLM is trained.** The K-means version has no supervised training at all. LearnedMap trains a
  small MLP (2 × 128, 5 epochs, CPU, minutes).

## Experimental facts

| Item | Paper |
|---|---|
| Models | EmbedLLM 112 (~37 unseen at test), SPROUT 15, Headlines 12, RouterBench 11, Math+Code 4; Chatbot Arena 26 |
| Models routed among at test | ~37 on EmbedLLM; 4–6 on the other four datasets |
| Data | e.g. Headlines 10K (4,000 / 400 / 5,600); OpenLLMv2 20,046 (13,232 / 800 / 6,014); EmbedLLM 60 / 10 / 30 |
| Validation size | 400 typical; 100–500 tested |
| Repeats | 400 random splits; sign test at α = 0.01 |
| Labels | 0/1 correctness from benchmarks; Bradley–Terry on Chatbot Arena pairwise votes (App. G.4) |
| Cost | Parameter count (EmbedLLM) or API USD per prompt; one fixed number per model |
| K | 3 … N_val / 50, chosen by area under the deferral curve (App. G.2) |
| Fixed pool | "Comparable to most baselines"; MLP often slightly better (App. G.5) |
| Answers | Pre-computed in public datasets; the authors did not call the models |

## How our pipeline maps to the paper

| Element | Paper | Our pipeline (spec) |
|---|---|---|
| Train split | Large; labels only from *training* models | Large, **unlabeled**; K-means only |
| Validation split | ~400, labels for test models | 400–800, judge labels for every candidate |
| Test split | Held out | 200–500, **locked** until the final report |
| Labels | Ground-truth 0/1 | Judge: pointwise (pass ≥ τ) or pairwise vs anchor (BT); pilot decides |
| Fingerprint | Eq. 12, plain average | Eq. 12 with smoothing α = 2 (α = 0 = paper), or BT P(lose to anchor) |
| Choosing K | Training-model labels on S_tr | Split-validation on S_val (S_tr stays unlabeled) |
| Routing rule | Eq. 8 / 11 | Identical |
| Cost | One number per model | Identical, normalized to [0, 1] |
| λ | Sweep / line search (App. E) | Identical; quality or budget mode |
| Metrics | Deferral area, QNC | Identical; plus the brief's similarity, latency, cache hits |
| Unseen-model test | Disjoint train / test model sets | Experiment mode: ~1/3 of models held out |
| LearnedMap | Main best variant | Later (needs labels for 3–5 models on thousands of train prompts) |

## Corrections to v1

| v1 claim | Problem | v2 |
|---|---|---|
| "We cluster the training set, not the validation set" | With 377 turns, our training folds were also the labeled set, so in practice we clustered and fingerprinted the same data | Train split unlabeled; fingerprints from validation only |
| K and λ by cross-validation, reported on the same folds | Selection bias | Split-validation on val; locked test |
| Plain average, no smoothing | Small clusters give noisy values | α = 2 smoothing, reported next to α = 0 |
| Per-message cache-aware cost | Not the paper's rule | One cost per model; cache-aware cost is a later experiment |
| Labels vs production's answer | Production used 18 different models, so the reference is unstable | Pointwise or anchor-based pairwise, chosen by a pilot |
| Unseen-model test "pointless" with a fixed pool | It is the paper's main claim and can be simulated | Experiment mode |

## Differences that remain on purpose

- **Judge labels, not ground truth.** Open-ended Persian chat has no single correct answer. The human
  calibration gate (≥ 75%) is mandatory.
- **Each turn keeps its own chatbot's system prompt** (68 chatbots in the sample).
- **The router sits inside a gateway** (rules, cache, failover, escalation) because the brief requires it.

## Ideas for later

- **Attribute-based clusters** (App. G.4): helped under prompt distribution shift.
- **Coreset validation set** (§7): a diverse validation set may represent models better than a random one.
- **Budget control** (App. E): cheap line search for λ.
