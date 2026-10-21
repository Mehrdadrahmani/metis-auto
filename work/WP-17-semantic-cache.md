# WP-17: Semantic cache (starts with the owner's deferred decision)

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-17-semantic-cache.md; follow the
> session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 5 | default (Opus 5.5) | ~150k | **decide the threshold method**; "go" if paid | $0 or ≤ ~$1 | WP-15 (code), WP-08 (real pairs) | WP-18 |

## Context
The brief requires a semantic cache. The owner deferred the threshold decision (2026-10-20) because
the router comes first. Safety rules are already fixed (PLAN E8): exact match after Persian
normalization + meaning match; namespace = chatbot + instruction hash + language; only standalone
messages; never images, personal data, time-sensitive or RAG-dependent answers (unless the context
hash matches); only answers that passed checks; TTL 7 days. Expect a low hit rate; report it honestly.
Pairs come from the **train** split only (never test).

## Read (only these)
- `PLAN.md` §1.2 E8; `work/reports/WP-15-report.md`, `WP-16-report.md`; `ref/docs/design.md` §5 (G3 row).

## Steps
1. ⏸ **Decision point:** present the three options in plain words and get the owner's choice:
   1. **AI-grader labels** (recommended): ~200–300 candidate pairs; the judge answers "Does this
      saved answer correctly answer the new message? yes/no"; ~$0.5–1; the owner optionally glances
      at 20 in a local HTML (15 min).
   2. **Fixed strict threshold:** cosine ≥ 0.95 + exact match; $0; wrong-hit rate assumed, not
      measured.
   3. **Exact match only:** $0, safest; weak on the brief's "semantic" requirement.
   Record the decision (D-xxx).
2. `gateway/cache.py`: Qdrant collection per namespace (D-048; local mode, payload = ids, hashes and
   numbers; the cached answer itself is stored locally next to it, never in git; lookup ≤ 5 ms p95,
   else in-memory numpy fallback) + metadata. Test whether Jina's `text-matching` adapter separates
   paraphrases better than `clustering` (costs a second embedding per request: measure latency),
   persistence to SQLite; `lookup(namespace, vec, text_norm)` → exact first, then max cosine ≥ θ;
   `store()` only if the answer passed checks and the message is cacheable.
3. `gateway/cache_policy.py`: `is_cacheable(msg, session)`: first turn or no reference words to
   history (Persian/English list: «اون», «قبلی», «همین», "it", "that", …); no image; no personal-data
   patterns (phone, national id, card numbers, emails, order/tracking ids); no time words («امروز»,
   «الان», «قیمت», "today", "price"); RAG answers only if the context hash matches. Tests.
4. Threshold, depending on the decision:
   - Option 1: build candidate pairs within each chatbot on **train** prompts with cosine in
     [0.80, 0.99], stratified across the range; for each pair, the "saved answer" = the production
     answer of the earlier message (redacted) — the judge decides if it fits the later message.
     ⏸ "go" with the estimate (stage `cache_labels`). Choose θ = the lowest threshold whose upper 95%
     Wilson bound of the wrong-hit rate is ≤ 5% and whose point estimate is ≤ 2% (with ~200 pairs a
     tighter bound is impossible; say so); if none qualifies, use 0.97 and report.
   - Option 2: θ = 0.95. Option 3: semantic lookup disabled.
5. Wire into the gateway (G3) with config `cache: {enabled, theta, ttl_days}`; trace hit/miss/reason.
6. Tests: namespace isolation (no cross-chatbot hit), non-cacheable messages never hit, TTL expiry,
   exact-match normalization (ی/ي, digits, ZWNJ).

## Outputs
- `src/metis/gateway/{cache,cache_policy}.py`, `results/cache_threshold.md` (method, θ, pair counts,
  wrong-hit estimate with CI; no text), tests.

## Acceptance checks
- [ ] Policy tests green; θ chosen by the agreed method and recorded.
- [ ] Cache lookup ≤ 5 ms p95 at 10k entries per namespace.

## If blocked
- Too few candidate pairs in train (< 100) → report it; use option 2 and say the hit rate can't be
  calibrated on this data.

## End of session
- `work/reports/WP-17-report.md`; update WP-18 replay settings (cache on/off, θ).

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-17 step n", stop.
