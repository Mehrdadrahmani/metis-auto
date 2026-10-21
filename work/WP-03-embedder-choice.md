# WP-03: Set up and check the embedder (S4) + vector store

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-03-embedder-choice.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~150k | approve the choice; ~10 min to look at cluster samples | $0 | WP-02 | WP-05 (real runs), WP-08, WP-15 |

## Context
One frozen multilingual embedder is used offline (clustering, K-NN) and online (router, cache). It
must handle Persian, be fast on the owner's Apple Silicon Mac (16 GB+), and give readable clusters.
Latency budget: embedding ≤ 60 ms p95 for one message of ≤ 512 tokens (PLAN E5). The whole message
is embedded, never cut by us (D-047): prefer an embedder whose max input covers the longest user
messages (sample max ≈ 13.8k chars ≈ 4.6k tokens); report how many messages exceed the limit and
the latency of long inputs.

**Owner decision D-048:** embedder = **jinaai/jina-embeddings-v5-text-small** (Feb 2026; 677M,
32K tokens, 1024-dim, LoRA adapter **`clustering`** used for routing; local, CC BY-NC 4.0 = fine for
the course, state in the report); fallback **jina-embeddings-v5-text-nano** (239M) only if small
misses the latency budget. Vector store = **Qdrant in local mode** (`qdrant-client`, path `qdrant/`,
git-ignored; no Docker). This WP no longer picks among several models: it sets them up and checks
them; if Jina fails the Persian check, ⏸ ask the owner (reference: bge-m3).

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §4 S4. `PLAN.md` §1.2 E5. `work/reports/WP-02-report.md` (token stats).

## Steps
1. Propose; ⏸ wait for OK (includes downloading ~1–2 GB of model weights; say so).
2. Add deps: `sentence-transformers`, `torch` (MPS), `numpy`, `scikit-learn`, `pyarrow`.
3. `src/metis/embed/embedder.py`: `Embedder(name, device, max_tokens, prefix)` with `encode(list[str])
   -> np.ndarray` (L2-normalized float32), batch size param, records `embedder_id` = name + revision
   hash + preprocessing config hash.
4. Models: **jina-embeddings-v5-text-small** (task adapter `clustering`; check the model card for
   the exact loading code, `trust_remote_code` and task/prompt names) and **v5-text-nano** (latency
   fallback). Pin revisions. Confirm Persian is covered (model card / tokenizer) and record it.
4b. `src/metis/embed/store.py`: Qdrant local (`QdrantClient(path="qdrant/")`), one collection per
   `embedder_id` (cosine, 1024-dim); point id = `prompt_id` hash; **payload = ids and numbers only**
   (split, category, lang, cluster), never text. Helpers: `upsert`, `search(vec, k, filter)`,
   `exact=True` option (K-NN baseline must equal brute force). Tests vs numpy brute force.
5. Benchmarks, written to `results/embedder_benchmark.md`:
   - **Latency:** single-message p50/p95 over 200 calls (inputs of 30, 200, 512 tokens; synthetic Persian
     text), on CPU and on MPS; throughput (prompts/s) for batch 64; RAM use; load time.
   - **Persian sanity:** write **40 synthetic pairs** yourself (20 paraphrase pairs, 20 unrelated but
     topically close pairs) in Persian, typical of chatbot traffic (greetings, order status, coding
     question, complaint, product question). Not from the data. Report the mean cosine of each group,
     the gap, and the AUC.
   - **Cluster readability on the sample** (eligible prompts, `embed_input`): K-means K = 4 and 6,
     seed 20261020. Claude sees **only numbers**: cluster sizes, category mix, language mix, mean
     length, silhouette. Write `runs/s4/cluster_samples_<model>.html` (local file, git-ignored) with
     8 random redacted prompts per cluster for the owner.
     ⏸ **STOP:** ask the owner to open the files (~10 min) and say for each model whether the clusters
     "make sense" (yes / partly / no). Claude never reads the prompt texts.
6. Confirm: small meets the latency budget on the owner's Mac (else nano), Persian AUC acceptable
   (≥ 0.85 as a guide), clusters "make sense". Write the results.
   ⏸ **STOP:** owner approves.
7. Freeze the choice in `configs/pipeline.yaml` (`embedder.name`, revision, device, `max_tokens`,
   prefix, batch size).

## Outputs
- `src/metis/embed/embedder.py`, tests (normalization, determinism, prefix handling),
  `results/embedder_benchmark.md`, `configs/pipeline.yaml` updated.

## Acceptance checks
- [ ] Same input → identical vector (determinism on the chosen device; if MPS isn't deterministic
      enough, use CPU offline and note it).
- [ ] Chosen model meets ≤ 60 ms p95 at 512 tokens on the owner's Mac, or the best available is chosen
      and the gateway latency budget is updated (PLAN §6).

## If blocked
- Download blocked or too slow → use the e5-base model only, log it.
- None meets the latency budget → choose the fastest with acceptable AUC and ⏸ ask the owner
  before any truncation (D-047); log the trade-off.

## End of session
- `work/reports/WP-03-report.md` (decision table). Log decision D-xxx "embedder = …".
- Update `work/WP-15-gateway-core.md` latency numbers if they differ from the budget.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-03 step n", stop.
