"""Circuit breaker per model and a small provider error type (PLAN E3, E4)."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable


class ProviderError(RuntimeError):
    """A model call failed. `kind` is a class name only, never provider text."""

    def __init__(self, kind: str = "error"):
        super().__init__(kind)
        self.kind = kind


class Breaker:
    """closed → open after N failures in a window → half-open after a pause → one probe."""

    def __init__(self, failures: int = 3, window_s: float = 60, open_s: float = 30, clock: Callable[[], float] = time.monotonic):
        self.failures, self.window_s, self.open_s, self.clock = failures, window_s, open_s, clock
        self.recent: deque[float] = deque()
        self.opened_at: float | None = None
        self.probing = False

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "closed"
        return "half-open" if self.clock() - self.opened_at >= self.open_s else "open"

    def available(self) -> bool:
        state = self.state
        if state == "closed":
            return True
        return state == "half-open" and not self.probing

    def before_call(self) -> None:
        if self.state == "half-open":
            self.probing = True

    def success(self) -> None:
        self.recent.clear()
        self.opened_at, self.probing = None, False

    def failure(self) -> None:
        now = self.clock()
        if self.state == "half-open":
            self.opened_at, self.probing = now, False
            return
        self.recent.append(now)
        while self.recent and now - self.recent[0] > self.window_s:
            self.recent.popleft()
        if len(self.recent) >= self.failures:
            self.opened_at = now
            self.recent.clear()
