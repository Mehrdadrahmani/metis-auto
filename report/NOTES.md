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

## WP-03 Embedder + Qdrant (part 2)
- Latency (one message, MPS, p95, 512 tok): small 311 ms → 221 ms with the LoRA adapter merged; nano
  95 ms → 59 ms (meets the 60 ms budget). Merging gives identical vectors (≤ 4.6e-7); fp16 ≈ no gain.
  Measured on battery (Low Power Mode off), n = 200 calls (40 for merged rows).
- Persian paraphrase vs same-topic pairs (n = 20 + 20, synthetic): AUC with the clustering adapter
  0.61 (small) / 0.66 (nano); text-matching 0.76 / 0.85. Surprise: nano (EuroBERT base) ≥ small on
  every adapter. The clustering adapter groups by topic by design → use text-matching for the cache.
- Sample clusters (K = 4/6, silhouette 0.08–0.15) split mainly by length and language; owner: "partly".
- Embedder choice (small vs nano) deferred to WP-08 on real train data (D-052).
- Possible extra experiment: public Persian benchmarks (Q-023, `ref/docs/persian-datasets.md`).

## WP-03b Persian clustering test (paper protocol, Jina instead of Gecko)
- Public data, $0: 9 benchmarks + Khayyam (gated, granted) + 10,651 Persian chat first messages.
- Protocol = paper: train 60 % / val 400 / test, 10 repeats, K-means on train, K = 3..8 (+ reference K).
- NMI at K = 8 (small / nano): mix vs source 0.35 / 0.35; Khayyam 38 categories 0.42 / 0.41; MMLU 57 subjects
  0.41 / 0.39; one topic 0.10 / 0.11. Chat silhouette 0.15 (benchmarks 0.15–0.30). Measured, 95 % CI ≤ ±0.015.
- Human-difficulty proxy for Prop. 2 (Khayyam examinee error as one "model"): clusters shrink the gap vs
  K = 1 by 5.4 % ± 0.4 (nano, K = 8, Ψ from val 400); one topic ≈ 0 → EmbedLLM vs Headlines reproduced.
- With Ψ from val 400 the gain peaks at K ≈ 8–16 then falls (noise); from train it keeps rising → why K ≤ N_val/50.
- Surprise: text-matching adapter = worse topic clusters but slightly larger difficulty gain (7.7 %).
- Figures: `results/wp03b_persian/figures/persian_*.png`.
- Paper note for the method chapter: UniRoute defines Area (mean accuracy over the normalised budget range) and
  QNC (smallest budget reaching the best test LLM's accuracy, / that LLM's cost) only in words; we formalise them
  with linear interpolation between deferral-curve points (justified by random mixing of two routers).

- Spec check |C_k| ≥ 50 leaves K = 3–4 at val 400 (K = 8: ~5 of 8 clusters under 50). Owner chose the paper's rule
  K ≤ N_val/50 with α = 0 (D-054). Small clusters give noisier Ψ; α = 2 is the robustness check.

## WP-05a Router core (synthetic only)
- K chosen by split-validation (20 halvings, both directions, sessions kept whole): the search for
  7 K values and 61 λ takes 0.05 s.
- Limitation to measure in WP-05b: the deferral area keeps the best points of the scored half, so
  extra clusters can gain area by luck. On 5 no-structure datasets K = 3 beat K = 1 once.

## WP-05b Synthetic proof (simulated, n_test = 300)
- UniRoute minus ZeroRouter area: +0.0845 [+0.0520, +0.1178] with planted structure, -0.0057
  [-0.0253, +0.0217] without. Quality within 1 point of the strong model at 3.6% of its cost.
- Highest-score K selection finds planted K = 3 in 12 of 100 datasets: areas for K = 3..8 differ by
  less than their noise. Mean test area changes by at most 0.0006 (Q-025).
- Exact QNC can read "never reached" over one prompt in 300; show it with QNC within 1 point.

## WP-05 K rule review (simulated, 8 scenarios, 100 datasets each)
- Mean test area: highest score 0.9354, one spread 0.9332, fixed K = 8 0.9360. Owner chose highest
  score, the paper's rule (D-064). K* is not the number of real topics: it found planted K = 3 in
  12 of 100 datasets, with almost no effect on routing.
- What didn't work: the one-spread rule looked better on the datasets used to design it (93 of 100),
  then lost up to 0.0066 area on fresh data with true K = 6.
