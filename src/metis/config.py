"""Config loading with a stable id (hash of the canonical JSON), AGENTS.md §7."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"


def config_id(cfg: Any) -> str:
    canon = json.dumps(cfg, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]


def load_config(name: str, config_dir: Path | None = None) -> dict[str, Any]:
    """Load `configs/<name>.yaml`; adds `_id` (hash of the content without `_id`)."""
    path = (config_dir or CONFIG_DIR) / f"{name}.yaml"
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_id"] = config_id(cfg)
    return cfg
