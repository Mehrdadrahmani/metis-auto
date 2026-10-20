# UniRoute Pipeline Specification
**Variant:** UniRoute (K-Means) with two supported label methods: **pointwise** (pass/fail per answer) or **pairwise** (vs. an anchor, Bradley–Terry per cluster). A pilot decides which one to use.
**Audience:** humans (to understand) and coding agents (to implement)
**Source:** Jitkrittum et al., *Universal Model Routing for Efficient LLM Inference*, ICLR 2026. Items marked **[ours]** are adaptations not in the paper.

---

## 0. Read this first

### 0.1 What the system does
Given a user prompt and the set of LLMs currently available, pick the LLM that minimizes

$$\text{predicted loss on this kind of prompt} \;+\; \lambda \times \text{cost}.$$

Each LLM is described by a **fingerprint**: its loss in each of $K$ prompt clusters, measured on a small labeled validation set. A new LLM can be added by computing its fingerprint. **No retraining.**

### 0.2 Fixed design decisions

| Decision | Choice |
|---|---|
| Prompt representation | Frozen multilingual text embedder, run locally |
| Prompt grouping | K-means (hard assignment). LearnedMap is out of scope (see §11) |
| Label method | `method` ∈ {`point`, `pair`}; chosen by the pilot (§P) |
| Pointwise labels | the judge scores each answer 1–10; pass = score ≥ τ |
| Pairwise labels | the judge compares each answer with the anchor's answer **[ours]** |
| Per-cluster loss | `point`: fail rate (paper Eq. 12) · `pair`: Bradley–Terry $P(\text{lose to anchor})$ (paper App. G.4) |
| Choosing $K$ | Split-validation, no training-set labels **[ours]** |
| Cost | One number per model, normalized to $[0,1]$ |

### 0.3 Golden rules (invariants an agent must never break)
1. **The test set is never used for any choice** (method, K, λ, τ, rubric, thresholds). Only for the final report.
2. **Every LLM call and judge call is cached** under a deterministic key and is never repeated if a cached result exists.
3. **Answers are generated once and shared by both label methods.** Switching methods never regenerates answers.
4. **Pairwise only:** the anchor's answers are generated once and frozen. All comparisons use the cached anchor answers, so the anchor model can later be retired from serving.
5. **Pointwise only:** the raw 1–10 score is stored, so τ can be changed without new judge calls. τ is chosen on the human calibration set, never on the test set.
6. **The training split is unlabeled.** It is used only for K-means.
7. **Fingerprints are computed only from validation-set labels.**
8. All randomness (splits, K-means init, order of A/B in judging) uses a recorded seed.

---

## 1. Notation

| Symbol | Meaning |
|---|---|
| $x$ | a prompt (last user turn + truncated context) |
| $\varphi(x)\in\mathbb{R}^{D}$ | frozen, L2-normalized embedding of $x$ |
| $S_{\text{tr}}, S_{\text{val}}, S_{\text{te}}$ | train (unlabeled), validation (labeled), test (labeled) prompt sets |
| $S_{\text{cal}}$ | human calibration set (~100 items from $S_{\text{val}}$), used to validate judges and choose τ |
| $N_{\text{val}}=\lvert S_{\text{val}}\rvert$ | validation size (target 400–800) |
| $\mathcal{H}=\{h_1,\dots,h_N\}$ | candidate LLMs |
| $a\in\mathcal{H}$ | anchor model (pairwise only; strongest model at build time) |
| $c(h)$ | raw cost per prompt of model $h$; $\hat c(h)=c(h)/\max_{h'}c(h')$ normalized |
| $K$ | number of clusters |
| $\mu_1..\mu_K$ | K-means centroids |
| $k(x)$ | cluster of $x$: $\arg\max_k \varphi(x)^\top\mu_k$ |
| $C_k$ | validation prompts in cluster $k$ |
| **Pointwise** | |
| $q(x,h)\in\{1..10\}$ | judge score of $h$'s answer to $x$ |
| $\tau$ | pass threshold (default 7) |
| $p(x,h)=\mathbb{1}[q(x,h)\ge\tau]$ | pass label |
| $\ell_{\text{pt}}(x,h)=1-p(x,h)$ | pointwise loss (1 = fail) |
| **Pairwise** | |
| $o(x,h)\in[0,1]$ | outcome of $h$ vs anchor (1 = $h$ wins, 0.5 = tie, 0 = anchor wins) |
| $\ell_{\text{pw}}(x,h)=1-o(x,h)$ | pairwise loss ($\ell_{\text{pw}}(x,a)=0.5$ by definition) |
| $\beta_k(h)$ | Bradley–Terry strength of $h$ in cluster $k$ ($\beta_k(a)=0$) |
| **Shared** | |
| $\ell(x,h)$ | the loss of the active method: $\ell_{\text{pt}}$ or $\ell_{\text{pw}}$ |
| $\Psi_k(h)$ | **fingerprint entry**: loss of $h$ in cluster $k$ under the active method |
| $\lambda\ge 0$ | cost/quality trade-off |

