"""S12: the versioned router artifact, a folder with `artifact.json` and `.npy` tables.

The tables hold numbers only and are loaded without pickle. Their hashes are in the JSON, so a
changed or mixed-up file is refused on load.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from metis.router.route import Router

SCHEMA_VERSION = 1
TABLES = ("centroids", "psi", "counts", "c_hat")
ROUTER_TYPES = ("uniroute", "zerorouter", "knn", "logistic", "always-best", "always-cheapest")


@dataclass(frozen=True)
class Meta:
    method: str  # "point" | "pair"
    embedder_id: str
    k_star: int
    cluster_names: tuple[str, ...]
    models: tuple[str, ...]
    prices: dict[str, Any]
    lam: float
    lambda_mode: str  # "budget" | "quality"
    lambda_target: float
    router_type: str
    hashes: dict[str, str]  # val_set, gen_config, judge_config
    build_date: str
    tau: float | None = None  # pointwise
    anchor: str | None = None  # pairwise
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class RouterArtifact:
    meta: Meta
    centroids: np.ndarray  # (K, D)
    psi: np.ndarray  # (K, N)
    counts: np.ndarray  # (K,)
    c_hat: np.ndarray  # (N,)

    def __post_init__(self) -> None:
        m = self.meta
        if m.method == "point" and m.tau is None:
            raise ValueError("pointwise artifact needs tau")
        if m.method == "pair" and m.anchor not in m.models:
            raise ValueError("pairwise artifact needs an anchor from the pool")
        if m.method not in ("point", "pair"):
            raise ValueError(f"unknown method {m.method!r}")
        if m.router_type not in ROUTER_TYPES:
            raise ValueError(f"unknown router type {m.router_type!r}")
        if len(m.cluster_names) != m.k_star or len(self.counts) != m.k_star:
            raise ValueError("cluster names and counts must match K*")
        self.router()  # checks the table shapes

    def router(self) -> Router:
        return Router(self.meta.models, self.centroids, self.psi, self.c_hat)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_artifact(artifact: RouterArtifact, folder: str | Path) -> Path:
    """Write a new version; an existing version is never overwritten."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    files = {}
    for name in TABLES:
        path = folder / f"{name}.npy"
        np.save(path, getattr(artifact, name), allow_pickle=False)
        files[name] = _sha256(path)
    payload = {**asdict(artifact.meta), "files": files}
    with open(folder / "artifact.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
    return folder


def load_artifact(folder: str | Path) -> RouterArtifact:
    folder = Path(folder)
    with open(folder / "artifact.json", encoding="utf-8") as f:
        payload = json.load(f)
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"artifact schema {payload['schema_version']} is not supported")
    files = payload.pop("files")
    tables = {}
    for name in TABLES:
        path = folder / f"{name}.npy"
        if _sha256(path) != files[name]:
            raise ValueError(f"{path.name} does not match its hash")
        tables[name] = np.load(path, allow_pickle=False)
    payload["cluster_names"] = tuple(payload["cluster_names"])
    payload["models"] = tuple(payload["models"])
    return RouterArtifact(meta=Meta(**payload), **tables)
