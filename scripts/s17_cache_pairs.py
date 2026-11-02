"""WP-17 step 4: label near-duplicate pairs from TRAIN and pick theta. Stage cache_labels, about $0.2.

Judge question, pointwise jev: is the saved answer of an earlier message good for the new message?
Wrong hit = the saved answer fails (score < 7) while the new message's own answer passes.
Aggregates only in results/cache_threshold.md. Usage: uv run python scripts/s17_cache_pairs.py [--dry]
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd

from metis.eval.stats import wilson_ci
from metis.gateway.cache_policy import is_cacheable
from metis.judge import pointwise, render
from metis.judge.common import JudgeRun
from metis.llm import stage as st
from metis.llm.budget import Budget
from metis.llm.callcache import CallCache
from metis.llm.runner import run_batch

SEED = 20261020
BINS = [0.80, 0.85, 0.90, 0.93, 0.95, 0.97, 0.99]
PER_BIN = 50
MAX_GROUP = 6000
OUT = Path("runs/cache_pairs")


def train_vectors(ids: set[str]) -> tuple[np.ndarray, np.ndarray]:
    names, vecs = [], []
    for part in sorted(glob.glob("runs/s4/full/nano/part-*.npz")):
        with np.load(part) as z:
            keep = np.isin(z["ids"], list(ids))
            names.append(z["ids"][keep])
            vecs.append(z["vecs"][keep].astype(np.float32))
    return np.concatenate(names), np.concatenate(vecs)


def build_pairs() -> pd.DataFrame:
    cols = ["prompt_id", "session_id", "msg_index", "bot_id", "system_prompt_id", "lang", "timestamp", "text_norm", "match_key", "eligible_train", "uses_rag", "has_image"]
    df = pd.read_parquet("runs/s1/prompts.parquet", columns=cols)
    split = pd.read_parquet("runs/s2/split.parquet", columns=["prompt_id", "split"])
    df = df.merge(split[split["split"] == "train"], on="prompt_id")
    df = df[df.eligible_train & ~df.uses_rag & ~df.has_image & (df.msg_index <= 1)]
    df = df[[is_cacheable(t or "", True)[0] for t in df.text_norm]].drop_duplicates("match_key")
    print("cacheable train prompts", len(df))
    ids, vecs = train_vectors(set(df.prompt_id))
    pos = pd.Series(np.arange(len(ids)), index=ids)
    df = df[df.prompt_id.isin(pos.index)].sort_values("timestamp")
    pairs = []
    rng = np.random.default_rng(SEED)
    for _, g in df.groupby(["bot_id", "system_prompt_id", "lang"], dropna=False):
        if len(g) < 2:
            continue
        if len(g) > MAX_GROUP:
            g = g.iloc[np.sort(rng.choice(len(g), MAX_GROUP, replace=False))]
        m = vecs[pos[g.prompt_id].to_numpy()]
        m = m / np.linalg.norm(m, axis=1, keepdims=True)
        sims = np.tril(m @ m.T, -1)  # only earlier messages
        best, top = sims.argmax(1), sims.max(1)
        sessions = g.session_id.to_numpy()
        names = g.prompt_id.to_numpy()
        for i in np.flatnonzero(top >= BINS[0]):
            if sessions[i] != sessions[best[i]]:
                pairs.append((names[best[i]], names[i], float(top[i])))
    pairs = pd.DataFrame(pairs, columns=["saved", "new", "cos"])
    pairs["bin"] = pd.cut(pairs.cos, [*BINS, 1.0001], right=False, labels=False)
    print("candidates per bin", pairs.bin.value_counts().sort_index().to_dict())
    return pd.concat(g.sample(min(PER_BIN, len(g)), random_state=SEED) for _, g in pairs.groupby("bin"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "pairs.parquet"
    pairs = pd.read_parquet(path) if path.exists() else build_pairs()
    pairs.to_parquet(path, index=False)
    ids = sorted(set(pairs.saved) | set(pairs.new))
    prod = pd.concat(pd.read_parquet(p, columns=["prompt_id", "prod_answer"], filters=[("prompt_id", "in", ids)]) for p in sorted(glob.glob("runs/s1/context/part-*.parquet")))
    prod = prod.set_index("prompt_id").prod_answer
    pairs = pairs[pairs.saved.isin(prod.index) & pairs.new.isin(prod.index)]
    pairs = pairs[pairs.saved.map(prod).notna() & pairs.new.map(prod).notna()]
    print("usable pairs", len(pairs), "calls", 2 * len(pairs))
    if args.dry:
        return
    rows = st.load_rows(Path("runs/s1/prompts.parquet"), sorted(set(pairs.new)))
    cache, cfg = CallCache(), render.judge_config()
    budget = Budget(cache)
    run = JudgeRun(cache, budget, "cache_labels", "jev", cfg, 0.0006)
    items = [(r.new, r.saved, side) for r in pairs.itertuples() for side in ("saved", "own")]
    found = []

    def one(item):
        new, saved, side = item
        answer = prod[saved] if side == "saved" else prod[new]
        result, record = pointwise.judge(run, rows[new], f"cache-{side}", answer)
        found.append({"new": new, "saved": saved, "side": side, "score": record.get("score"), "status": record["status"]})
        return result

    report = run_batch("cache_labels", items, one, budget.config["anomalies"], 4, est_cost_per_call=0.0006, params={})
    print("cost", report.cost_usd, "stopped", report.stopped_reason)
    labels = pd.DataFrame(found)
    labels.to_parquet(OUT / "labels.parquet", index=False)
    ok = labels[labels.status == "ok"]
    wide = ok.pivot_table(index=["new", "saved"], columns="side", values="score").dropna()
    wide = wide.rename(columns={"saved": "score_saved", "own": "score_own"}).reset_index().merge(pairs, on=["new", "saved"])
    wide["wrong"] = (wide.score_saved < 7) & (wide.score_own >= 7)
    wide.to_parquet(OUT / "scored.parquet", index=False)
    write(wide)


def write(wide: pd.DataFrame) -> None:
    lines = ["# Cache threshold (WP-17, D-121)", "",
             f"Measured on train pairs, n = {len(wide)}, jev pointwise, pass mark 7, routing vectors (nano, clustering).",
             "Wrong hit: the saved answer fails for the new message while that message's own production answer passes.", "",
             "| θ | Pairs at or above | Wrong hits | Rate | 95% Wilson |", "|---:|---:|---:|---:|---|"]
    chosen = None
    for theta in reversed(BINS):
        part = wide[wide.cos >= theta]
        w, n = int(part.wrong.sum()), len(part)
        if not n:
            continue
        low, high = wilson_ci(w, n)
        lines.append(f"| {theta:.2f} | {n} | {w} | {w / n:.1%} | {low:.1%} to {high:.1%} |")
        if high <= 0.05 and w / n <= 0.02:
            chosen = theta
    final = chosen if chosen is not None else 0.97
    note = "the lowest θ meeting both limits" if chosen is not None else "no θ met both limits, so the fallback 0.97 applies and the wrong-hit bound above stands"
    lines += ["", f"Chosen θ = {final:.2f}: {note}. Pairs in one bin are sampled evenly, so rows at or above θ are not traffic-weighted."]
    Path("results/cache_threshold.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
