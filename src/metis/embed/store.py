"""Vector store: Qdrant in local mode (WP-03 step 4b, D-048). No Docker, path `qdrant/` (git-ignored).

One collection per `embedder_id` (cosine). Point id = UUID from the `prompt_id` hash. Payload holds
ids and numbers only (split, category, lang, cluster), never text: short strings are allowed,
anything longer than `MAX_PAYLOAD_STR` is refused.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path
from typing import Any

import numpy as np
from qdrant_client import QdrantClient, models

MAX_PAYLOAD_STR = 64


def point_id(prompt_id: str) -> str:
    return str(uuid.UUID(hashlib.sha256(prompt_id.encode("utf-8")).hexdigest()[:32]))


def collection_name(embedder_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", embedder_id)


def _check_payload(p: dict[str, Any]) -> None:
    for k, v in p.items():
        if isinstance(v, str) and (len(v) > MAX_PAYLOAD_STR or "\n" in v):
            raise ValueError(f"payload field {k!r} looks like text; only ids and numbers allowed")
        if not isinstance(v, (str, int, float, bool)) and v is not None:
            raise ValueError(f"payload field {k!r} has type {type(v).__name__}")


class VectorStore:
    def __init__(self, embedder_id: str, dim: int, path: str | Path | None = "qdrant/"):
        # path=None → in-memory (tests)
        self.client = (
            QdrantClient(location=":memory:") if path is None else QdrantClient(path=str(path))
        )
        self._local = True  # both constructors above are local (no server)
        self.name = collection_name(embedder_id)
        self.dim = dim
        if not self.client.collection_exists(self.name):
            self.client.create_collection(
                self.name,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            )

    def upsert(
        self, prompt_ids: list[str], vecs: np.ndarray, payloads: list[dict[str, Any]] | None = None
    ) -> None:
        if vecs.shape != (len(prompt_ids), self.dim):
            raise ValueError(f"vecs shape {vecs.shape} != ({len(prompt_ids)}, {self.dim})")
        payloads = payloads or [{} for _ in prompt_ids]
        points = []
        for pid, v, p in zip(prompt_ids, vecs, payloads, strict=True):
            p = {"prompt_id": pid, **p}
            _check_payload(p)
            points.append(models.PointStruct(id=point_id(pid), vector=v.tolist(), payload=p))
        for i in range(0, len(points), 256):
            self.client.upsert(self.name, points=points[i : i + 256], wait=True)

    def count(self) -> int:
        return self.client.count(self.name, exact=True).count

    def search(
        self, vec: np.ndarray, k: int, filter: dict[str, Any] | None = None, exact: bool = False
    ) -> list[tuple[str, float]]:
        """Top-k (prompt_id, cosine). `filter` = {field: value} (all must match).
        `exact=True` → brute force (the K-NN baseline must equal numpy). Local mode is always
        brute force, so the flag only matters against a Qdrant server."""
        flt = None
        if filter:
            flt = models.Filter(
                must=[
                    models.FieldCondition(key=f, match=models.MatchValue(value=v))
                    for f, v in filter.items()
                ]
            )
        res = self.client.query_points(
            self.name,
            query=np.asarray(vec, np.float32).tolist(),
            limit=k,
            query_filter=flt,
            search_params=models.SearchParams(exact=True) if exact and not self._local else None,
            with_payload=["prompt_id"],
        )
        return [(p.payload["prompt_id"], float(p.score)) for p in res.points]

    def close(self) -> None:
        self.client.close()
