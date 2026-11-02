# Dry run report (WP-07)

**MOCK.** Sample only, mock LLM, mock grades: every quality number here is made up and says nothing about the models. Only the plumbing is tested. Measured: stage durations, counts, hashes.

K values: (1, 3, 4) (explicit: `candidate_ks` is empty for 60 prompts). Mock tau = 7.

## Stages (first run)

| Stage | Counts | Seconds | $ | Second run identical |
|---|---|---:|---:|---|
| s1 | `{"prompts": 434, "labeled": 343, "train": 371}` | 1.3 | 0 | yes |
| s2 | `{"none": 278, "val": 60, "train": 56, "pilot": 20, "test": 40}` | 0.4 | 0 | yes |
| s4 | `{"train": 56, "val": 60, "test": 40}` | 12.2 | 0 | yes |
| s5 | `{"k1_val_counts": [60], "k3_val_counts": [0, 0, 60], "k4_val_counts": [0, 0, 43, 17]}` | 0.3 | 0 | yes |
| s6 | `{"new_calls": 420, "records": 500}` | 33.0 | 0 | yes |
| s7 | `{"mock_scores": 400, "new_calls": 1320, "records": 1520}` | 36.3 | 0 | yes |
| s8 | `{"bt_vs_closed_form_k1": 2.4189650282835373e-11, "bt_vs_closed_form_k3": 2.4189650282835373e-11, "bt_vs_closed` | 0.0 | 0 | yes |
| s9 | `{"pt": 3, "pw": 3}` | 0.0 | 0 | yes |
| s10 | `{"pt": 0.10811807510766078, "pw": 0.13141473626117553}` | 0.0 | 0 | yes |
| s11 | `{"pt": 0.8196318507363343, "pw": 0.4273458914446068}` | 0.3 | 0 | yes |
| s12 | `{"point": {"k": 3, "routed_one_prompt_to_a_model": true}, "pair": {"k": 3, "routed_one_prompt_to_a_model": tru` | 0.0 | 0 | yes |

Second run: new mock calls S6 = 0, S7 = 0.

## Leak test

All 343 eligible sample prompts, 4 models, both judges. The stored prompts hold no key patterns, so 13720 fake key values were planted in the message, instructions, RAG context and history. Requests scanned: 4802. Secret hits: 0.

## Mock fingerprints (MOCK)

pt, K* = 3 (MOCK)

| cluster | n | gemini-2.5-flash-lite | deepseek-v4-flash | gpt-5.6-luna | claude-sonnet-5-5 |
|---|---:|---:|---:|---:|---:|
| 0 | 0 | 0.80 | 0.20 | 0.68 | 0.10 |
| 1 | 0 | 0.80 | 0.20 | 0.68 | 0.10 |
| 2 | 60 | 0.80 | 0.20 | 0.68 | 0.10 |

pw, K* = 3 (MOCK)

| cluster | n | gemini-2.5-flash-lite | deepseek-v4-flash | gpt-5.6-luna | claude-sonnet-5-5 |
|---|---:|---:|---:|---:|---:|
| 0 | 0 | 0.92 | 0.62 | 0.89 | 0.50 |
| 1 | 0 | 0.92 | 0.62 | 0.89 | 0.50 |
| 2 | 60 | 0.90 | 0.62 | 0.88 | 0.50 |

## Mock deferral curves (MOCK)

Test n = 40, val n = 60.

| method | router | area |
|---|---|---:|
| pt | always_best | 0.000 |
| pt | always_cheapest | 0.300 |
| pt | knn | 0.842 |
| pt | logistic | 0.820 |
| pt | uniroute | 0.820 |
| pt | zerorouter | 0.820 |
| pw | always_best | 0.000 |
| pw | always_cheapest | 0.100 |
| pw | knn | 0.423 |
| pw | uniroute | 0.427 |
| pw | zerorouter | 0.427 |

pt: UniRoute minus ZeroRouter 0.000, 95% CI -0.000 to 0.000 (session bootstrap, n_boot = 200, MOCK).

| cost | 1.00 | 1.00 | 1.00 | 0.06 | 0.06 | 0.04 |
|---|---:|---:|---:|---:|---:|---:|
| quality | 0.85 | 0.85 | 0.85 | 0.80 | 0.80 | 0.30 |

pw: UniRoute minus ZeroRouter 0.000, 95% CI -0.000 to 0.000 (session bootstrap, n_boot = 200, MOCK).

| cost | 1.00 | 1.00 | 1.00 | 0.06 | 0.06 | 0.04 |
|---|---:|---:|---:|---:|---:|---:|
| quality | 0.50 | 0.50 | 0.50 | 0.36 | 0.36 | 0.10 |

## Artifacts

`runs/dry/s12/artifact_point`, `runs/dry/s12/artifact_pair` (git-ignored)

## Spec section 10 checklist

| Item | Status | Note |
|---|---|---|
| No prompt or conversation in two splits | ✓ | sessions compared on the sample |
| Every val cluster has at least n_min prompts; clusters nameable | – | real clusters: WP-08, WP-14 |
| Pilot decision recorded | n.a. | WP-11 |
| Judge-human agreement gate passed | n.a. | WP-11 |
| Pointwise: tau chosen on S_cal; alpha 0 reproduces Eq. 12 | – | Eq. 12 in tests; tau is a mock value here |
| Pairwise: closed form matches the BT fit; anchor row 0.5 | ✓ | largest gap 2.4e-11 |
| Test set not used for method, K, lambda, tau, rubric, thresholds | ✓ | S9 and S10 read val only; the mock test here is the sample's own draw |
| UniRoute area at least ZeroRouter's and K-NN's on test | n.a. | mock numbers mean nothing (holds here: False); real check in WP-19 |
| Adding a mock new model touches only its row and lambda | ✓ | pointwise, K* |
| A rerun gets cache hits for every call | ✓ | second run |

## Not covered

- Qdrant: K-NN used an in-memory exact search. Real calls, prices and usage reporting wait for WP-09.
- S3 and S4 full-data runs are not repeated here. The holdout demo is WP-14.
- Val and test use most of the 100 sample sessions, so train has only 56 prompts; some K = 3 and
  K = 4 clusters are empty in val. Mock grades use K = 4. This exercises the empty-cluster path.
