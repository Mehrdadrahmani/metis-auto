# Lambda on validation

Measured, n = 798. Always-best = claude-sonnet-5-5, pass 66.2%, cost 1.000.
Quality mode target 64.2% (always-best minus 2 points, primary). Budget mode target cost 0.500.
In-sample is S10 on all validation. Unseen is out of fold, the fairer figure.

| K | Mode | λ | In-sample cost | In-sample pass | Unseen cost | Unseen pass | Unseen shares |
|---:|---|---:|---:|---:|---:|---:|---|
| 8 | quality | 5.356 | 0.037 | 64.8% | 0.036 | 63.7% | deepseek 72%, gpt 0%, gemini 28%, claude 0% |
| 8 | budget | 0 | 0.486 | 67.3% | 0.534 | 64.6% | deepseek 47%, gpt 1%, gemini 0%, claude 51% |
| 4 | quality | 4.406 | 0.038 | 64.8% | 0.036 | 63.0% | deepseek 69%, gpt 0%, gemini 31%, claude 0% |
| 4 | budget | 0.007038 | 0.417 | 67.5% | 0.529 | 66.1% | deepseek 47%, gpt 2%, gemini 0%, claude 51% |
