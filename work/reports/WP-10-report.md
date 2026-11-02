# WP-10 report: labels by Claude Opus

Date 2026-11-02. Cost $0 in API calls. Owner had no time to label, so this replaced the plan (D-098, DEV-14).

Blind method: 10 fresh agents, 10 items each, answers named 1 and 2, re-shuffled. Agents had no access to the key, scores or logs. Labels: `runs/labeling/opus/opus_labels.parquet`, git-ignored, rater `claude-opus-5-5`.

Limits: not a human check; rater is in the same family as the anchor; 20 re-labels not done. Numbers: `report/NOTES.md`.
