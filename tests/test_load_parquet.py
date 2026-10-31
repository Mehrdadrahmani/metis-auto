"""Parquet loader tests on tiny hand-written tables (not derived from the real data)."""

import json
from datetime import datetime

import pandas as pd
import pytest

from metis.data.load import SchemaError, load_with_report
from metis.data.load_parquet import is_parquet_dir, iter_sessions, message_types


def _msg(mid, sid, kind, sec, content="x", rag=None, inp=None, att=None):
    ts = None if sec is None else datetime(2026, 9, 1, 10, 0, sec)
    return {
        "message_id": mid,
        "session_id": sid,
        "type": kind,
        "timestamp": ts,
        "content": content,
        "finish_reason": "STOP",
        "attachments": att,
        "rag": rag,
        "input": inp,
    }


@pytest.fixture
def root(tmp_path):
    bots = [
        {"bot_id": "b1", "provider_model": "gpt-x", "provider_name": "openai", "instructions": "be"}
    ]
    sessions = [
        {
            "session_id": sid,
            "bot_id": "b1",
            "user_id": "u1",
            "created_at": datetime(2026, 9, 1),
            "dialogue_length": n,
        }
        for sid, n in [("s1", 3), ("s2", 2)]
    ]
    rag = json.dumps([{"query": "q", "relevantChunks": [{"content": "c1"}, {"content": "c2"}]}])
    inp = json.dumps({"items": [{"type": "SINGLE_CHOICE", "choices": ["a"]}]})
    att = json.dumps([{"contentType": "IMAGE", "content": "https://x/a.png"}])
    msgs = [
        _msg("m3", "s1", "AI", 2),
        _msg("m1", "s1", "USER", 1, att=att),
        _msg("m2", "s1", "AI", 1, rag=rag, inp=inp),
        _msg("m4", "s2", "SYSTEM", None),
        _msg("m5", "s2", "USER", 5),
    ]
    pd.DataFrame(bots).to_parquet(tmp_path / "chat_bot.parquet")
    pd.DataFrame(sessions).to_parquet(tmp_path / "chat_session.parquet")
    pd.DataFrame(msgs[:2]).to_parquet(tmp_path / "chat_message-00000-of-00002.parquet")
    pd.DataFrame(msgs[2:]).to_parquet(tmp_path / "chat_message-00001-of-00002.parquet")
    return tmp_path


def test_joins_tables_across_shards(root):
    assert is_parquet_dir(root)
    sessions = list(iter_sessions(root))
    assert [s.session_id for s in sessions] == ["s1", "s2"]
    s = sessions[0]
    assert [m.extra["message_id"] for m in s.messages] == ["m1", "m2", "m3"]
    assert [m.role for m in s.messages] == ["user", "bot", "bot"]
    assert (s.user_turns, s.bot_turns, s.session_len) == (1, 2, 3)
    assert s.category is None and s.extra["bot_id"] == "b1"


def test_bot_fields_only_on_bot_messages(root):
    user, bot, _ = next(iter_sessions(root)).messages
    assert user.model is None and user.instructions is None
    assert (bot.model, bot.provider, bot.instructions) == ("gpt-x", "openai", "be")


def test_rag_widgets_attachments(root):
    user, bot, plain = next(iter_sessions(root)).messages
    assert bot.rag.context == ["c1", "c2"] and bot.rag.query == "q"
    assert bot.input[0].type == "SINGLE_CHOICE" and bot.input[0].choices == ["a"]
    assert user.attachments[0].content_type == "IMAGE"
    assert plain.rag is None and plain.input == []


def test_null_timestamp_sorts_last(root):
    s2 = list(iter_sessions(root))[1]
    assert [m.role for m in s2.messages] == ["user", "system"]
    assert s2.messages[1].timestamp is None


def test_limit_and_report(root):
    _, report = load_with_report(root)
    assert (report.n_sessions, report.n_messages) == (2, 5) and not report.mismatches
    assert len(list(iter_sessions(root, limit_sessions=1))) == 1
    assert message_types(root) == {"AI": 2, "USER": 2, "SYSTEM": 1}


def test_length_mismatch_and_unknown_type(root):
    df = pd.read_parquet(root / "chat_session.parquet")
    df.loc[0, "dialogue_length"] = 9
    df.to_parquet(root / "chat_session.parquet")
    with pytest.raises(SchemaError):
        list(iter_sessions(root, strict=True))
    bad = pd.DataFrame([_msg("m9", "s2", "ROBOT", 9)])
    bad.to_parquet(root / "chat_message-00002-of-00003.parquet")
    with pytest.raises(SchemaError):
        list(iter_sessions(root))
