"""Local MLflow tracing (WP-04 step 8b, D-044). Local files only, telemetry off.

``METIS_TRACING=0`` turns everything here into a no-op. MLflow is imported lazily so that code
which does not trace stays fast to import. Callers pass only redacted text.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

# Must be set before mlflow is imported.
os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")
os.environ.setdefault("DO_NOT_TRACK", "true")
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

_ready_for: str | None = None


def enabled() -> bool:
    return os.environ.get("METIS_TRACING", "1") != "0"


def mlflow_dir() -> Path:
    return Path(os.environ.get("METIS_MLFLOW_DIR", ROOT / "mlflow"))


def _mlflow() -> Any:
    """Import mlflow and point it at the local store (once per store)."""
    global _ready_for
    import mlflow

    folder = mlflow_dir()
    if _ready_for != str(folder):
        folder.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(f"sqlite:///{folder / 'mlflow.db'}")
        if mlflow.get_experiment_by_name("metis") is None:
            mlflow.create_experiment("metis", artifact_location=(folder / "artifacts").as_uri())
        mlflow.set_experiment("metis")
        _ready_for = str(folder)
    return mlflow


@contextmanager
def batch_run(stage: str, params: dict[str, Any]) -> Iterator[Any]:
    """One MLflow run per ``run_batch``. Yields a ``log(metrics)`` function."""
    if not enabled():
        yield lambda metrics: None
        return
    mlflow = _mlflow()
    with mlflow.start_run(run_name=stage):
        mlflow.log_params({"stage": stage, **params})
        yield mlflow.log_metrics
        mlflow.flush_trace_async_logging()


@contextmanager
def call_span(model_id: str, messages: list[dict[str, Any]]) -> Iterator[Any]:
    """Trace one call. Yields ``finish(outputs)``; ``messages`` must already be redacted."""
    if not enabled():
        yield lambda outputs: None
        return
    mlflow = _mlflow()
    with mlflow.start_span(name=f"llm:{model_id}", span_type="LLM") as span:
        span.set_inputs({"messages": messages})
        yield span.set_outputs
