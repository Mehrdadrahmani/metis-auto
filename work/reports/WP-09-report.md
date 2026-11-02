# WP-09 report: pilot run

Date 2026-11-02. Cost $5.87 of $10. Tests 264 pass.

## Results
- All acceptance checks met: 500 answers, 499 + 500 pointwise, 800 pairwise (jev only, D-093). Terra dropped 1 item after two parse failures. Details: `results/pilot_run_stats.md`.
- Answers cut at 1,024: Sonnet 9, others 1 to 3. Redone at rising limits for all models; none cut now (D-095).
- Jev position consistency 0.755, under the 0.80 line, with a lean to position B. WP-11 decides.
- Measured costs: generation up 37%, terra judging down 45% (`results/cost_estimate_v2.md`).
- Labeling file: `runs/labeling/cal_2026-11-02.html`, 100 items. The 20-item re-label file is built from the owner's exported CSV, so it comes after labeling.

## Added beyond the WP
Noise check also covers Jev pointwise (owner: do not cut). 60 repeats in total.

## Open
Old Metis key still in use (D-096). Compare the ledger with the Metis invoice. `s6_generate.py` pre-check still counts cached work (D-097). Reasoning tokens are not reported for Sonnet, DeepSeek and Gemini.
