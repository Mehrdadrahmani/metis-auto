"""Shared parts of the paid stage scripts S6 and S7 (WP-06 step 6).

The test ids are read from `test_ids.sealed` only inside a batch and are never printed. Test output
files carry `.sealed` in their name (AGENTS.md section 6).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

from metis.data.split import ids_sha256

T_OUT = 300  # PLAN 7.2, mean answer tokens
SETS = ("pilot", "val", "test")
OPEN_SETS = ("pilot", "val")  # sets that may be judged or analysed here
TEXT_COLUMNS = ("text", "instructions", "history", "rag_context", "est_tokens_in")


def select_ids(split_path: Path, which: str, limit: int | None = None) -> list[str]:
    if which not in SETS:
        raise ValueError(f"unknown set {which}")
    if which == "test":
        ids = sorted(json.loads((split_path.parent / "test_ids.sealed").read_text(encoding="utf-8")))
        return ids[:limit] if limit else ids
    df = pd.read_parquet(split_path, columns=["prompt_id", "split", "in_pilot"])
    picked = df[df["in_pilot"]] if which == "pilot" else df[df["split"] == "val"]
    ids = sorted(picked["prompt_id"])
    return ids[:limit] if limit else ids


def file_tag(which: str) -> str:
    """Name part of output files: test files are marked sealed."""
    return "test.sealed" if which == "test" else which


def _as_list(value: Any) -> list[Any]:
    return [] if value is None else list(value)


def load_rows(prompts_path: Path, ids: list[str]) -> dict[str, dict[str, Any]]:
    """Text and context for ``ids``. The full data keeps context in ``context/part-*.parquet``."""
    names = set(pq.ParquetFile(prompts_path).schema_arrow.names)
    wide = [c for c in TEXT_COLUMNS if c in names]
    filters = [("prompt_id", "in", ids)]
    df = pd.read_parquet(prompts_path, columns=["prompt_id", *wide], filters=filters)
    if "instructions" not in names:
        parts = sorted((prompts_path.parent / "context").glob("part-*.parquet"))
        cols = ["prompt_id", "instructions", "history", "rag_context"]
        extra = pd.concat(pd.read_parquet(p, columns=cols, filters=filters) for p in parts)
        df = df.merge(extra, on="prompt_id", how="left")
    if len(df) != len(ids):
        raise ValueError(f"expected {len(ids)} prompts, found {len(df)}")
    rows = {}
    for row in df.to_dict("records"):
        row["history"] = [dict(t) for t in _as_list(row.get("history"))]
        row["rag_context"] = _as_list(row.get("rag_context"))
        rows[row["prompt_id"]] = row
    return rows


def cheapest_first(models: dict[str, dict[str, Any]], ids: list[str]) -> list[str]:
    return sorted(ids, key=lambda m: (models[m]["price_in"] + models[m]["price_out"], m))


def write_manifest(path: Path, ids: list[str], extra: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {"inputs_sha256": ids_sha256(ids), "n_prompts": len(ids), **extra}
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
