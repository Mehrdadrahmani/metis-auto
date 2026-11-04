# Frozen lambda (D-118, DEV-16)

Measured on validation, out of fold, n = 798. Target: always-DeepSeek pass 65.4%.

| K | λ | Unseen cost | Unseen pass | Target met | Shares (DeepSeek, Luna, Gemini, Sonnet) |
|---:|---:|---:|---:|---|---|
| 8 | 0.5151 | 0.042 | 65.4% | yes | 89%, 10%, 1%, 0% |
| 4 | 0.04954 | 0.333 | 65.6% | yes | 66%, 4%, 0%, 30% |
