"""Collect result numbers for the TakRouter site. Aggregates only; nothing is typed by hand."""

from __future__ import annotations

import json
from pathlib import Path

load = lambda p: json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else None  # noqa: E731
out = {"test": load("results/final/final.json"), "live": load("results/final/live_latency.json"), "khayyam": load("results/khayyam/khayyam.json"), "val": load("results/replay_val.json")}
for k in ("head", "frozen_changed"):
    out["test"].pop(k, None)
Path("web/data.json").write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
print("ok", {k: bool(v) for k, v in out.items()})
