# WP-03 report: Embedder + Qdrant

Sessions: 2026-10-22 (part 1), 2026-10-24 (part 2). Cost $0. Tests: 100 pass.

## Built
- `src/metis/embed/embedder.py`: `Embedder` (L2-norm float32, `task`, `prompt_name`, token-budget
  batching, `embedder_id`, **`merge_adapter`**), `src/metis/embed/store.py` (Qdrant local, payload
  ids/numbers only, exact search).
- `scripts/fetch_model.py` (resumable model download), `scripts/s4_embed_bench.py`,
  `scripts/data/persian_pairs.yaml` (40 synthetic pairs).
- `configs/pipeline.yaml` `s4:` (both candidates, choice pending).

## Decision table (details: `results/embedder_benchmark.md`)

| Check | Guide | small | nano |
|---|---|---|---|
| p95 at 512 tok, MPS, adapter merged | ≤ 60 ms | 221 ms ✗ | 59 ms ✓ |
| p95 at 30 tok (typical p50 = 24 tok) | – | 44 ms | 15 ms |
| Persian AUC, clustering adapter | ≥ 0.85 | 0.61 ✗ | 0.66 ✗ |
| Persian AUC, text-matching adapter | ≥ 0.85 | 0.76 | 0.85 |
| Determinism (same input, CPU and MPS) | identical | ✓ | ✓ |
| Messages over the token limit | 0 | 0 | 0 |
| Qdrant exact == numpy (scores) | 20/20 | ✓ | ✓ |
| Clusters "make sense" (owner, sample) | yes | partly | partly |

## Outcome
- **Not frozen:** owner keeps small and nano; choice in WP-08 on real train data (D-052, WP-08 step 6).
- Semantic cache will use the `text-matching` adapter (`s4.cache_task`); routing uses `clustering`.
- Acceptance "chosen model meets 60 ms": nano does; if small is chosen in WP-08, update the gateway
  latency budget (PLAN E5, WP-15).
- New idea Q-023: test the router on public Persian benchmark data (`ref/docs/persian-datasets.md`).
