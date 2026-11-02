# WP-11 report: pilot decision

Date 2026-11-02. Cost $0. Tables: `results/pilot_decision.md`, script `scripts/pilot_decision.py`.

Outcome: pointwise jev with history, τ = 7. Gate 2 failed by one item (0.74 against 0.75, n = 100, κ 0.431). Owner went ahead with a weaker gate on record and declined the rubric revision (D-105). Terra stays out (D-106). Sonnet stays, no Qwen (D-107).

Length bias |ρ| 0.008, so no length analysis added to WP-19. Self-preference not visible for gpt-5.6-luna, no flag. Gemini is over-passed (8 over, 3 under, n = 33).

Limits: labels are Opus, not human; the 20 re-labels were not done; separability 0.111 at K = 3; the wrong-prompt check was not run. The choice is in `configs/judge_choice.yaml` because editing `judge_config.yaml` would change the config id.

Still to decide: validation size (D-091).
