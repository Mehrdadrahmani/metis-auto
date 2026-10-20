# WP-10: Owner labels the calibration set (human work, no Claude session needed)

| Phase | Who | Time | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|
| 3 | **Mehrdad (owner)** | ~3 h (100 items) + ~30 min (20 re-labels, ≥ 2 days later) | $0 | WP-09 | WP-11 |

## Why this matters
The AI grader decides every fingerprint. Your 100 labels are the only check that it judges Persian
answers the way a demanding user would. The grader must agree with you on ≥ 75% (and κ ≥ 0.40) before
we pay for the main build (Gate 2). You are on the critical path: try to finish within one day of
WP-09.

## What to do
1. Open `metis-auto/runs/labeling/cal_<date>.html` in a browser (works offline).
2. Read the guideline box once. For each item:
   - **Acceptable?** "Would a demanding user accept this answer without asking again?" Yes/No.
     Judge for *this chatbot*: if its instructions say "only answer about our product", a good general
     answer that ignores that rule is **not** acceptable.
   - **Better?** Compare the two answers shown (left/right order is random): left / right / tie.
     Use tie when you'd honestly be equally happy.
   - Note (optional): one line if something is odd (e.g. "question unclear").
3. Don't look for which model wrote what (names are hidden; don't guess). Take a break every ~30 items.
4. When done, click **Export CSV** and save it as `metis-auto/runs/labeling/cal_labels.csv`.
5. Two or more days later, do the 20-item re-label file the same way → `relabel_labels.csv`.
6. Start a session and type `/start` (the next WP is WP-11).

## If something is wrong
- Items that are broken (empty answer, garbled text): label "No" and write a note.
- If an item contains something that looks like a password or key: note it; don't copy it anywhere.
