# Holdout demo

Measured, n = 798, validation only. Gemini hidden, then added back from its validation row alone.
K is fixed per candidate, so this shows the add-a-model step, not a fresh K choice.

| K | Area without Gemini | Area with Gemini | Change | λ | Gemini share, unseen |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.6480 | 0.6522 | +0.0042 | 0.1 | 0.7% (in-sample 0.0%) |
| 4 | 0.6559 | 0.6634 | +0.0075 | 0.1 | 0.0% (in-sample 0.0%) |
