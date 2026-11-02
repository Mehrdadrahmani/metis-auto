"""WP-17: does the text-matching adapter separate wrong hits better than routing vectors? Free."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from metis.config import load_config
from metis.embed.embedder import Embedder
from metis.eval.stats import wilson_ci

s = pd.read_parquet("runs/cache_pairs/scored.parquet")
text = pd.read_parquet("runs/s1/prompts.parquet", columns=["prompt_id", "text_norm"]).set_index("prompt_id").text_norm
c = load_config("pipeline")["s4"]
cand = c["candidates"][c["choice"]]
e = Embedder(cand["name"], cand["revision"], device="cpu", path=cand["path"], task=c["cache_task"], prompt_name=c["prompt_name"], merge_adapter=True, max_tokens=c["max_tokens"], batch_size=16, max_batch_tokens=8192)
ids = sorted(set(s.saved) | set(s.new))
vec = e.encode([text[i] for i in ids])
vec = vec / np.linalg.norm(vec, axis=1, keepdims=True)
pos = {p: i for i, p in enumerate(ids)}
s["cos_tm"] = (vec[[pos[p] for p in s.saved]] * vec[[pos[p] for p in s.new]]).sum(1)
s.to_parquet("runs/cache_pairs/scored_tm.parquet", index=False)
a, b = roc_auc_score(~s.wrong, s.cos), roc_auc_score(~s.wrong, s.cos_tm)
lines = ["", "## Second check: text-matching vectors", "", f"Measured, n = {len(s)}. AUC for telling good hits from wrong hits: routing vectors {a:.3f}, text-matching {b:.3f}.", "",
         "| Text-matching θ | Pairs | Wrong | Rate | 95% Wilson |", "|---:|---:|---:|---:|---|"]
for t in (0.99, 0.98, 0.97, 0.95, 0.93, 0.90, 0.85):
    p = s[s.cos_tm >= t]
    if len(p):
        w = int(p.wrong.sum())
        lo, hi = wilson_ci(w, len(p))
        lines.append(f"| {t:.2f} | {len(p)} | {w} | {w / len(p):.1%} | {lo:.1%} to {hi:.1%} |")
own_pass = (s.score_own >= 7).mean()
lines += ["", f"The new message's own production answer passes {own_pass:.1%} of the time, and saved answers {(s.score_saved >= 7).mean():.1%}. Repeat-judging noise also creates some wrong hits."]
with open("results/cache_threshold.md", "a", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
