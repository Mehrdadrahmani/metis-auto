# Representation test on validation

Measured, held out, n = 798, 40 halves. 79% of prompts have a previous message; short means 20 chars or fewer.
Same centroids throughout. Cheap gap: pass rate minus always-DeepSeek at λ = 0.1.

| Input | K | Area | Cheap gap | Prompts moved to another cluster |
|---|---:|---:|---:|---:|
| A current message | 8 | 0.6522 | -1.1% | 0% |
| A current message | 4 | 0.6634 | -0.8% | 0% |
| T = 2 | 8 | 0.6493 | -1.1% | 28% |
| T = 2 | 4 | 0.6651 | -0.2% | 21% |
| Hybrid | 8 | 0.6562 | -1.1% | 11% |
| Hybrid | 4 | 0.6672 | -0.5% | 9% |