- A bug was found by a sanity check: Always-best scored above every router until `area()` stopped
  giving credit below a model's cost.

## WP-08 part A (full data, measured)
- 338,325 prompts; 206,729 eligible for val/test, 209,109 for train. Huge prompts 0.12%.
- Eligible prompts: 94.2% Persian, 19.3% RAG; 83.4% not first in session; 21.8% short and not first.
- Train is older and mostly non-RAG; val 87% and test 85% RAG (recent pool 89.5%).
- Standardized differences: val vs test all < 0.1; test vs pool on RAG 0.136.
- Nano vs small (10,000 train prompts): 146 vs 24 prompts/s; 60 vs 239 ms at 512 tokens (p95).
- Near-duplicates at cosine 0.95: 29.4% of train; 50.9% of messages up to 10 chars, 33.4% over 500.
- K = 3..20 on 146,921 prompts: silhouette 0.118 at K = 5, drops to about 0.05 at K = 9.
- Val per cluster uneven from K = 9; clusters with 0 val from K = 16 (n_val = 400).
- GPU memory failed on the longest messages; CPU finished the last 1,162.

## WP-08 paper review (measured, current split, to be replaced)
- Paper p6: success "critically requires" val to reflect deployment; val is a random subset of train.
- Current val vs train gap 0.43 (K = 5); against RAG train 0.055. Val 90.2% company support vs 15.8% overall.
- Stability (ARI, other seeds): 1.00 at K = 3, 5; 0.998 to 1.00 at K = 8; 0.74 to 0.85 at K = 12; 0.71 to 0.82 at K = 20.
- Paper Math+Code (no training labels) uses K = N_val/50, our situation. Static pool tries K from 5 to 300.
- Paper App. G.4: attributes beat text embeddings under prompt shift (.545 vs .529).
- All 1,830 bots: 807 with a description, 1,177 with no prompts; `b_1765` 35.7% of eligible prompts.

## WP-08 split redo (measured, val n = 400)
- Drawing sessions equally over-samples short support chats: val 28.5% support vs 16.0% of eligible prompts. Drawing prompts equally: 16.5%. Top 5% of sessions hold 44% of messages.
- Cost of keeping sessions whole: train falls from 207,839 to 179,185.
- Val vs train gap at K = 5: 0.43 (recent, RAG-balanced split) to 0.05. K-means ARI 0.99 or higher to K = 11, 0.60 to 0.84 at K 12 to 20; silhouette 0.05 to 0.12.
- Messages: median 27 chars; code about 0.09% (pattern count). Bot clusters: silhouette 0.28 at elbow K = 13, ARI 0.82; not used in routing yet.
- Draft cost (simulated): input tokens about 2,800 vs 1,640 planned, mid total $35 vs $25.

## Decisions to explain in the method chapter
- Full data: 710,640 messages, 80,179 sessions; secret scan 1,544 rows hit, 0 left after redaction (`results/wp08_full_data/`). Sample showed live keys in instructions; full data shows 3 such rows.
- Sessions are not independent: intervals resample whole sessions (D-060).
- Data selection and the `workflow` exclusion (D-057): `report/data_selection.md`. State the limitation: results cover direct single-model bots only.
- D-044 local MLflow for tracing and run comparison (vs Phoenix, Langfuse, Opik, cloud tools).
- D-045 / DEV-8 embedding input = current user message only (paper) instead of + 2 turns (spec);
  generation sees the full history (M6).
- D-049 clustering input = "Document: " + message (model-card default).
- D-048 Jina v5-text-small (local, clustering adapter) + Qdrant local; license CC BY-NC 4.0
  (non-commercial: fine for the course, a limitation for production use); Persian coverage checked in WP-03.
- D-047 the whole user message is embedded (no truncation); only light Persian normalization.
- D-046 / DEV-9 judge also sees only the current message (spec had 2 previous turns) → limitation:
  short follow-ups are harder to judge; check in the pilot (WP-11) whether follow-ups disagree more.

## WP-04
- Metis AI margin is about 10% over list prices; routes differ per provider; DeepSeek doubles at peak hours.
- Sonnet is 82% of generation cost ($4.84 of $5.92 for 700 calls per model, planned sizes).
- Judge cost for 2,800 calls (assumed 2,800 in, 150 out tokens): gpt-5.6-terra ~$23, jev-latest ~$0.36.
- Candidate change: gemini-2.5-flash-lite replaces gemini-3.5-flash-lite for a wider quality spread.

