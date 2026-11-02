# TakRouter: a measured LLM router for Persian chatbots

Draft for owner review. It has not had the fresh-session review WP-20 asks for. Every number comes from `results/`.

## 1. Problem
Chatbot traffic is mostly Persian, and sending everything to a premium model is expensive. The goal: pick a model per message, cut cost, keep quality, and add the gateway parts the brief requires (semantic cache, cascade, failover, observability).

## 2. Data
338,325 prompts in the prepared table. Secrets inside `instructions` are masked before any model call. Validation 800 prompts (798 scored), test 300 (299 scored), both drawn at random. Clusters come from user text only. `category` is empty, so per-category analysis was not possible.

## 3. Method
UniRoute as in the paper: K-means on unlabeled train prompts, fingerprints Ψ on validation with Eq. 12, and online rule s(h) = Ψ_k(h) + λ·ĉ(h). Main deviations: val grown to 800 (DEV-15), λ chosen out of fold to not fall below always-DeepSeek (DEV-16), judge Jev not GPT-5.x, K chosen by owner at 8 although the rule gave 4 (D-117).

## 4. Labels
Pointwise Jev scores, pass ≥ 7. Pilot agreement 0.74 (line 0.75), kappa 0.431, AUC 0.79, against Opus labels, not human ones. The wrong-prompt test and 20 re-labels were not done. Repeats on test, n = 60: mean gap 0.137, 5% flipped pass or fail.

## 5. Router results
See `results/final/test_report.md` and `results/final/figures/cost_quality.png`. Against Sonnet all 3 criteria were met. Against DeepSeek the shipped router adds nothing: -1.7 points (-3.8 to +0.3). Area differences across routers all include 0. Validation predicted this: no router clearly beat DeepSeek at low cost. So cluster routing did not show real value on this data; the saving is mostly the choice of one cheap, strong model.

K = 4 had the top pass rate, 70.2%, and beat Sonnet (+5.4 points, +1.4 to +9.4) at 66% lower cost. It beat DeepSeek only inside the noise, at 8 times the cost.

## 6. Gateway
Overhead p50 23 ms, p95 72 ms (real embedder, this Mac). Outages: 0 failed requests in tests and replay. Checks cost +43% on validation replay with no quality gain, though replay repair is pessimistic. Cache: no threshold met the target; θ = 0.97 has 10.0% wrong hits (5.5% to 17.4%). Meaning hits are about 2.7% of eligible train prompts, an upper estimate. Replay shows 0 hits on sampled prompts, so cache savings are not demonstrated.

Live run, 50 validation messages per row: TakRouter p50 4.84 s, p90 10.60 s; Sonnet p50 8.88 s, p90 18.09 s (`results/final/live_latency.md`). Live latency was about twice the replay figures; the cause was not investigated.

## 7. Economics
Measured test cost per 1,000 messages: $0.69 vs $16.32 for Sonnet. At that gap, 1 million messages cost about $690 vs $16,320, before cache and retries, and at list prices without DeepSeek's peak doubling.

KHAYYAM_SECTION

## 8. Limitations
One judge with imperfect agreement. 299 test prompts. Four models and one aggregator, so a real provider outage was simulated. Almost no code in the data. Test and validation differ in Persian share. Cache quality and live cost at scale are unproven. The site was never viewed in a browser. Report figures in draw.io and MLflow screenshots from WP-20 are not done.

## 9. Next steps
Check K = 4 or a cheaper variant on fresh data, add a stronger model only where Ψ differs clearly, replace Jev's labels on a sample with human ones, and tighten the cache with a fit check instead of a threshold alone.
