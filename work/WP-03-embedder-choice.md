# WP-03: Choose the embedder (S4)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-03-embedder-choice.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~150k | approve the choice; ~10 min to look at cluster samples | $0 | WP-02 | WP-05 (real runs), WP-08, WP-15 |

## Context
One frozen multilingual embedder is used offline (clustering, K-NN) and online (router, cache). It
must handle Persian, be fast on the owner's Apple Silicon Mac (16 GB+), and give readable clusters.
Latency budget: embedding ≤ 60 ms p95 for one message of ≤ 512 tokens (PLAN E5).

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §4 S4. `PLAN.md` §1.2 E5. `work/reports/WP-02-report.md` (token stats).

## Steps
1. Propose; ⏸ wait for OK (includes downloading ~1–2 GB of model weights; say so).
2. Add deps: `sentence-transformers`, `torch` (MPS), `numpy`, `scikit-learn`, `pyarrow`.
3. `src/metis/embed/embedder.py`: `Embedder(name, device, max_tokens, prefix)` with `encode(list[str])
   -> np.ndarray` (L2-normalized float32), batch size param, records `embedder_id` = name + revision
   hash + preprocessing config hash.
4. Candidates: **BAAI/bge-m3** (dense output only), **intfloat/multilingual-e5-base** (prefix
   `"query: "`), **intfloat/multilingual-e5-large** (prefix `"query: "`). Pin model revisions.
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
6. Decide with a simple score: must meet the latency budget on the owner's Mac; then the best Persian
   AUC; cluster readability as a tie-breaker. Write the decision and its reasons.
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
- None meets the latency budget → choose the fastest with acceptable AUC; truncate `embed_input` to
  256 tokens; log the trade-off.

## End of session
- `work/reports/WP-03-report.md` (decision table). Log decision D-xxx "embedder = …".
- Update `work/WP-15-gateway-core.md` latency numbers if they differ from the budget.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-03 step n", stop.