## WP-06
- Sonnet 5.5 rejects non-default temperature, so all candidates run at provider defaults (D-084). Provider differences limit a "same settings" comparison.
- Cost estimate (simulated, mean input 2,871 tokens against 1,640 planned): pointwise $47.68, pairwise $62.12, cap $60. Longer prompts and judge price drive the rise.
- Jev has no free-text prompt or reasons, so the two pilot judges differ in form as well as in model (D-086).
- Agreement is measured overall; 100 labels cannot validate the judge per chatbot.

- Near-duplicates at 0.95 removed 29.4% of train, and most removed messages over 10 characters had different text from their match (sample n = 200 per length group). Owner chose to keep them (D-088); frequent messages now weigh more in the clusters.

## WP-07 (mock dry run, sample; numbers below are plumbing, not quality)

- S1 to S12 run from one command. Second run: 0 new calls, 11 of 11 stages identical.
- Leak test first proved nothing: the pilot and all stored eligible prompts hold no key patterns. With 13,720 fake keys planted across all fields, 0 of 4,802 requests carried one.
- Keeping near-duplicates (measured, n_train = 179,185) moved the stability drop from K = 12 to K = 10: mean ARI 0.99 or higher to K = 9, 0.89 at K = 10, 0.85 at K = 11 (three fits). K limit now 9. Silhouette 0.07 to 0.12.
- Limit: changing `n_val` would redraw test, because both use one random sequence. A larger val must add sessions from train.

## WP-09 pilot (measured, n = 100 prompts)
- $5.87 of $10, 2,361 calls, 0 failed.
- A shared token limit is not a shared length limit: Sonnet fits about 1.5 chars per token on this mostly Persian data, others 2.4 to 3. At 1,024, 9% of Sonnet answers were cut against 1 to 3% for others. This would have biased the anchor. Fixed by rising limits on cut answers only (D-095).
- Jev chose position B 443 times against A 291; position consistency 0.755 (n = 400 pairs). Spearman terra against jev 0.709 (n = 499).
- Test-retest, n = 20: terra exact 0.65, within 1 point 1.00; jev mean gap 0.108; jev pairwise same verdict 1.00.
- Cache-key lesson: editing a hashed config would have re-paid all answers, so later passes use their own config files.

## WP-10 Opus labels and routing preview (measured, pilot, not final)
- Labels by Claude Opus, not human (D-098, DEV-14): 10 fresh agents, 100 items, blind, Answer 1 chosen 50, Answer 2 chosen 46, tie 4.
- Acceptable: luna 0.70 (n = 33), flash 0.71 (n = 34), gemini 0.45 (n = 33), Sonnet 0.82 (n = 100). Sonnet preferred 72 of 96 non-ties. Same model family as the rater.
- Judges against the labels: terra best agreement 0.677, best kappa 0.328; jev best agreement 0.697, best kappa 0.355, pass marks chosen on the same labels. Jev pairwise agreement 0.647 (n = 68).
- At pass mark 7, prompts with history (n = 80): terra 0.675, jev 0.688. Without (n = 19): 0.632 both.
- Routing preview, 300 half splits of the pilot, 4 candidates, K = 3 and 8: area difference against ZeroRouter between -0.016 and +0.002, 5-95% ranges include 0. QNC favoured ZeroRouter in 7 of 8 rows. About 6 prompts per cluster at K = 8, so noise dominates.
- Dashboard $6.29 against ledger $5.87 (7% gap).

## Jev with chat history (measured, pilot, against Opus labels, n = 100)
- Pointwise at pass mark 7: agreement 0.68 to 0.74, kappa 0.36 to 0.43. Marks 6 to 7.5 now give 0.72 to 0.74. Pairwise agreement 0.647 (n = 68) to 0.736 (n = 72). Position consistency fell from 0.755 to 0.738 (n = 400); B 441, A 289, tie 70. Mean score 6.81 to 7.40. Spearman old against new 0.749. The earlier split by history did not predict this gain. Rater saw history too, so part of the gain may be shared input.

