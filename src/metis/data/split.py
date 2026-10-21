"""S2: split by session (WP-02 step 7, spec S2).

Sessions are sorted by `created_at`; the most recent ones form the **recent pool** (≈ factor × the
labeled prompts needed). Val and test are drawn from it by sampling sessions **stratified by
category**, with at most `max_per_session` eligible prompts per session. All other sessions go to
train (unlabeled). Pilot ⊂ val (stratified); cal = each pilot prompt paired with one non-anchor
model, round-robin. Same seed + same input → identical ids.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SPLITS = ("train", "val", "test", "none")


@dataclass
class SplitResult:
    table: pd.DataFrame  # prompt_id, session_id, category, lang, split, in_pilot, cal_model
    info: dict[str, Any] = field(default_factory=dict)


def _largest_remainder(shares: pd.Series, n: int) -> dict[str, int]:
    raw = shares / shares.sum() * n
    base = np.floor(raw).astype(int)
    rest = n - int(base.sum())
    order = (raw - base).sort_values(ascending=False, kind="stable").index[:rest]
    base.loc[order] += 1
    return base.to_dict()


def _draw(
    sessions: pd.DataFrame,
    elig_by_session: dict[str, list[str]],
    n: int,
    cap: int,
    rng: np.random.Generator,
) -> tuple[list[str], set[str], dict[str, int]]:
    """Draw `n` eligible prompts from `sessions`, stratified by category. Returns prompt ids,
    used session ids and the shortfall per category (0 if met)."""
    capacity = sessions.groupby("category")["capped"].sum()
    capacity = capacity[capacity > 0]
    targets = _largest_remainder(capacity, n) if n and len(capacity) else {}
    queues = {
        c: [str(x) for x in rng.permutation(sorted(g.index[g["capped"] > 0]))]
        for c, g in sessions.groupby("category")
    }
    chosen: list[str] = []
    used: set[str] = set()
    got = {c: 0 for c in targets}

    def take(c: str, want: int) -> int:
        sid = queues[c].pop(0)
        ids = sorted(elig_by_session[sid])
        k = min(cap, len(ids), want)
        chosen.extend(rng.choice(ids, size=k, replace=False).tolist())
        used.add(sid)
        return k

    for c, t in targets.items():
        while got[c] < t and queues.get(c):
            got[c] += take(c, t - got[c])
    # categories that ran short: fill from the others, round-robin
    short = n - len(chosen)
    while short > 0 and any(queues.values()):
        for c in sorted(queues):
            if short > 0 and queues[c]:
                k = take(c, short)
                got[c] = got.get(c, 0) + k
                short -= k
    shortfall = {c: max(0, targets[c] - got.get(c, 0)) for c in targets}
    return chosen, used, shortfall


def make_splits(
    prompts: pd.DataFrame,
    n_val: int,
    n_test: int,
    n_pilot: int,
    pool_factor: float,
    max_per_session: int,
    cal_models: list[str],
    seed: int,
) -> SplitResult:
    rng = np.random.default_rng(seed)
    df = prompts.sort_values("prompt_id").reset_index(drop=True)
    elig = df[df["eligible_labeled"]]
    elig_by_session = elig.groupby("session_id")["prompt_id"].apply(list).to_dict()
    sess = (
        df.groupby("session_id")
        .agg(created=("session_created_at", "first"), category=("category", "first"))
        .assign(n_elig=lambda s: s.index.map(lambda i: len(elig_by_session.get(i, []))))
    )
    sess["capped"] = sess["n_elig"].clip(upper=max_per_session)
    # newest first; ties broken by session id
    sess = sess.loc[sorted(sess.index, key=lambda i: (str(sess.at[i, "created"]), i), reverse=True)]

    need = pool_factor * (n_val + n_test)
    cum = sess["capped"].cumsum()
    n_pool = int((cum < need).sum()) + 1 if cum.iloc[-1] >= need else len(sess)
    pool = sess.iloc[:n_pool]

    val_ids, val_sess, val_short = _draw(pool, elig_by_session, n_val, max_per_session, rng)
    rest = pool.drop(index=list(val_sess))
    test_ids, test_sess, test_short = _draw(rest, elig_by_session, n_test, max_per_session, rng)

    labeled_sess = val_sess | test_sess
    split = pd.Series("none", index=df.index)
    split[df["prompt_id"].isin(val_ids)] = "val"
    split[df["prompt_id"].isin(test_ids)] = "test"
    split[~df["session_id"].isin(labeled_sess) & df["eligible_train"]] = "train"
    df["split"] = split

    # pilot ⊂ val, stratified by category; cal = round-robin over non-anchor models
    val = df[df["split"] == "val"]
    targets = _largest_remainder(val.groupby("category").size(), min(n_pilot, len(val)))
    pilot: list[str] = []
    for c, t in sorted(targets.items()):
        ids = sorted(val.loc[val["category"] == c, "prompt_id"])
        pilot.extend(rng.choice(ids, size=t, replace=False).tolist())
    pilot_order = [str(x) for x in rng.permutation(sorted(pilot))]
    cal = {pid: cal_models[i % len(cal_models)] for i, pid in enumerate(pilot_order)}
    df["in_pilot"] = df["prompt_id"].isin(pilot)
    df["cal_model"] = df["prompt_id"].map(cal)

    table = df[["prompt_id", "session_id", "category", "lang", "split", "in_pilot", "cal_model"]]
    info = {
        "seed": seed,
        "sizes_requested": {"val": n_val, "test": n_test, "pilot": n_pilot},
        "sessions_total": len(sess),
        "pool_sessions": n_pool,
        "pool_capacity": int(pool["capped"].sum()),
        "pool_oldest_created_at": str(pool["created"].min()),
        "val_sessions": len(val_sess),
        "test_sessions": len(test_sess),
        "shortfall": {"val": val_short, "test": test_short},
    }
    return SplitResult(table=table, info=info)


def ids_sha256(ids) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def split_manifest(res: SplitResult, config_ids: dict[str, str]) -> dict[str, Any]:
    t = res.table
    counts = (
        t.groupby(["split", "category", "lang"]).size().rename("n").reset_index().to_dict("records")
    )
    by_split = t["split"].value_counts().to_dict()
    cal = t.dropna(subset=["cal_model"])
    return {
        "stage": "s2_split",
        **res.info,
        "config_ids": config_ids,
        "counts_by_split": {s: int(by_split.get(s, 0)) for s in SPLITS},
        "pilot": int(t["in_pilot"].sum()),
        "cal_per_model": cal["cal_model"].value_counts().sort_index().to_dict(),
        "counts_split_category_lang": counts,
        "sha256": {
            **{
                s: ids_sha256(t.loc[t["split"] == s, "prompt_id"]) for s in ("train", "val", "test")
            },
            "pilot": ids_sha256(t.loc[t["in_pilot"], "prompt_id"]),
            "cal": ids_sha256(f"{p}:{m}" for p, m in zip(cal["prompt_id"], cal["cal_model"])),
        },
    }


def write_split(res: SplitResult, out_dir, manifest: dict[str, Any]) -> None:
    """`split.parquet` without test rows; test ids only in `test_ids.sealed` (WP-08 sealing)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    t = res.table
    t[t["split"] != "test"].to_parquet(out / "split.parquet", index=False)
    test_ids = sorted(t.loc[t["split"] == "test", "prompt_id"])
    (out / "test_ids.sealed").write_text(json.dumps(test_ids) + "\n", encoding="utf-8")
    (out / "split.manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
