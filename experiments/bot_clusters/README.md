# Bot clusters (experiment)

Separate from the main pipeline: nothing here changes the split, the message clusters or the router.

Bots are embedded from redacted `description` + `instructions`, then K-means for K = 2..60; K by the
elbow rule. Local outputs with text: `runs/bot_clusters/` (git-ignored). Numbers: this folder.

    uv run python experiments/bot_clusters/run.py embed
    uv run python experiments/bot_clusters/run.py cluster
