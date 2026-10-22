# Report notes (running; aggregates only, no message text)

Every session adds what the final report (WP-20) should mention. WP-20 builds the report from this
file, the WP reports and `MASTER_LOG.md §2`.

## WP-00 Bootstrap
- Reproducible setup: uv env `metis-rahnema` (CPython 3.12.15), pinned `uv.lock`, private GitHub repo.
- Secret protection: local pre-commit scan (GitHub push protection unavailable on a free private
  repo, Q-022) → limitation to state.
- Continuity mechanism (STATUS, hooks, /start, /handoff) so work survives session limits (D-041).

## WP-01 Data access + redaction
- Sample: 4 categories × 25 sessions, 907 messages (465 user / 442 bot), 18 models, 7 providers;
  14 messages with images, 29 with choice widgets, 71 with RAG; 408 system prompts (78 distinct),
  33 over 20k chars (9 distinct) → excluded from labeled sets (M7).
- **Secrets in the data:** 44 redaction hits in 29 messages / 10 sessions: system prompts 27, image
  URLs 13 (signed URL parameters), user/bot text 4. After redaction: 0 (two independent scans).
  Shows why every outgoing text is redacted (D-042, D-043).
- Privacy by design: the agent never reads content; only counts, hashes and masked shapes (E13).

## WP-02 Prompts, rules, splits
- Sample: 434 prompt rows → 375 with a real LLM reply → 343 usable for val/test, 371 for train.
- Exclusions (waterfall): workflow 32, no model 27, image 3, junk 2, exact duplicates 27.
- System prompts > 20k chars occur only in workflow turns (29 rows); 0 of 375 LLM replies → the
  M7 exclusion costs nothing on the sample.
- Widget clicks: 14 of 19 messages after a choice widget are exact clicks, all handled by
  workflow steps (supports the hard-rule design of the gateway).
- Mostly Persian: fa 321 / en 15 / mixed 7 among usable prompts.
- Input size ≈ 1,675 tokens per message (chars/3), matching the budget assumption (1,640).
- Split by session, stratified by category, ≤ 3 prompts per session, recent pool; reproducible
  (hashes); test ids sealed in a separate file.

## WP-03 Embedder + Qdrant (part 1)
- Jina v5-text-small (Qwen3-0.6B base, 1024-dim, 32K tokens) runs locally; clustering LoRA adapter +
  "Document: " prompt as the model card. Nano (EuroBERT-210M) likely lacks Persian.
- Qdrant local mode does brute-force search: exact K-NN == numpy (tested).
- Practical issues: HF download stalls (switched to resumable curl); batch of long messages needs
  > 11 GB RAM → token-budget batching; Low Power Mode on battery makes latency numbers invalid
  (measure plugged in).

## Decisions to explain in the method chapter
- D-044 local MLflow for tracing and run comparison (vs Phoenix, Langfuse, Opik, cloud tools).
- D-045 / DEV-8 embedding input = current user message only (paper) instead of + 2 turns (spec);
  generation sees the full history (M6).
- D-049 clustering input = "Document: " + message (model-card default).
- D-048 Jina v5-text-small (local, clustering adapter) + Qdrant local; license CC BY-NC 4.0
  (non-commercial: fine for the course, a limitation for production use); Persian coverage checked in WP-03.
- D-047 the whole user message is embedded (no truncation); only light Persian normalization.
- D-046 / DEV-9 judge also sees only the current message (spec had 2 previous turns) → limitation:
  short follow-ups are harder to judge; check in the pilot (WP-11) whether follow-ups disagree more.
