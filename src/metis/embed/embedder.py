"""S4: one frozen multilingual embedder (WP-03, D-048).

`Embedder.encode(texts)` returns L2-normalized float32 vectors. The whole text is embedded (D-047):
`max_tokens` is set to the model limit, and `count_tokens` lets callers report inputs above it.
`embedder_id` = name + pinned revision + hash of the preprocessing config, so vectors from different
settings never mix (one Qdrant collection per id).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np

from metis.config import config_id


class _Model(Protocol):
    def encode(self, sentences: list[str], **kw: Any) -> Any: ...


@dataclass
class Embedder:
    name: str
    revision: str
    device: str = "cpu"
    max_tokens: int = 32768
    prefix: str = ""
    task: str | None = "clustering"  # Jina v5 LoRA adapter; None for models without tasks
    prompt_name: str | None = "document"  # model-side prompt ("Document: "), as the model card
    dtype: str = "float32"
    batch_size: int = 16
    max_batch_tokens: int | None = 8192  # batch size × longest input ≤ this (memory)
    path: str | None = None  # local copy (models/<short>_<rev12>/, scripts/fetch_model.py)
    model: _Model | None = field(default=None, repr=False)  # injected in tests

    def __post_init__(self) -> None:
        if self.model is None:
            self.model = self._load()

    def _load(self) -> _Model:
        import torch
        from sentence_transformers import SentenceTransformer

        local = self.path is not None
        m = SentenceTransformer(
            self.path if local else self.name,
            revision=None if local else self.revision,
            trust_remote_code=True,
            device=self.device,
            model_kwargs={"dtype": getattr(torch, self.dtype)},
        )
        m.max_seq_length = self.max_tokens
        m.eval()
        return m

    @property
    def preprocessing(self) -> dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "prefix": self.prefix,
            "task": self.task,
            "prompt_name": self.prompt_name,
            "dtype": self.dtype,
            "normalize": "l2",
        }

    @property
    def embedder_id(self) -> str:
        short = self.name.rsplit("/", 1)[-1]
        return f"{short}@{self.revision[:12]}#{config_id(self.preprocessing)}"

    def encode(self, texts: list[str], batch_size: int | None = None) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        bs = batch_size or self.batch_size
        if len(texts) == 1 or self.max_batch_tokens is None or not hasattr(self.model, "tokenizer"):
            return self._encode(texts, bs)
        # token-budget batches (longest first): a batch of long messages would need > 11 GB
        ntok = np.array(self.count_tokens(texts))
        order = np.argsort(-ntok, kind="stable")
        out = np.zeros((len(texts), 0), np.float32)
        i = 0
        while i < len(order):
            n = int(max(1, min(bs, self.max_batch_tokens // max(1, ntok[order[i]]))))
            idx = order[i : i + n]
            v = self._encode([texts[j] for j in idx], n)
            if out.shape[1] == 0:
                out = np.zeros((len(texts), v.shape[1]), np.float32)
            out[idx] = v
            i += n
        return out

    def _encode(self, texts: list[str], batch_size: int) -> np.ndarray:
        kw: dict[str, Any] = {
            "batch_size": batch_size,
            "convert_to_numpy": True,
            "normalize_embeddings": False,  # we normalize ourselves, in float32
            "show_progress_bar": False,
        }
        if self.task is not None:
            kw["task"] = self.task
        if self.prompt_name is not None:
            kw["prompt_name"] = self.prompt_name
        vecs = np.asarray(self.model.encode([self.prefix + t for t in texts], **kw), np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.maximum(norms, 1e-12)

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Token counts as the model sees them (prompt, prefix and special tokens included)."""
        tok = self.model.tokenizer
        prompt = getattr(self.model, "prompts", {}).get(self.prompt_name or "", "")
        return [len(ids) for ids in tok([prompt + self.prefix + t for t in texts])["input_ids"]]
