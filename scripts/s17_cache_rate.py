"""WP-17: real cache hit rate, sequential over train traffic under the policy. Free, no model calls."""

from __future__ import annotations

import numpy as np
import pandas as pd
from s17_cache_pairs import train_vectors

from metis.gateway.cache_policy import is_cacheable

cols = ["prompt_id", "msg_index", "bot_id", "system_prompt_id", "lang", "timestamp", "text_norm", "match_key", "eligible_train", "dup_exact_train", "dup_exact", "uses_rag", "has_image"]
df = pd.read_parquet("runs/s1/prompts.parquet", columns=cols)
split = pd.read_parquet("runs/s2/split.parquet", columns=["prompt_id", "split"])
df = df.merge(split[split["split"] == "train"], on="prompt_id")
df = df[df.eligible_train | df.dup_exact_train.fillna(False) | df.dup_exact.fillna(False)].sort_values("timestamp")  # repeats were removed for labels, not for traffic
total = len(df)
ok = np.array([not u and not h and is_cacheable(t or "", m <= 1)[0] for u, h, t, m in zip(df.uses_rag, df.has_image, df.text_norm, df.msg_index, strict=True)])
df = df[ok]
exact = df.duplicated(["bot_id", "system_prompt_id", "lang", "match_key"]).to_numpy()
uniq = df[~exact]
ids, vecs = train_vectors(set(uniq.prompt_id))
pos = pd.Series(np.arange(len(ids)), index=ids)
uniq = uniq[uniq.prompt_id.isin(pos.index)]
semantic = 0
checked = 0
for _, g in uniq.groupby(["bot_id", "system_prompt_id", "lang"], dropna=False):
    if len(g) < 2:
        checked += len(g)
        continue
    g = g.iloc[:6000]
    m = vecs[pos[g.prompt_id].to_numpy()]
    m = m / np.linalg.norm(m, axis=1, keepdims=True)
    sims = np.tril(m @ m.T, -1).max(1)
    semantic += int((sims >= 0.97).sum())
    checked += len(g)
rate = semantic / checked
lines = ["", "## Hit rate on real traffic", "",
         f"Measured sequentially on {total} eligible train prompts, no TTL applied, so an upper estimate.",
         f"Allowed by the policy: {len(df)} ({len(df) / total:.1%}). Exact repeats: {exact.sum()} ({exact.sum() / total:.1%} of all). Meaning hits at 0.97: about {rate:.1%} of the {checked} unique cacheable prompts checked, {rate * len(uniq) / total:.1%} of all.",
         "Validation replay shows 0 hits because 800 sampled prompts rarely repeat each other, so it cannot show this rate."]
with open("results/cache_threshold.md", "a", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
