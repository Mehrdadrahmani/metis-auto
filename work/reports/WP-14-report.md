# WP-14 report: fingerprints, K, λ, freeze

Validation only, n = 798 of 800 (2 refused, D-112). $0 in this WP's final part. Gate 3 approved through owner consent D-119; the owner did not read the protocol before the tag.

- **Fingerprints:** `results/fingerprints.md`. **K:** the D-064 rule gives K = 4 (area 0.6634); the owner shipped K = 8 (0.6522, D-117), below K = 1 (0.6545). Stated plainly so nobody reads K = 8 as the rule's winner.
- **λ (D-118, DEV-16):** K = 8 λ 0.5151: unseen cost 0.042, pass 65.4%, shares DeepSeek 89%, Luna 10%, Gemini 1%. K = 4 λ 0.04954: cost 0.333, pass 65.6%, DeepSeek 66%, Sonnet 30%. Sonnet at cost 1.000 passes 66.2%.
- **Ladder:** `results/ladder_val.md`. K-NN 0.6636, K = 4 0.6634, ZeroRouter 0.6545, logistic 0.6532. No router clearly beats DeepSeek at low cost.
- **Holdout:** adding Gemini from its validation row alone raised area by 0.0042 (K = 8) and 0.0075 (K = 4); one row touched, no code changed (`results/holdout_demo.md`).
- **Signals and inputs:** bot groups, RAG, language, length, T = 2 and hybrid did not beat DeepSeek at low cost (`results/signal_tests.md`, `results/representation_test.md`). D-078 not shipped; input stays the current message.
- **Sealed guard:** `metis.data.sealed.read_sealed_parquet`, tests in `tests/test_sealed.py`.
- **Artifacts:** `artifacts/router_v1/` (shipped), `artifacts/router_v1_k4/` (comparison). K = 4 cluster names are placeholders (D-088).
- **Protocol:** `results/eval_protocol.md`. Replay settings are fixed later in WP-18, on validation, before the test opens.
- WP-19 note: fixed λ and K only; replay config is the one commit-pinned at the end of WP-18.
