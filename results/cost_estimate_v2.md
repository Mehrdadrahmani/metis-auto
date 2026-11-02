# Cost estimate v2 (measured from the pilot)

Simulated from measured cost per call, n = 100 pilot prompts. Sizes: val 400, test 300, pilot 100 reused. Assumes the pilot prompts are like the rest. No confidence interval yet.

| Item | Memo, mid | Measured basis | New estimate |
|---|---:|---|---:|
| Main generation, 4 models, 500 new prompts | $7.06 | $0.0194 per prompt, Sonnet $0.0175 | $9.70 |
| Main judging, terra pointwise, 2,000 new calls | $24.13 | $0.00665 per call | $13.30 |
| Main judging, jev pointwise, 2,000 new calls | about $0.40 | $0.00018 per call | $0.35 |
| Re-judge 5%, terra | $1.21 | same rate | $0.70 |

Generation is 37% above the memo; terra judging is 45% below it. Both differ by more than 25%: owner told at the end of WP-09.

Sonnet costs more than planned because its input is about 4,700 tokens against 2,800 for DeepSeek on the same prompts. Terra costs less because the judge input was far smaller than the memo assumed.

Rest of the pointwise path with terra: about $26 (with cache labels $1 and live run $1.50). With the spent pilot: about $32 of the $60 cap, before Gate 2 changes.
