"""Guard for sealed test files (AGENTS.md section 6, WP-14 acceptance check).

Sealed files open only from `scripts/eval_test.py`, and only once the `pre-test` tag exists. Every
opening is logged. Paid stages that write test output use `metis.llm.stage`, which never reads labels.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ALLOWED_SCRIPT = "eval_test.py"
LOG = Path("runs/final/sealed_opens.jsonl")


def _tag_commit() -> str | None:
    done = subprocess.run(["git", "rev-parse", "-q", "--verify", "pre-test^{commit}"], capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else None


def read_sealed_parquet(path: str | Path, columns: list[str] | None = None) -> pd.DataFrame:
    """Open a sealed parquet file for the final evaluation; refuses every other caller."""
    path = Path(path)
    if Path(sys.argv[0]).name != ALLOWED_SCRIPT:
        raise PermissionError(f"sealed files open only from {ALLOWED_SCRIPT}")
    tag = _tag_commit()
    if tag is None:
        raise PermissionError("sealed files stay closed until the pre-test tag exists")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": time.time(), "file": path.name, "pre_test": tag}) + "\n")
    return pd.read_parquet(path, columns=columns)
