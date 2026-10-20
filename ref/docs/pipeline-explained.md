# The pipeline, explained step by step (v2)

This is the plain-language version of [`UNIROUTE_PIPELINE.md`](../UNIROUTE_PIPELINE.md) and
[`design.md`](design.md). All numbers in the examples are **illustrative**; the real ones come after
the full dataset arrives.

## The big picture

Think of a manager assigning tasks to five employees with different salaries.

- **Offline ("school"):** the manager sorts many past tasks into types *without grading them*. Then
  every employee does the same small set of a few hundred tasks, the work is graded, and each employee
  gets a **report card**: how often they fail at each type of task.
- **Online ("the job"):** a new task arrives, the manager sees its type, reads the report cards, and
  gives it to the **cheapest employee who is reliably good at that type**.
- **New employee joins:** they only do the same few hundred graded tasks and get their own report card.
  Nobody else is retrained. This is UniRoute's main idea.

---

## Part A: Offline build

### A1. Clean and split the data (S1–S2)

- Each **routable prompt** is the user's last message plus up to 2 earlier turns.
- Secrets are removed first (the dataset's workflow configs contain API keys).
- The data is split **by conversation**, so one conversation never ends up in two places:

| Split | Size | Labeled? | Used for |
|---|---|---|---|
| Train | everything else (ideally ≥ 5,000) | **No** | Only to find the message types (clusters) |
| Validation | 400 | Yes | Report cards, choosing K and λ |
| Calibration | 100 items from validation | Yes, by humans | Checking the judge |
| Test | 300 | Yes | **Only for the final report.** Never used for any choice |

Why keep the train split unlabeled? Grading costs money, and finding message types doesn't need grades.
In v1 we found types and built report cards on the same 377 turns, which overfits.

### A2. Find the message types (S4–S5), free

1. Each prompt becomes an **embedding** (a list of numbers capturing its meaning) using a multilingual
   model running on our own machine.
2. **K-means** groups the train prompts into K clusters. We try K = 3, 4, … up to (validation size ÷ 50),
   so each cluster has at least 50 validation prompts. K = 1 (no clusters) is kept as a baseline.
3. We read 10 prompts per cluster and name them, e.g. "greetings", "technical how-to", "complaints".

### A3. Get real answers (S6)

Every candidate model answers every validation and test prompt **once**, with exactly what production
had: that chatbot's system prompt, retrieved documents and history. Every answer is saved and never
requested again.

### A4. Grade the answers (S7): two possible ways

- **Pointwise:** a judge gives each answer a score from 1 to 10. Pass = score ≥ τ (about 7).
- **Pairwise:** a judge compares each answer with the **anchor**'s answer (the strongest model,
  claude-sonnet-4-6), twice with the order swapped: win, tie or lose.

Which one is better for our traffic? We don't guess: **the pilot** (A5) decides.

### A5. The pilot

On a small part of the data (4 models, 200 validation and 150 test prompts):

1. Grade the same answers **both** ways.
2. Persian speakers label 100 answers without seeing model names: "acceptable?" and "better than
   the anchor?". The judge must agree with them at least 75% of the time.
3. Build two routers, one per grading method, and compare them on four criteria: which routes better
   (A), which agrees more with humans (B), which gives stable report cards (C), which can tell models
   apart (D).
4. Pick one. If it's a tie, pick pointwise (cheaper).

All pilot answers and grades are reused by the full build.

### A6. Build the report cards (S8)

For each cluster and model: the **fail rate** (pointwise) or the **chance of losing to the anchor**
(pairwise), computed on validation prompts only. Small clusters are gently pulled toward the model's
overall rate (smoothing α = 2).

| Cluster | flash-lite | deepseek | gpt-4o-mini | gemini-flash | sonnet |
|---|---|---|---|---|---|
| Greetings | 0.02 | 0.01 | 0.01 | 0.01 | 0.01 |
| Technical | 0.30 | 0.15 | 0.12 | 0.06 | 0.03 |
| Complaints | 0.22 | 0.09 | 0.06 | 0.04 | 0.02 |
| **Cost (0–1)** | 0.02 | 0.03 | 0.04 | 0.20 | 1.00 |

### A7. Choose K and λ (S9–S10), free

- **K:** split the validation set in half many times; build report cards on one half, test routing on
  the other; keep the K that does best.
- **λ:** how much price matters. We choose it for a target quality (or a cost budget).

### A8. Test (S11), free

Only now do we look at the test set. We compare UniRoute with always-best, always-cheapest, ZeroRouter
and K-NN, and also report similarity to production's answers (the brief's metric).

**Simulating a new model:** we hide ~1/3 of the models while choosing K and λ, then route only among
the hidden ones. If that works, adding a real new model later will work too.

---

## Part B: Online, one message

An angry customer writes: *"خانم قرار بود کارشناسا با ما تماس بگیره… لطفا سریع انجام بدین"*.

1. **Hard rules:** not a menu click, not an image, no attachment; every model fits; no provider down.
   → all 5 models allowed.
2. **Embed:** same preprocessing as offline; one vector.
3. **Cache:** a complaint about "since yesterday" is a follow-up → never cached. → skip.
4. **Router:** nearest cluster = "complaints". With λ = 0.4:
   - flash-lite 0.22 + 0.4×0.02 = 0.228
   - deepseek 0.09 + 0.4×0.03 = 0.102
   - gpt-4o-mini 0.06 + 0.4×0.04 = **0.076** ← lowest
   - gemini-flash 0.04 + 0.4×0.20 = 0.120
   - sonnet 0.02 + 0.4×1.00 = 0.420
5. **Call** gpt-4o-mini. If OpenAI fails → the next-lowest score, deepseek.
6. **Checks:** not empty, Persian, not cut off → pass. If a check failed: one repair, then escalate to
   the model with the next-lower fail rate in this cluster (gemini-flash).
7. **Trace:** cluster, scores, model, cost, latency, checks.

**"سلام" (hello):** likely a cache hit within the same chatbot → $0. If not, the "greetings" cluster
has ~0 fail rate everywhere, so the cheapest model wins.

---

## Part C: Keeping it fresh

| Event | What we do | Cost |
|---|---|---|
| New model released | It answers the 400 validation prompts, gets graded, gets its row | ~800 calls |
| Model removed | Delete its row | $0 |
| Price change | Update its cost, re-pick λ | $0 |
| Traffic changes | Recluster on fresh unlabeled data, regroup the stored grades | $0 |
| Weekly | Compare live cluster shares with the validation set (drift check) | small |
