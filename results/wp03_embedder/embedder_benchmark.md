# Embedder benchmark (WP-03 step 5)

Measured 2026-10-24 on the owner's Mac (Apple Silicon, **on battery, Low Power Mode off**), torch
2.14.1, 8 threads. Raw numbers: `results/embedder_benchmark_{small,nano}.json` (`scripts/s4_embed_bench.py`);
merge/fp16 and per-adapter checks from one-off scratch profiling (same synthetic inputs).
Inputs: synthetic Persian text (from `scripts/data/persian_pairs.yaml`, not from the data); sample =
371 eligible prompts (`embed_input`, D-045/D-047). Latency = one message per call, 200 calls after 10
warm-up calls (merge/fp16 rows: 40 calls). Budget (PLAN E5): **≤ 60 ms p95 at 512 tokens**.

## 1. Latency, p50 / p95 in ms (one message)

| Model, device, setup | 30 tok | 200 tok | 512 tok | longest sample (2,562 tok) |
|---|---|---|---|---|
| small, CPU | 179 / 208 | 341 / 386 | 600 / 681 | 3,083 / 3,335 |
| small, MPS (as loaded) | 94 / 102 | 167 / 174 | 304 / 311 | 1,543 / 1,547 |
| small, MPS, **adapter merged** | 43 / 44 | 102 / 103 | 220 / 221 | – |
| small, MPS, merged + fp16 | 36 / 37 | 98 / 99 | 207 / 215 | – |
| nano, CPU | 54 / 59 | 99 / 111 | 168 / 175 | 442 / 451 |
| nano, MPS (as loaded) | 35 / 36 | 52 / 55 | 92 / 95 | 218 / 218 |
| nano, MPS, **adapter merged** | 15 / 15 | 29 / 29 | **58 / 59** | – |
| nano, MPS, merged + fp16 | 11 / 12 | 27 / 27 | 53 / 54 | – |

- **Why "merged" is faster:** the Jina model keeps 4 LoRA adapters live and calls `set_adapter` on every
  encode, so each layer does the extra LoRA matmuls. Merging the `clustering` adapter into the base
  weights once (`peft merge_and_unload`) gives the **same vectors** (max |diff| ≤ 4.6e-7) at
  1.6–2.5× the speed. fp16 adds little (cos ≥ 0.999998 vs fp32), so fp32 stays.
- small cannot reach 60 ms at 512 tokens on this Mac even merged (~220 ms; it is near the GPU's
  compute limit for 677M parameters). Merged small at a typical message (p90 = 100 tokens) ≈ 70 ms.
- nano merged meets the budget (59 ms p95 at 512 tokens, battery).
- Throughput (as loaded, sample, token-budget batches): small 9.5/s CPU, 16.5/s MPS; nano 59/s CPU,
  99/s MPS. Batch 64 × 200 tok: small 5.6/s CPU, 11.7/s MPS; nano 26.9/s CPU, 48.8/s MPS.
- Load time: small 7 s CPU / 6 s MPS; nano 5 s / 2 s. RAM after load: small ≈ 1.1 GB (+2.7 GB MPS
  allocation); peak during the run 2.3 GB (token-budget batching, `max_batch_tokens` 8,192).

## 2. Determinism and devices

- Same input → identical vector on CPU and on MPS (max |diff| = 0.0), both models.
- Batched vs single: max |diff| ≤ 2.8e-7. CPU vs MPS: max |diff| ≤ 3.5e-7, min cos 0.9999999.
- Sample token lengths (model tokens): mean 72, p50 24, p90 100, max 2,562; 11 of 371 over 512;
  **0 over the 32K limit** (no truncation, D-047).

## 3. Persian sanity (40 synthetic pairs: 20 paraphrase, 20 topically close but different)

AUC = how well cosine separates paraphrases from close-topic pairs (guide ≥ 0.85). n = 20 + 20, so the
AUC is rough (± ~0.15).

| Adapter (prompt "Document: ") | small AUC | small gap | nano AUC | nano gap |
|---|---|---|---|---|
| **clustering** (planned, D-048) | 0.61 | 0.014 | 0.66 | 0.025 |
| classification | 0.70 | 0.045 | 0.74 | 0.048 |
| retrieval | 0.76 | 0.164 | 0.80 | 0.179 |
| text-matching | 0.76 | 0.112 | **0.85** | 0.118 |

(The "Query: " prompt was no better: 0.59–0.81.)

- The `clustering` adapter puts same-topic messages almost on top of each other (mean cos 0.81 vs
  0.83), whatever their exact meaning. That is what topic clustering wants, but it fails this check.
- For the **semantic cache** (WP-17), paraphrase-vs-close separation is what matters: there
  `text-matching` is clearly better.
- No setup passes 0.85 with margin; nano text-matching reaches it (0.848). Reference model bge-m3
  not tested yet.

## 4. Cluster readability on the sample (K-means, seed 20261020, `clustering` adapter)

Categories coded c1–c4 (sorted names); cos silhouette is low for both (short chat messages).

| Model | K | silhouette | sizes |
|---|---|---|---|
| small | 4 | 0.119 | 55 / 149 / 101 / 66 |
| small | 6 | 0.104 | 55 / 140 / 55 / 10 / 28 / 83 |
| nano | 4 | 0.151 | 84 / 162 / 20 / 105 |
| nano | 6 | 0.081 | 73 / 69 / 70 / 54 / 75 / 30 |

What the numbers suggest (no text read): clusters split mostly by **length and language**: e.g. small
K = 4 has a very short cluster (mean 11 chars, 101 prompts), a long one (600 chars, 17 of 66 English)
and a c4-heavy one (83 of 149). Whether they "make sense" needs the owner's look at
`runs/s4/cluster_samples_{small,nano}.html`.

## 5. Qdrant vs numpy

Exact search returns the same top-10 **scores** as numpy brute force (20/20 queries, both models, max
diff 0.0). The first check compared ids in order and showed 17/20 and 19/20: all mismatches were exact
score ties (duplicate messages) swapping places. The check now compares scores.
