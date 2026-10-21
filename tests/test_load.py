"""Loader tests on a tiny hand-written fixture (not derived from the real data)."""

import json

import pytest

from metis.data.load import SchemaError, load_categories, load_dataset, load_with_report

FIXTURE = [
    {
        "category": "shop",
        "sessions": [
            {
                "session_id": "s1",
                "created_at": "2026-01-01T10:00:00Z",
                "user_turns": 2,
                "bot_turns": 1,
                "session_len": 3,
                "messages": [
                    {
                        "role": "user",
                        "content": "سلام",
                        "timestamp": "2026-01-01T10:00:00Z",
                        "attachments": [{"contentType": "IMAGE", "content": "https://x/a.png"}],
                    },
                    {
                        "role": "bot",
                        "content": "hello",
                        "timestamp": "2026-01-01T10:00:05Z",
                        "model": "gpt-4o-mini",
                        "provider": "openai",
                        "instructions": "be nice",
                        "rag": {"query": "q", "context": ["c1", "c2"]},
                        "input": {
                            "items": [
                                {
                                    "type": "SINGLE_CHOICE",
                                    "label": "pick",
                                    "name": "p",
                                    "choices": ["a", "b"],
                                    "required": True,
                                    "default": None,
                                    "placeholder": "",
                                }
                            ]
                        },
                        "new_field": 1,
                    },
                    {"role": "user", "content": "ok", "timestamp": "2026-01-01T10:01:00Z"},
                ],
            }
        ],
    },
    {
        "category": "support",
        "sessions": [
            {
                "session_id": "s2",
                "user_turns": 5,  # wrong on purpose
                "bot_turns": 0,
                "session_len": 1,
                "messages": [{"role": "user", "content": "hi"}],
            }
        ],
    },
]


@pytest.fixture
def path(tmp_path):
    p = tmp_path / "fixture.json"
    p.write_text(json.dumps(FIXTURE, ensure_ascii=False), encoding="utf-8")
    return p


def test_load_dataset(path):
    sessions = load_dataset(path)
    assert [s.session_id for s in sessions] == ["s1", "s2"]
    assert [s.category for s in sessions] == ["shop", "support"]
    s1 = sessions[0]
    assert [m.role for m in s1.messages] == ["user", "bot", "user"]
    user, bot = s1.messages[0], s1.messages[1]
    assert user.attachments[0].content_type == "IMAGE"
    assert bot.model == "gpt-4o-mini" and bot.provider == "openai"
    assert bot.rag.context == ["c1", "c2"]
    assert bot.input[0].type == "SINGLE_CHOICE" and bot.input[0].choices == ["a", "b"]
    assert bot.extra == {"new_field": 1}


def test_report_counts_and_mismatches(path):
    _, report = load_with_report(path)
    assert (report.n_categories, report.n_sessions, report.n_messages) == (2, 2, 4)
    assert report.extra_fields == {"message.new_field": 1}
    assert report.mismatches == {"user_turns": 1}


def test_strict_raises_without_content(path):
    with pytest.raises(SchemaError) as e:
        load_categories(path, strict=True)
    assert "s2" in str(e.value) and "hi" not in str(e.value)


def test_bad_structure(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"not": "a list"}))
    with pytest.raises(SchemaError):
        load_dataset(p)


def test_loader_prints_nothing(path, capsys):
    load_dataset(path)
    out = capsys.readouterr()
    assert out.out == "" and out.err == ""


def test_data_card_has_no_content(path):
    from metis.data.inspect import build_card, render_markdown

    card = build_card(path)
    assert (card["sessions"], card["messages"], card["rag_messages"]) == (2, 4, 1)
    assert card["instructions_nonempty"] == 1 and card["attachment_messages"] == 1
    md = render_markdown(card, "fixture.json")
    for text in ["سلام", "hello", "be nice", "c1", "pick", "https://x/a.png"]:
        assert text not in md