## WP-11 pilot decision (measured, pilot, against Opus labels, not human)
- Gate 2 failed by one item and the owner went ahead on record: pointwise jev with history, τ = 7, agreement 0.74 (CI 0.65 to 0.82, n = 100, line 0.75), κ 0.431 (CI 0.24 to 0.62), AUC 0.79. The report must state this. Leave-one-out τ gives the same result.
- Pairwise: agreement 0.736 on 72 decided items, 24 of 96 undecided, κ 0.285, position consistency 0.738 (n = 400). A model won 0.367 shown second, 0.188 shown first.
- Separability pointwise 0.333 at K = 1, 0.111 at K = 3, n = 100. Length bias none (ρ 0.008). No visible self-preference for gpt-5.6-luna; gemini over-passed 8 to 3 (n = 33).
- Chat history helped Jev: AUC 0.727 to 0.789. Terra without history AUC 0.727, κ 0.268 at τ = 7. Terra with history not measured.
- Of 26 disagreements, 10 under-passed (mostly required bot behaviour) and 16 over-passed (mostly poor fit to the bot, or weak on the question).
- deepseek-v4-pro against Sonnet: mean gap -0.29 (CI -0.53 to -0.04, n = 100), cost per answer $0.0027 against $0.0156.
- Not done: human check, 20 re-labels, wrong-prompt test.

## WP-12, WP-13 validation and test (measured)
- Pass at 7, n = 400: Sonnet 65.2%, DeepSeek 64.9%, Luna 61.2%, Gemini 53.9%, each about ±5 points. DeepSeek at about 1/26 of Sonnet's price.
- Pilot n = 100 ran higher: 72, 73, 65, 57. All pass 40.9%, all fail 21.3%, ceiling 78.7%. DeepSeek and Sonnet disagree on about 18% of prompts.
- Separability at K = 3 and K = 8: 0.111, 0.042 on the pilot; 0.167, 0.104 on 399 prompts. Part of the rise comes from n.
- Val repeat n = 80: mean gap 0.147, all within 1 point.
- Generation $11.88, judging $0.58. Test answers 1,200, 0 failed, 3 left cut off. Failed val answer: Sonnet error 500 on 3 tries. Jev refused 1 prompt on each set (error 400, cause not confirmed).
- What didn't work: cost estimate counted 500 new prompts, real 600. Guard estimate ignored Sonnet's larger input, so a false stop at 42 of 400. Stored failures blocked resume until fixed. A failed answer read back as NaN and would have crashed the judge; the pilot had none to show it.

## WP-14 validation 800 (measured, val only)
- 400 to 800 removed a false gain: K = 8 area +0.013 over ZeroRouter became -0.002. K* moved from 8 to 4. Worth stating as a lesson: choice of K on 400 was noise.
- Old 400 to new 400, K = 8, cheap setting: -2.0 points vs DeepSeek (-4.2 to 0.0). Shuffle test p = 0.44.
- Cheap setting out of fold, K = 8: 65.4% at 0.042 cost share, DeepSeek 65.4% at 0.041. K = 4 at λ 0.03: 66.9% at 0.417, +1.4 vs ZeroRouter (0.0 to +2.8).
- K-NN ties (0.6636). Area gain over ZeroRouter +0.009, near Headlines in the paper (+0.009).
- Pairwise on 797 prompts: Sonnet beats DeepSeek 40% to 21% both-orders. Pass-rate parity does not mean quality parity. Length not controlled (471 vs 254 tokens out).
- Train was the only safe pool for more val: `none` holds test-session leftovers.

## Product session (2026-11-03, D-125 to D-127)
- Live chat app routes real traffic: 3 smoke calls, $0.0056; balanced λ sends 7 of 8 clusters to DeepSeek because Sonnet's lead (≤ 8 points, 2 clusters) is worth less than its 25× price.
- Adding a model needs only its Psi column on the 798 val prompts (UniRoute); the onboarding code reproduces the 4 shipped columns and c_hat exactly. Estimate for a DeepSeek-priced model: ~$0.85.
- Khayyam per subject (test n = 1,100, true answers): DeepSeek flash best on maths (49%) and physics (59%), Luna on biology (68%) and humanities mix (65%), Gemini on Persian literature (53%). Small clusters mislead (chemistry, 24 val prompts: Gemini picked, 35% on test vs 55%).
- Khayyam through its gateway (replay): 55.5% (offline 55.0%; checks escalated cut answers), 0 failed; Luna down: 54.3%, 0 failed.
- Khayyam chat (D-128): users can type their own exam question; the Khayyam router picks the model live. Demo only, not part of any measured number.