---

## 2. Pipeline overview

```
PILOT (recommended, §P): run S1–S11 on a small subset with method = both → pick a method

FULL BUILD (chosen method)
 S1  Ingest & clean prompts
 S2  Split → S_tr (unlabeled, large) | S_val (~400-800) | S_te (~200-500) | S_cal ⊂ S_val
 S3  Model registry + costs (+ anchor if pairwise)
 S4  Embed all prompts (local)                              ← no API calls
 S5  K-means on S_tr for each candidate K                   ← no API calls
 S6  Generate answers on S_val and S_te (shared)            ← API (generation)
 S7  Judge:  S7-PT pointwise  |  S7-PW pairwise vs anchor   ← API (judge)
 S8  Fingerprints: S8-PT fail rates | S8-PW Bradley–Terry   ← no API calls
 S9  Choose K by split-validation                           ← no API calls
 S10 Choose λ on S_val                                      ← no API calls
 S11 Evaluate on S_te vs baselines                          ← no API calls
 S12 Package router artifact

ONLINE (per request, identical for both methods)
 embed x → nearest centroid k → argmin_h [Ψ_k(h) + λ·ĉ(h)] over available h → call 1 LLM

MAINTENANCE
 add model | remove model | price change | drift check | recluster
```

**Key properties:**
- The paid steps (S6, S7) do not depend on $K$. Changing $K$ or re-clustering only re-groups stored labels.
- The two methods differ **only** in S7 and S8. Everything downstream consumes a fingerprint table $\Psi$ and a per-prompt loss $\ell$, whichever method produced them.

---

## 3. Data artifacts (schemas)

All tables are keyed by stable IDs. Field names are suggestions; keep the semantics.

| Artifact | Key | Fields |
|---|---|---|
| `prompts` | `prompt_id` | `text`, `context_turns`, `lang`, `source_conversation_id`, `user_hash`, `timestamp`, `split` ∈ {train, val, test}, `in_cal` (bool) |
| `models` | `model_id` | `provider`, `api_name`, `price_in`, `price_out`, `is_anchor`, `exp_role` ∈ {dev, holdout} (experiment mode only), `active` |
| `gen_config` | `gen_config_id` | system prompt, temperature, max output tokens, hash |
| `responses` | (`prompt_id`, `model_id`, `gen_config_id`) | `text`, `tokens_in`, `tokens_out`, `latency_ms`, `status` ∈ {ok, failed} |
| `point_judgments` | (`prompt_id`, `model_id`, `judge_config_id`) | `score` (1–10), `reason`, `raw_output` |
| `pair_judgments` | (`prompt_id`, `model_id`, `order` ∈ {h_first, a_first}, `judge_config_id`) | `verdict` ∈ {h, anchor, tie}, `reason`, `raw_output` |
| `human_labels` | (`prompt_id`, `model_id`) | `human_pass` (bool), `human_pref` ∈ {h, anchor, tie} |
| `labels` | (`prompt_id`, `model_id`, `method`) | $\ell(x,h)$ for that method (derived; recomputable) |
| `embeddings` | `prompt_id` | vector $\varphi(x)$, `embedder_id` |
| `clusterings` | (`K`, `seed`) | centroids, assignment of every val/test prompt |
| `fingerprints` | (`method`, `K`, `model_id`) | $\Psi_{1..K}(h)$, per-cluster counts $n_k(h)$ |
| `router_artifact` | `version` | see §S12 |

---

## P. Label-method pilot (run before the full build)

**Goal:** decide empirically between `point` and `pair` for your traffic.

**Pilot sizes (defaults):** 4 models (including a strong model to act as anchor), $N_{\text{val}}=200$, $N_{\text{te}}=150$, $\lvert S_{\text{cal}}\rvert=100$.

