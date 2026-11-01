"""S2: split by session (WP-02 step 7, spec S2).

Val and test are random prompts from **all** eligible prompts, each equally likely (DEV-11, D-074,
D-076; dates are not used), with at most `max_per_session` per session. A session belongs to one
split only: every other prompt of a val or test session leaves train. `balance` is optional: with a
field name the draw is stratified by it (a session takes the value of its first eligible prompt);
with None it is plain random. All other sessions go to train (unlabeled). Pilot ⊂ val; cal = each
pilot prompt paired with one non-anchor model, round-robin. Same seed + same input → identical ids.
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
    table: pd.DataFrame  # prompt_id, session_id, stratum, lang, split, in_pilot, cal_model
    info: dict[str, Any] = field(default_factory=dict)


def _largest_remainder(shares: pd.Series, n: int) -> dict[str, int]:
    raw = shares / shares.sum() * n
    base = np.floor(raw).astype(int)
    rest = n - int(base.sum())
    order = (raw - base).sort_values(ascending=False, kind="stable").index[:rest]
    base.loc[order] += 1
    return base.to_dict()


def _draw(
    elig: pd.DataFrame, n: int, cap: int, rng: np.random.Generator
) -> tuple[list[str], set[str], dict[str, int]]:
    """Draw `n` eligible prompts, each equally likely, at most `cap` from one session. Stratified by
    `stratum`. Returns prompt ids, used session ids and the shortfall per stratum (0 if met)."""
    sizes = elig.groupby("stratum").size()
    targets = _largest_remainder(sizes, n) if n and len(sizes) else {}
    chosen: list[str] = []
    per_session: dict[str, int] = {}
    leftovers: list[tuple[str, str, str]] = []

    def walk(rows: list[tuple[str, str, str]], want: int) -> int:
        got = 0
        for row in rows:
            pid, sid, _ = row
            if got == want or per_session.get(sid, 0) >= cap:
                leftovers.append(row)
                continue
            chosen.append(pid)
            per_session[sid] = per_session.get(sid, 0) + 1
            got += 1
        return got

    got: dict[str, int] = {}
    for c, group in elig.groupby("stratum"):
        rows = list(group[["prompt_id", "session_id", "stratum"]].itertuples(index=False, name=None))
        order = rng.permutation(len(rows))
        got[str(c)] = walk([rows[i] for i in order], targets.get(str(c), 0))
    # strata that ran short: fill from the rest (order stays random inside each stratum)
    short = n - len(chosen)
    if short > 0:
        rows, leftovers = leftovers, []
        order = rng.permutation(len(rows))
        before = {c: 0 for c in got}
        for i in order:
            if short <= 0 or per_session.get(rows[i][1], 0) >= cap:
                continue
            chosen.append(rows[i][0])
            per_session[rows[i][1]] = per_session.get(rows[i][1], 0) + 1
            before[rows[i][2]] += 1
            short -= 1
        got = {c: got[c] + before[c] for c in got}
    shortfall = {c: max(0, targets[c] - got.get(c, 0)) for c in targets}
    return chosen, set(per_session), shortfall


def make_splits(
    prompts: pd.DataFrame,
    n_val: int,
    n_test: int,
    n_pilot: int,
    max_per_session: int,
    cal_models: list[str],
    seed: int,
    balance: str | None = None,
) -> SplitResult:
    rng = np.random.default_rng(seed)
    df = prompts.sort_values("prompt_id").reset_index(drop=True)
    df["stratum"] = df[balance].astype(str) if balance else "all"
    elig = df[df["eligible_labeled"]]
    order = [c for c in ("session_id", "msg_index") if c in elig]
    first_elig = elig.sort_values(order, kind="stable").groupby("session_id")["stratum"].first()
    sess = df.groupby("session_id").agg(stratum=("stratum", "first"))
    sess["stratum"] = first_elig.reindex(sess.index).fillna(sess["stratum"])
    sess["capped"] = sess.index.map(elig["session_id"].value_counts()).fillna(0).astype(int)
    sess["capped"] = sess["capped"].clip(upper=max_per_session)
    draw = elig[["prompt_id", "session_id"]].assign(stratum=elig["session_id"].map(sess["stratum"]))

    val_ids, val_sess, val_short = _draw(draw, n_val, max_per_session, rng)
    rest = draw[~draw["session_id"].isin(val_sess)]
    test_ids, test_sess, test_short = _draw(rest, n_test, max_per_session, rng)

    labeled_sess = val_sess | test_sess
    split = pd.Series("none", index=df.index)
    split[df["prompt_id"].isin(val_ids)] = "val"
    split[df["prompt_id"].isin(test_ids)] = "test"
    split[~df["session_id"].isin(labeled_sess) & df["eligible_train"]] = "train"
    df["split"] = split

    # pilot ⊂ val, stratified; cal = round-robin over non-anchor models
    val = df[df["split"] == "val"]
    targets = _largest_remainder(val.groupby("stratum").size(), min(n_pilot, len(val)))
    pilot: list[str] = []
    for c, t in sorted(targets.items()):
        ids = sorted(val.loc[val["stratum"] == c, "prompt_id"])
        pilot.extend(rng.choice(ids, size=t, replace=False).tolist())
    pilot_order = [str(x) for x in rng.permutation(sorted(pilot))]
    cal = {pid: cal_models[i % len(cal_models)] for i, pid in enumerate(pilot_order)}
    df["in_pilot"] = df["prompt_id"].isin(pilot)
    df["cal_model"] = df["prompt_id"].map(cal)

    table = df[["prompt_id", "session_id", "stratum", "lang", "split", "in_pilot", "cal_model"]]
    info = {
        "seed": seed,
        "balance_field": balance,
        "sizes_requested": {"val": n_val, "test": n_test, "pilot": n_pilot},
        "sessions_total": len(sess),
        "capacity": int(sess["capped"].sum()),
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
        t.groupby(["split", "stratum", "lang"]).size().rename("n").reset_index().to_dict("records")
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
        "counts_split_stratum_lang": counts,
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
