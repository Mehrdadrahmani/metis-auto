"""G3: exact then meaning cache, one namespace per chatbot + instructions + language (PLAN E5, E8).

In memory with numpy for speed, stored in SQLite so it survives a restart. Local only, never in git.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Entry:
    key: str
    vec: np.ndarray
    answer: str
    model: str
    created: float


class SemanticCache:
    def __init__(self, theta: float = 0.97, ttl_days: float = 7, path: str | Path | None = None, semantic: bool = True, clock: Callable[[], float] = time.time):
        self.theta, self.ttl_s, self.semantic, self.clock = theta, ttl_days * 86400, semantic, clock
        self.spaces: dict[str, list[Entry]] = {}
        self.matrix: dict[str, np.ndarray] = {}
        self.lock = threading.Lock()
        self.db = None
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(str(path), check_same_thread=False)
            self.db.execute("CREATE TABLE IF NOT EXISTS cache (space, key, vec BLOB, answer, model, created)")
            for space, key, vec, answer, model, created in self.db.execute("SELECT * FROM cache"):
                self._add(space, Entry(key, np.frombuffer(vec, dtype=np.float32), answer, model, created))

    def _add(self, space: str, entry: Entry) -> None:
        self.spaces.setdefault(space, []).append(entry)
        self.matrix.pop(space, None)

    def _live(self, space: str) -> list[Entry]:
        now = self.clock()
        entries = [e for e in self.spaces.get(space, []) if now - e.created <= self.ttl_s]
        if len(entries) != len(self.spaces.get(space, [])):
            self.spaces[space] = entries
            self.matrix.pop(space, None)
        return entries

    def lookup(self, space: str, key: str, vec: np.ndarray) -> tuple[str, Entry] | None:
        with self.lock:
            entries = self._live(space)
            if not entries:
                return None
            for e in entries:
                if e.key == key:
                    return "hit_exact", e
            if not self.semantic:
                return None
            if space not in self.matrix:
                m = np.stack([e.vec for e in entries]).astype(np.float32)
                self.matrix[space] = m / np.linalg.norm(m, axis=1, keepdims=True)
            q = np.asarray(vec, dtype=np.float32)
            sims = self.matrix[space] @ (q / np.linalg.norm(q))
            i = int(sims.argmax())
            return ("hit_semantic", entries[i]) if sims[i] >= self.theta else None

    def store(self, space: str, key: str, vec: np.ndarray, answer: str, model: str) -> None:
        entry = Entry(key, np.asarray(vec, dtype=np.float32), answer, model, self.clock())
        with self.lock:
            self._add(space, entry)
            if self.db:
                self.db.execute("INSERT INTO cache VALUES (?,?,?,?,?,?)", (space, key, entry.vec.tobytes(), answer, model, entry.created))
                self.db.commit()