**Procedure:**
1. Run S1–S6 at pilot sizes.
2. Run **both** S7-PT and S7-PW on the same answers.
3. Human calibration: for each item in $S_{\text{cal}}$ (a prompt + one non-anchor model), a person records `human_pass` for that model's answer **and** `human_pref` between it and the anchor's answer. Hide model names; randomize order.
4. Choose τ on $S_{\text{cal}}$ (see S7-PT).
5. Build two routers with S8–S10, identical except for the fingerprint table: **R-point** and **R-pair**. Each chooses its own $K$ and λ on $S_{\text{val}}$.
6. Compute the four criteria below on the pilot's $S_{\text{te}}$ / $S_{\text{cal}}$.

**Criteria:**

| # | Criterion | How to compute |
|---|---|---|
| A | **Cross-evaluation** (primary) | Evaluate both routers on $S_{\text{te}}$ under **both** quality measures (§7): pass rate $Q_{\text{pt}}$ and win-rate-vs-anchor $Q_{\text{pw}}$. That gives a 2×2 table of deferral areas and QNC. |
| B | **Human agreement** | Pointwise: accuracy of $p(x,h)$ vs `human_pass`. Pairwise: accuracy of the judge verdict vs `human_pref`, on items where the human did not say tie. |
| C | **Fingerprint stability** | Over $R=5$ random halvings of $S_{\text{val}}$, compute $\Psi$ on each half and take the Pearson correlation of the two $N\times K$ tables; average. Report it next to the number of judge calls spent. |
| D | **Separability** | The fraction of (cluster, model pair) cells where $\lvert\Psi_k(h)-\Psi_k(g)\rvert>2\sqrt{\text{SE}_k(h)^2+\text{SE}_k(g)^2}$, with $\text{SE}=\sqrt{\Psi(1-\Psi)/n_k}$. A low value means the labels can't tell models apart (e.g., everyone passes). |

