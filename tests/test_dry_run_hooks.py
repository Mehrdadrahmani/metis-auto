"""WP-07: the mock-only cache and recording hooks, and the pipeline's refusal without --mock."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from metis.llm import callcache, client

ROOT = Path(__file__).resolve().parents[1]


def test_record_only_writes_requested_file(tmp_path, monkeypatch):
    path = tmp_path / "requests.jsonl"
    monkeypatch.setenv("METIS_MOCK", "1")
    monkeypatch.setenv("METIS_MOCK_RECORD", str(path))
    client.complete("deepseek-v4-flash", [{"role": "user", "content": "hello"}])
    assert json.loads(path.read_text("utf-8"))["messages"][0]["content"] == "hello"


def test_mock_cache_override_cannot_reach_a_real_run(tmp_path, monkeypatch):
    monkeypatch.setenv("METIS_MOCK_CACHE", str(tmp_path / "c.sqlite"))
    monkeypatch.setenv("METIS_MOCK", "1")
    assert callcache.default_path() == tmp_path / "c.sqlite"
    monkeypatch.setenv("METIS_MOCK", "0")
    assert callcache.default_path().name == "llm_calls.sqlite"


def test_pipeline_refuses_without_mock():
    run = subprocess.run(
        [sys.executable, "scripts/pipeline.py"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert run.returncode != 0 and "--mock" in run.stderr
