"""S4: embed all eligible prompts with the chosen model, load Qdrant (WP-08).

Usage: uv run python scripts/s4_embed_full.py embed      (resumable, safe to kill)
       uv run python scripts/s4_embed_full.py embed --device cpu   (longest messages: GPU runs out)
       uv run python scripts/s4_embed_full.py set-split  (Qdrant split payload only, no embedding)

The sealed test ids are never opened: prompts are chosen by eligibility flags. Rows in
split.parquet get their split as payload; every other prompt is stored as `unassigned`.
Chunks run shortest text first, so the rare very long messages come last.
Writes runs/s4/full/<model>/part-*.npz, results/wp08_full_data/embed_full.json.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from qdrant_client import models

from metis.config import config_id, load_config
from metis.embed.embedder import Embedder
from metis.embed.store import DEFAULT_URL, VectorStore

ROOT = Path(__file__).resolve().parents[1]
CHUNK = 2000


def load_table() -> pd.DataFrame:
    cols = ["prompt_id", "bot_id", "lang", "uses_rag", "text_chars", "embed_input",
            "eligible_labeled", "eligible_train"]  # fmt: skip
    df = pd.read_parquet(ROOT / "runs/s1/prompts.parquet", columns=cols)
    df = df[df["eligible_labeled"] | df["eligible_train"]]
    split = pd.read_parquet(ROOT / "runs/s2/split.parquet", columns=["prompt_id", "split"])
    df = df.merge(split, on="prompt_id", how="left")
    df["split"] = df["split"].fillna("unassigned").replace({"none": "unassigned"})
    df["n"] = df["embed_input"].str.len()
    return df.sort_values(["n", "prompt_id"], ignore_index=True)


def embedder(cfg: dict, device: str | None = None) -> Embedder:
    s4 = cfg["s4"]
    cand = s4["candidates"][s4["choice"]]
    return Embedder(cand["name"], cand["revision"], device=device or s4["device"], path=str(ROOT / cand["path"]),
                    task=s4["task"], prompt_name=s4["prompt_name"],
                    merge_adapter=s4["merge_adapter"], max_tokens=s4["max_tokens"],
                    batch_size=s4["batch_size"], max_batch_tokens=s4["max_batch_tokens"])  # fmt: skip


def run_embed(cfg: dict, out: Path, device: str | None = None) -> None:
    t0 = time.perf_counter()
    df = load_table()
    emb = embedder(cfg, device)
    dim = None
    store = None
    n_new = 0
    for part, start in enumerate(range(0, len(df), CHUNK)):
        path = out / f"part-{part:05d}.npz"
        g = df.iloc[start : start + CHUNK]
        if path.exists():
            continue
        vecs = emb.encode(g["embed_input"].tolist())
        dim = dim or vecs.shape[1]
        store = store or VectorStore(emb.embedder_id, dim, url=DEFAULT_URL)
        payloads = [
            {"split": s, "lang": x, "uses_rag": bool(r), "bot_id": b}
            for s, x, r, b in zip(g["split"], g["lang"], g["uses_rag"], g["bot_id"], strict=True)
        ]
        store.upsert(g["prompt_id"].tolist(), vecs, payloads)
        tmp = path.with_suffix(".tmp.npz")
        np.savez(tmp, ids=g["prompt_id"].to_numpy(str), vecs=vecs)
        tmp.rename(path)  # a chunk counts only once it is complete
        n_new += len(g)
        if part % 10 == 0 and emb.device == "mps":
            torch.mps.empty_cache()
        mins = (time.perf_counter() - t0) / 60
        print(f"{start + len(g):,} / {len(df):,}  max chars {g['n'].max():,}  {mins:.1f} min", flush=True)
    if store is None:
        store = VectorStore(emb.embedder_id, emb.encode(["x"]).shape[1], url=DEFAULT_URL)
    manifest = {
        "stage": "s4_embed_full", "embedder_id": emb.embedder_id, "seed": cfg["seed"],
        "config_id": config_id(cfg["s4"]), "prompts": len(df), "embedded_this_run": n_new,
        "qdrant_points": store.count(), "by_split": df["split"].value_counts().to_dict(),
        "duration_s": round(time.perf_counter() - t0, 1), "cost_usd": 0.0,
    }  # fmt: skip
    store.close()
    res = ROOT / "results/wp08_full_data/embed_full.json"
    res.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(manifest))


def run_set_split(cfg: dict) -> None:
    """Rewrite the split payload after a new S2. Test is inside `unassigned`, so it stays unmarked."""
    df = load_table()
    cand = cfg["s4"]["candidates"][cfg["s4"]["choice"]]
    res = ROOT / "results/wp08_full_data/embed_full.json"
    manifest = json.loads(res.read_text(encoding="utf-8"))
    dim = np.load(next((ROOT / "runs/s4/full" / cfg["s4"]["choice"]).glob("part-*.npz")))["vecs"].shape[1]
    store = VectorStore(manifest["embedder_id"], dim, url=DEFAULT_URL)
    assert store.count() == len(df), "Qdrant and the prompt table differ"
    for name, ids in df.groupby("split")["prompt_id"]:
        store.set_payload(ids.tolist(), {"split": name})
        print(name, len(ids), flush=True)
    counts = {s: store.client.count(store.name, exact=True, count_filter=models.Filter(must=[
        models.FieldCondition(key="split", match=models.MatchValue(value=s))])).count
        for s in df["split"].unique()}  # fmt: skip
    store.close()
    assert counts == df["split"].value_counts().to_dict(), counts
    manifest["by_split"] = counts
    res.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(cand["name"], counts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step", choices=["embed", "set-split"])
    ap.add_argument("--device", help="override s4.device, e.g. cpu for the longest messages")
    a = ap.parse_args()
    cfg = load_config("pipeline")
    out = ROOT / "runs/s4/full" / cfg["s4"]["choice"]
    out.mkdir(parents=True, exist_ok=True)
    if a.step == "embed":
        run_embed(cfg, out, a.device)
    else:
        run_set_split(cfg)


if __name__ == "__main__":
    main()
