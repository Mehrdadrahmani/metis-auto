import re
from pathlib import Path

import pytest

from metis.data import sealed


def test_refused_outside_eval_script(tmp_path):
    with pytest.raises(PermissionError):
        sealed.read_sealed_parquet(tmp_path / "x.sealed.parquet")


def test_refused_without_tag(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["eval_test.py"])
    monkeypatch.setattr(sealed, "_tag_commit", lambda: None)
    with pytest.raises(PermissionError):
        sealed.read_sealed_parquet(tmp_path / "x.sealed.parquet")


def test_no_other_code_names_sealed_data_files():
    """Only the eval script may read sealed labels or answers; s7_stats.py only writes them."""
    pattern = re.compile(r"(labels|responses|pointwise|noise)[\w{}]*\.?test\.sealed|labels_test\.sealed|responses_test\.sealed")
    bad = []
    for root in ("src", "scripts"):
        for path in Path(root).rglob("*.py"):
            if path.name not in ("eval_test.py", "s7_stats.py") and pattern.search(path.read_text(encoding="utf-8")):
                bad.append(str(path))
    assert not bad
