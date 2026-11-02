# WP-12 report: generation

Date 2026-11-02. Cost $11.88 of the $14 approved. Tables: `results/s6_stats.md` (val), `results/s6_stats_test.md` (test, no quality).

Outcome: 1,600 val and 1,200 test slots, 2,799 answers. Pilot answers reused. Rerun leaves 0 new calls on test, and only the one failed Sonnet val call on val (3 tries, error 500).

| Set | New calls in ledger | Failed answers | Left cut off | Cost |
|---|---:|---:|---:|---:|
| Val | 1,234 | 1 of 1,600 | 0 | $5.76 |
| Test | 1,253 | 0 of 1,200 | 3 | $6.12 |

Test cost ran 4% over the $5.90 estimate: Sonnet mean input 5,231 tokens and output 462, against 5,046 and 443 on val. One luna test answer ended on `content_filter` and counts as ok, so WP-13 judges it as it is.

Returned versions match the requested names, except deepseek-v4-flash returns `deepseek-flash` on every call. Reasoning tokens stay unreported for Sonnet, DeepSeek and Gemini.

Changes: account stop and resume (D-110), measured Sonnet estimate (D-111), sealed test selection, with `.sealed` output names. S7 refuses the test set until WP-13 opens it. Nobody read test text or computed test quality.
