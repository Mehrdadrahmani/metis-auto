# UniRoute on Khayyam (D-124)

Measured with true answers, no judge, n = 1,100 test questions; K and λ chosen on 400 validation questions; clusters from 12,000 other questions. No Sonnet, per the owner's plan. Spent $0.47. Khayyam's licence is academic only, so no question text is stored here.

| Router | Test accuracy | Cost (ĉ) | Answers cut at 300 tokens |
|---|---:|---:|---:|
| gemini-2.5-flash-lite | 46.2% | 0.252 | 15.5% |
| deepseek-v4-flash | 56.2% | 0.573 | 16.4% |
| gpt-5.6-luna | 56.2% | 0.257 | 0.0% |
| deepseek-v4-pro | 54.4% | 1.000 | 2.7% |
| UniRoute K = 7, λ = 21 | 55.0% | 0.256 | |

Area: UniRoute 0.5819, ZeroRouter 0.5615, gain +0.0204 (95% CI +0.0015 to +0.0444, 500 draws, questions treated as independent).
Against the best single model on validation (gpt-5.6-luna): -1.2 points (95% CI -2.6 to +0.3).

A cut answer counts as wrong, which hurts Gemini and DeepSeek flash, so model comparisons here partly measure how briefly a model answers. The prompt asked for the option number only. Parsing takes the last named option. The first 20 Gemini calls came from an earlier limit of 64 tokens and were replaced; two runs stopped before scoring.

Reading: on true labels, clustering gave a small real gain on the cost-quality curve, which the judge-labeled data did not show. At the chosen λ it did not beat the best single model.