**Decision rule:**
1. If one method wins A in **both** columns (or wins the other method's column), choose it.
2. Otherwise choose the method with the higher B.
3. If still tied (differences within noise), choose **`point`**: it is cheaper (one judge call per answer, no anchor dependency).

Record the decision, the 2×2 table and B–D in the report.

**Pilot cost:**

$$\underbrace{4\cdot350}_{\text{gen}}+\underbrace{4\cdot350}_{\text{point}}+\underbrace{3\cdot350\cdot2}_{\text{pair}}=1{,}400+1{,}400+2{,}100=\mathbf{4{,}900}\ \text{calls}$$

After the pilot, the full build runs **only the chosen method's** judging. Pilot answers and judgments are reused (they are cached).

---

## 4. Offline build — stage by stage

Each stage lists **Goal / Inputs / Procedure / Outputs / Checks / API calls**.

### S1 — Ingest & clean prompts
- **Goal:** turn raw chat logs into routable prompts.
- **Procedure:**
  1. Define the routable unit: the **last user message** plus up to $T$ previous turns (default $T=2$), truncated to a max token length.
  2. Remove empty, junk and spam messages; strip PII.
  3. Tag language (Persian / English / mixed / other).
  4. De-duplicate: exact duplicates, then near-duplicates (after S4: cosine > 0.95 → keep one).
- **Checks:** report counts removed per rule; language distribution.
- **API calls:** 0.

### S2 — Split
- **Procedure:** split **by user or by time** (never let one conversation appear in two splits).
  - $S_{\text{val}}$: 400–800 prompts, random sample from the most recent period.
  - $S_{\text{te}}$: 200–500 prompts, same sampling as val.
  - $S_{\text{tr}}$: everything else (ideally ≥ 5,000). Unlabeled.
  - $S_{\text{cal}}$: ~100 items drawn from $S_{\text{val}}$ (prompt + one non-anchor model each), spread across models.
- **Checks:** language and length distributions of val ≈ test ≈ recent traffic.
- **API calls:** 0.

### S3 — Model registry, costs, anchor
- **Procedure:**
  1. Register every candidate model in `models`.
  2. **Pairwise only:** pick the **anchor** $a$, the strongest model available now. (Pointwise needs no anchor; every model is judged on its own.)
  3. Cost per prompt (after S6, from real token counts on $S_{\text{val}}$):
  $$c(h)=\overline{\text{tokens\_in}}\cdot\text{price\_in}(h)+\overline{\text{tokens\_out}}(h)\cdot\text{price\_out}(h),\qquad \hat c(h)=\frac{c(h)}{\max_{h'}c(h')}$$
  4. *Experiment mode only:* mark ~1/3 of models as `holdout` to simulate "new, unseen" models (paper §6). Production mode uses all models.
- **API calls:** 0.

### S4 — Embed
- **Procedure:** embed every prompt with one frozen **multilingual** embedder that handles Persian well (e.g., a BGE-M3 / multilingual-E5 class model), run locally. L2-normalize.
- **API calls:** 0.

### S5 — K-means on the training split
- **Candidate set:** $\mathcal{K}=\{3,4,\dots,\lfloor N_{\text{val}}/50\rfloor\}$ (paper App. G.2), plus $K=1$ as a baseline.
- **Procedure:** for each $K\in\mathcal{K}$ run K-means on $\{\varphi(x):x\in S_{\text{tr}}\}$, minimizing
  $$\sum_{x\in S_{\text{tr}}}\min_{k}\lVert\varphi(x)-\mu_k\rVert^2$$
  with k-means++ init, ≥ 10 restarts, fixed seed. Assign every val and test prompt: $k(x)=\arg\max_k\varphi(x)^\top\mu_k$.
- **Checks:** every cluster has $\lvert C_k\rvert\ge n_{\min}=50$ validation prompts (else drop that $K$); print 10 random prompts per cluster; clusters should be nameable.
- **API calls:** 0.

### S6 — Generate answers (shared by both methods)
- **Procedure:**
  1. Fix one `gen_config` for all models (same system prompt, temperature, max output tokens).
  2. Generate every model (including the anchor, if any) on all of $S_{\text{val}}\cup S_{\text{te}}$. The anchor's answers are frozen once generated.
  3. Cache key = (`prompt_id`, `model_id`, `gen_config_id`). Retry transient errors; persistent failure → `status=failed`.
- **Policy [ours]:** a failed response counts as the worst label: score 1 (pointwise) or $o=0$ (pairwise).
- **API calls:** $N\cdot(N_{\text{val}}+N_{\text{te}})$.

### S7-PT — Pointwise judging
- **Goal:** for each (prompt, model), a score $q(x,h)\in\{1..10\}$ and a pass label $p(x,h)$.
- **Judge:** a strong Persian-capable LLM, ideally not in the candidate pool. Temperature 0. Blind (no model names). Prompt: Appendix A2.
- **Procedure:** for every $x\in S_{\text{val}}\cup S_{\text{te}}$ and **every** model $h$ (anchor included, if one exists):
  1. Judge the single answer → store `score` and `reason`.
  2. Parse failure → retry once → else drop and log.
- **Choosing τ [ours]:** on $S_{\text{cal}}$, pick
  $$\tau^\star=\arg\max_{\tau\in\{4,\dots,9\}}\ \frac{1}{\lvert S_{\text{cal}}\rvert}\sum_{(x,h)\in S_{\text{cal}}}\mathbb{1}\big[\mathbb{1}[q(x,h)\ge\tau]=\texttt{human\_pass}(x,h)\big]$$
  If $S_{\text{cal}}$ is not available, use $\tau=7$.
- **Loss:** $\ell_{\text{pt}}(x,h)=1-\mathbb{1}[q(x,h)\ge\tau^\star]$.
- **Gate [ours]:** judge–human pass/fail agreement on $S_{\text{cal}}$ ≥ 75% (suggested). If below, revise the rubric and re-check.
- **API calls:** $N\cdot(N_{\text{val}}+N_{\text{te}})$.

### S7-PW — Pairwise judging vs anchor
- **Goal:** for each (prompt, non-anchor model), an outcome $o(x,h)$.
- **Judge:** as in S7-PT. Prompt: Appendix A1.
- **Procedure:** for every $x\in S_{\text{val}}\cup S_{\text{te}}$ and every $h\neq a$:
  1. Judge (A = $h$, B = anchor) and (A = anchor, B = $h$). The order swap removes position bias.
  2. Map each verdict to a score for $h$: win = 1, tie = 0.5, loss = 0. Call them $s_1,s_2$.
  3. $o(x,h)=\tfrac12(s_1+s_2)$. (Disagreement between orders automatically becomes 0.5.)
  4. Parse failure → retry once → else drop and log.
- **Budget mode:** judge once with a random order ($o=s_1$); record that this was done.
- **Loss:** $\ell_{\text{pw}}(x,h)=1-o(x,h)$; $\ell_{\text{pw}}(x,a)=0.5$.
- **Gate [ours]:** judge–human preference agreement on non-tie $S_{\text{cal}}$ items ≥ 75% (suggested).
- **API calls:** $(N-1)\cdot(N_{\text{val}}+N_{\text{te}})\cdot J$, with $J=2$ (order swap) or $J=1$.

### S8-PT — Pointwise fingerprints (paper Eq. 12)
- **Raw per-cluster fail rate:**
  $$\Psi^{\text{raw}}_k(h)=\frac{1}{\lvert C_k\rvert}\sum_{x\in C_k}\ell_{\text{pt}}(x,h)$$
- **Smoothing [ours]:** shrink small clusters toward the model's overall fail rate $\bar f(h)=\frac{1}{N_{\text{val}}}\sum_{x\in S_{\text{val}}}\ell_{\text{pt}}(x,h)$:
  $$\boxed{\Psi_k(h)=\frac{\sum_{x\in C_k}\ell_{\text{pt}}(x,h)+\alpha\,\bar f(h)}{\lvert C_k\rvert+\alpha}}$$
  With $\alpha=0$ this is exactly the paper's Eq. 12.
- **Checks:** all $\Psi_k(h)\in[0,1]$; print the $N\times K$ table with cluster names; flag a ceiling (all models' $\Psi_k<0.05$ in a cluster).
- **API calls:** 0.

### S8-PW — Pairwise fingerprints (Bradley–Terry per cluster)
- **Model:** in cluster $k$, $P(h\succ g\mid k)=\sigma\big(\beta_k(h)-\beta_k(g)\big)$, with $\sigma(z)=1/(1+e^{-z})$ and $\beta_k(a)=0$.
- **Fit:** for each cluster $k$, maximize over $\beta_k$
  $$\sum_{x\in C_k}\sum_{h\neq a}\Big[o(x,h)\log\sigma(\beta_k(h))+\big(1-o(x,h)\big)\log\big(1-\sigma(\beta_k(h))\big)\Big]$$
  plus **smoothing [ours]:** $\alpha$ virtual ties (default $\alpha=2$) between each model and the anchor in each cluster. If non-anchor pairs ($h$ vs $g$) are ever judged, they enter the same likelihood with $\sigma(\beta_k(h)-\beta_k(g))$.
- **Fingerprint [ours]:**
  $$\boxed{\Psi_k(h)=P(a\succ h\mid k)=1-\sigma\big(\beta_k(h)\big)},\qquad \Psi_k(a)=0.5$$
- **Closed form (anchor-only design; use it to verify the implementation):**
  $$\Psi_k(h)=1-\frac{\sum_{x\in C_k}o(x,h)+0.5\,\alpha}{\lvert C_k\rvert+\alpha}$$
- **Checks:** all $\Psi_k(h)\in(0,1)$; anchor row = 0.5.
- **API calls:** 0.

### S9 — Choose $K$ (split-validation) [ours]
The paper (App. G.2) tunes $K$ with training-model labels on $S_{\text{tr}}$. We avoid labeling $S_{\text{tr}}$:
1. For each $K\in\mathcal{K}$ and each of $R$ random halvings (default $R=5$) of $S_{\text{val}}$ into $A,B$:
   - compute $\Psi$ on $A$ (S8 restricted to $A$, active method);
   - route every $x\in B$ with the §5 rule over a λ grid, using **realized** losses $\ell(x,h)$ on $B$;
   - compute the normalized deferral area (§7) on $B$; swap $A\leftrightarrow B$; average.
2. Pick $K^\star=\arg\max_K$ mean area. Ties → smaller $K$.
3. Experiment mode: route only among `dev` models here.
4. Recompute $\Psi$ for $K^\star$ on **all** of $S_{\text{val}}$.
- **API calls:** 0.

### S10 — Choose λ
- **Grid:** $\Lambda=\{0\}\cup\{10^{-3},\dots,10^{2}\}$ (≈ 60 log-spaced values).
- For each $\lambda$, on $S_{\text{val}}$:
  $$\text{Cost}(\lambda)=\frac{1}{N_{\text{val}}}\sum_{x}\hat c\big(r_\lambda(x)\big),\qquad \text{Quality}(\lambda)=\frac{1}{N_{\text{val}}}\sum_{x}\big(1-\ell(x,r_\lambda(x))\big)$$
- **Budget mode** (paper App. E): the smallest λ with $\text{Cost}(\lambda)\le B$.
- **Quality mode:** the largest λ with $\text{Quality}(\lambda)\ge Q_{\text{target}}$.
- Re-run whenever the pool or prices change (no labels, no API calls).

### S11 — Evaluate on the test set
- Fingerprints come from $S_{\text{val}}$; λ is swept; realized losses come from $S_{\text{te}}$ labels.
- **Experiment mode:** route among `holdout` models only; $K^\star$ was chosen with `dev` models only.
- **Methods to compare** (same pool, same λ/budget grid):

| Method | Rule |
|---|---|
| Always-best | the model with the lowest overall val loss |
| Always-cheapest | $\arg\min_h c(h)$ |
| ZeroRouter (paper App. D) | the lower convex hull of $(\hat c(h), \bar\ell_{\text{val}}(h))$; for budget $B$ between hull models $m_1,m_2$ route to $m_1$ w.p. $\frac{c_{m_2}-B}{c_{m_2}-c_{m_1}}$, else $m_2$ |
| K-NN (paper Eq. 4) | $\gamma(x,h)=\frac{1}{k}\sum_{j\in\text{NN}_{\text{val}}(x,k)}\ell(x_j,h)$; tune $k$ by split-validation |
| **UniRoute (K-Means)** | §5 rule with $K^\star$ |

- **Metrics:** deferral area and QNC (§7); per-cluster quality; routing share per model; cost saved at quality parity with Always-best. If both label methods exist (pilot), also the 2×2 cross-evaluation (§P, criterion A).
- **API calls:** 0.

### S12 — Package the router artifact
Contents (versioned):
- `method` (point/pair), plus τ★ (point) or anchor id (pair);
- `embedder_id` + preprocessing config;
- $K^\star$, centroids, cluster names;
- the fingerprint table $\Psi\in[0,1]^{N\times K^\star}$ + per-cluster counts;
- $\hat c(h)$ per model, the price snapshot;
- λ and the mode with its target;
- hashes of $S_{\text{val}}$, gen_config, judge_config; the build date.

---

## 5. Online routing algorithm (identical for both methods)

**Input:** prompt $x$ (+ context), the currently available models $\mathcal{A}\subseteq\mathcal{H}$.

1. Preprocess exactly as in S1.
2. $\varphi(x)$ ← local embedder; $k^\star=\arg\max_k\varphi(x)^\top\mu_k$.
3. For each $h\in\mathcal{A}$ with a fingerprint:
   $$s(h)=\Psi_{k^\star}(h)+\lambda\,\hat c(h)$$
   (paper Eq. 8 with $\gamma(x,h)=\Phi_{\text{clust}}(x)^\top\Psi_{\text{clust}}(h)$, Eq. 11).
4. Route to $\arg\min_h s(h)$; ties → the cheaper model.
5. On failure or timeout → next-lowest $s(h)$.
6. Log (`prompt_id`, $k^\star$, chosen model, all scores, artifact version).

---

## 6. Maintenance operations

| Operation | Steps | API calls (point / pair) |
|---|---|---|
| **Add model** | S6 for the new model on $S_{\text{val}}$ (and $S_{\text{te}}$ for reports) → S7 for it (pair: vs the **cached** anchor answers) → S8 for that row only → cost → S10 | $2N_{\text{val}}$ / $N_{\text{val}}(1+J)$ |
| **Remove model** | `active=false`; drop its row; S10 | 0 |
| **Price change** | update $c(h)$, $\hat c$; S10 | 0 |
| **Change τ** (point) | recompute $\ell_{\text{pt}}$ from stored scores → S8–S10 | 0 |
| **Recluster** | S4–S5 on fresh $S_{\text{tr}}$ → regroup stored val labels → S8–S10 | 0 |
| **Refresh validation set** | new $S_{\text{val}}$; S6–S10 for all active models | full validation cost |
| **Drift check** (e.g., weekly) | compare live cluster shares with $S_{\text{val}}$; optionally judge a small sample of live answers | small |

Pairwise: the anchor may be retired from serving; its cached answers remain the reference. Changing the anchor requires re-judging everything.

---

## 7. Evaluation definitions

- **Quality of a routed system on a set $S$:**
  $$Q_{\text{pt}}=\frac{1}{\lvert S\rvert}\sum_{x\in S}p\big(x,r(x)\big)\ \ (\text{pass rate}),\qquad Q_{\text{pw}}=\frac{1}{\lvert S\rvert}\sum_{x\in S}o\big(x,r(x)\big)\ \ (\text{win rate vs anchor; anchor}=0.5)$$
  A router is normally evaluated with its own method's measure. Cross-evaluation (pilot) uses both.
- **Deferral curve** (paper App. F.2): the points $\big(\text{Cost}(\lambda),Q(\lambda)\big)$ for $\lambda\in\Lambda$; take the upper Pareto envelope and interpolate linearly (achievable by randomizing between two λ).
- **Normalized area:**
  $$\text{Area}=\frac{1}{\hat c_{\max}-\hat c_{\min}}\int_{\hat c_{\min}}^{\hat c_{\max}}\tilde Q(b)\,db$$
- **QNC:** with $h^\dagger$ the best single model (quality $Q^\dagger$),
  $$\text{QNC}=\frac{\min\{b:\tilde Q(b)\ge Q^\dagger\}}{\hat c(h^\dagger)}$$
  Report 100% if never reached.

---

## 8. Defaults

| Parameter | Default | Source |
|---|---|---|
| $N_{\text{val}}$ | 400 (up to 800) | paper uses 400 |
| $n_{\min}$ per cluster | 50 | paper's $K\le N_{\text{val}}/50$ |
| $\mathcal{K}$ | $\{3..\lfloor N_{\text{val}}/50\rfloor\}$ | paper App. G.2 |
| K-means | k-means++, ≥ 10 restarts | standard |
| Context turns $T$ | 2 | [ours] |
| Pass threshold τ | chosen on $S_{\text{cal}}$; fallback 7 | [ours] |
| Smoothing $\alpha$ | 2 | [ours] |
| Split-validation repeats $R$ | 5 | [ours] |
| λ grid | $\{0\}\cup$ 60 log-spaced in $[10^{-3},10^2]$ | [ours] |
| Pairwise order swap $J$ | 2 | [ours] |
| Judge–human agreement gate | ≥ 75% | [ours] |
| $\lvert S_{\text{cal}}\rvert$ | 100 | [ours] |
| Pilot sizes | 4 models, 200 val, 150 test | [ours] |

---

## 9. API budget formulas

$$\text{Gen}=N(N_{\text{val}}+N_{\text{te}})$$
$$\text{Judge}_{\text{point}}=N(N_{\text{val}}+N_{\text{te}}),\qquad \text{Judge}_{\text{pair}}=(N-1)(N_{\text{val}}+N_{\text{te}})\,J$$
$$\text{Add model: point}=2N_{\text{val}},\qquad \text{pair}=N_{\text{val}}(1+J)$$

Example: $N=8$, $N_{\text{val}}=400$, $N_{\text{te}}=300$, $J=2$:

| | Generation | Judging | Total | Add a model |
|---|---|---|---|---|
| Pointwise | 5,600 | 5,600 | **11,200** | 800 |
| Pairwise | 5,600 | 9,800 | **15,400** | 1,200 |

Pilot (§P): **4,900** calls; its results are reused by the full build.

---

## 10. Acceptance checklist

- [ ] No prompt or conversation appears in two splits.
- [ ] Every val cluster has ≥ $n_{\min}$ prompts for $K^\star$; clusters are human-nameable.
- [ ] Pilot decision recorded with the 2×2 cross-evaluation and criteria B–D.
- [ ] Judge–human agreement gate passed for the chosen method.
- [ ] Pointwise: τ was chosen on $S_{\text{cal}}$, not on the test set; with $\alpha=0$, S8-PT reproduces paper Eq. 12 exactly.
- [ ] Pairwise: the anchor-only closed form matches the BT fit; the anchor row = 0.5.
- [ ] The test set was not used for method, K, λ, τ, rubric or thresholds.
- [ ] UniRoute's area ≥ ZeroRouter's and K-NN's on the test set (if not, see §12).
- [ ] Adding a mock new model touches only that model's row and λ.
- [ ] A rerun gets cache hits for every call (zero new API spend).

---

## 11. Out of scope now: LearnedMap (later)
Upgrade path (paper §5.2, App. F.3): replace the hard $k(x)$ with soft weights $\Phi(x;\theta)=\text{Softmax}(\text{MLP}(\varphi(x)))$ (2 hidden layers × 128, BatchNorm, ReLU), trained for 5 epochs (Adam, lr 0.005, batch 64) with binary cross-entropy so that $\Phi(x;\theta)^\top\Psi(h)$ predicts the losses of a few *training models* on $S_{\text{tr}}$. Works with either label method (pointwise losses fit the paper's loss directly).
**Extra requirement:** labels on a few thousand $S_{\text{tr}}$ prompts for 3–5 diverse models.

---

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| UniRoute ≈ ZeroRouter | clusters don't separate model strengths | inspect the Ψ table; try another embedder or $K$; consider LearnedMap |
| Pointwise Ψ ≈ 0 for most models | ceiling: pass bar too low | raise τ; or switch to pairwise |
| Big gap between val and test results | val doesn't match traffic | resample val from recent traffic |
| Erratic Ψ for some cells | small clusters | lower $K$, raise $\alpha$, enlarge $S_{\text{val}}$ |
| One model always chosen | λ grid too narrow, or costs not normalized | check $\hat c$; widen the grid |
| Judge prefers long answers | length bias | tighten the rubric; cap max tokens |

---

## 13. Provenance: paper vs. this pipeline

| Element | Paper | This pipeline |
|---|---|---|
| Labels | binary correctness from benchmark datasets | `point`: judge score → pass/fail; `pair`: judge vs anchor |
| Per-cluster score | error rate (Eq. 12); BT on Chatbot Arena (G.4) | `point`: smoothed fail rate (= Eq. 12 at α=0); `pair`: BT → $P(\text{lose to anchor})$ |
| Choosing the label method | n/a | pilot with cross-evaluation (§P) |
| Choosing $K$ | training-model labels on $S_{\text{tr}}$ (G.2) | split-validation on $S_{\text{val}}$ |
| Routing rule | Eq. 8 / 11 | identical |
| λ selection | sweep / line search (App. E) | identical |
| Metrics | deferral area, QNC | identical definitions, operationalized in §7 |

---

## Appendix A1 — Pairwise judge prompt

```
You are an impartial expert evaluator. Compare two AI assistant responses to the same
user request. The user may write in Persian, English, or a mix.

[CONVERSATION CONTEXT]
{context_turns}

[USER REQUEST]
{prompt}

[RESPONSE A]
{response_a}

[RESPONSE B]
{response_b}

Judge using these criteria, in priority order:
1. Correctness — factual accuracy; correct code/math. Errors weigh heavily.
2. Instruction following — does it do what was actually asked?
3. Language — answers in the user's language; natural, fluent Persian when the user wrote Persian.
4. Helpfulness and completeness — addresses the real need.
5. Concision — do NOT prefer a response for being longer.
6. Safety — penalize harmful content and unjustified refusals.

Ignore the order in which responses are shown. Ignore style that does not affect usefulness.
If both are equally good or equally bad, answer "tie".

Return only JSON:
{"reason": "<2-4 sentences>", "verdict": "A" | "B" | "tie"}
```

## Appendix A2 — Pointwise judge prompt

```
You are a strict, impartial expert evaluator. Rate one AI assistant response to a user
request. The user may write in Persian, English, or a mix.

[CONVERSATION CONTEXT]
{context_turns}

[USER REQUEST]
{prompt}

[RESPONSE]
{response}

Evaluate using these criteria, in priority order:
1. Correctness — factual accuracy; correct code/math. Any significant error caps the score at 4.
2. Instruction following — does it do what was actually asked?
3. Language — answers in the user's language; natural, fluent Persian when the user wrote Persian.
4. Helpfulness and completeness — addresses the real need.
5. Concision — do NOT reward length.
6. Safety — penalize harmful content and unjustified refusals.

Scoring scale:
 1-2  wrong, harmful, unusable, or a refusal of a reasonable request
 3-4  major errors or misses the main point
 5-6  partly useful; noticeable gaps or errors; the user would likely need to ask again
 7-8  correct and useful; a demanding user would accept it without asking again
 9-10 excellent: correct, complete, well-targeted, nothing meaningful to improve

Write the reason first, then the score.
Return only JSON:
{"reason": "<2-4 sentences>", "score": <integer 1-10>}
```

---

## Appendix B — Worked example (works the same with either method)

$K=3$ clusters (coding, Persian literature, casual chat); λ = 0.4. Below are pairwise fingerprints (anchor = S); pointwise fail rates plug into the same rule.

| Model | $\Psi_{\text{coding}}$ | $\Psi_{\text{lit}}$ | $\Psi_{\text{chat}}$ | $\hat c$ |
|---|---|---|---|---|
| S (anchor) | 0.50 | 0.50 | 0.50 | 1.00 |
| M | 0.62 | 0.80 | 0.52 | 0.30 |
| C | 0.85 | 0.92 | 0.55 | 0.05 |

A casual-chat prompt: $s(S)=0.50+0.40=0.90$, $s(M)=0.52+0.12=0.64$, $s(C)=0.55+0.02=\mathbf{0.57}$ → **route to C**.
A Persian-literature prompt: $s(S)=0.90$, $s(M)=0.80+0.12=0.92$, $s(C)=0.92+0.02=0.94$ → **route to S**.
