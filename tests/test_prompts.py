"""S1 prompts table tests on hand-made sessions (not from the real data)."""

from metis.config import load_config
from metis.data.prompts import build_prompts, exclusion_counts
from metis.data.schema import Attachment, InputWidget, Message, Rag, Session

CFG = load_config("pipeline")
KEY = "sk-" + "proj-" + "a1B2c3D4e5F6g7H8i9J0kLmN"


def bot(content="ok", model="gpt-4o-mini", provider="openai", instr="be helpful", **kw):
    return Message(
        role="bot",
        content=content,
        model=model,
        provider=provider,
        instructions=instr,
        timestamp=kw.pop("ts", "2026-01-01 10:00:05"),
        **kw,
    )


def user(content, ts="2026-01-01 10:00:00", **kw):
    return Message(role="user", content=content, timestamp=ts, **kw)


def session(sid, msgs, category="shop"):
    return Session(session_id=sid, category=category, created_at="2026-01-01 10:00:00",
                   messages=msgs)  # fmt: skip


def build(sessions):
    df, counts = build_prompts(sessions, CFG)
    return df.set_index("prompt_id", drop=False), counts


def test_rows_and_flags():
    s = session(
        "s1",
        [
            user("سلام، سفارشم کجاست؟ " + KEY),
            bot(
                "پاسخ",
                rag=Rag(query="q", context=["c1", "c2"]),
                input=[InputWidget(type="SINGLE_CHOICE", choices=["بله", "خير"])],
            ),
            user("خیر", ts="2026-01-01 10:01:00"),  # widget click (normalized match)
            bot("workflow step", model="default", provider="workflow"),
            user("یه عکس", attachments=[Attachment(content_type="IMAGE", content="https://x")]),
            bot("dalle answer", model="dalle", provider="imagination"),
            user("!!!"),
            bot(model=None, provider=None, instr=None),
            user("question", ts="2026-01-01 10:02:00"),
            bot(instr="x" * 20001),
            user("no reply at the end"),
        ],
    )
    df, counts = build([s])
    assert counts["user_messages"] == 6 and counts["user_without_reply"] == 1
    assert len(df) == 5
    r = df.iloc
    first, widget, image, junk, huge = (r[i] for i in range(5))
    assert KEY not in first["text"] and "[REDACTED:openai]" in first["text"]
    assert first["rag_context"] == ["c1", "c2"] and first["uses_rag"]
    assert first["lang"] == "fa" and first["eligible_labeled"] and first["eligible_train"]
    assert first["prod_latency_s"] == 5.0
    assert widget["widget_click"] and not widget["eligible_train"]
    assert widget["reply_workflow"]
    assert image["has_image"] and image["reply_image"]
    assert junk["junk"] and junk["reply_no_model"]
    assert huge["huge_prompt"] and huge["instr_len_bucket"] == ">20k"
    assert not huge["eligible_labeled"] and huge["eligible_train"]
    # history: earlier messages only, roles mapped, redacted
    assert [t["role"] for t in huge["history"]][:2] == ["user", "assistant"]
    assert all(KEY not in t["content"] for t in huge["history"])
    ex = exclusion_counts(df)
    assert ex["eligible_labeled"] == 1
    assert sum(v for k, v in ex.items() if k.startswith("waterfall_")) == len(df) - 1


def test_exact_duplicates_keep_first_usable():
    s1 = session(
        "a", [user("سلام", ts="2026-01-01 09:00:00"), bot(model="default", provider="workflow")]
    )
    s2 = session("b", [user("سلام", ts="2026-01-01 10:00:00"), bot()])
    s3 = session("c", [user("سلام ", ts="2026-01-01 11:00:00"), bot()])
    s4 = session("d", [user("سلام", ts="2026-01-01 12:00:00"), bot()], category="other")
    df, _ = build([s1, s2, s3, s4])
    by_sid = df.set_index("session_id")
    # a is a workflow turn (excluded) and must not knock out b
    assert not by_sid.loc["b", "dup_exact"] and by_sid.loc["b", "eligible_labeled"]
    assert (
        by_sid.loc["c", "dup_exact"] and by_sid.loc["c", "dup_of"] == by_sid.loc["b", "prompt_id"]
    )
    assert not by_sid.loc["d", "dup_exact"]  # other chatbot


def test_history_limits():
    msgs = []
    for i in range(15):
        msgs += [user(f"m{i}", ts=f"2026-01-01 10:{i:02d}:00"), bot(f"a{i}")]
    df, _ = build([session("h", msgs)])
    last = df.iloc[-1]
    assert len(last["history"]) == CFG["s1"]["history_max_turns"]
    assert last["history"][-1]["content"] == "a13"


def test_prompt_ids_stable():
    s = session("s", [user("x1"), bot()])
    assert build([s])[0]["prompt_id"].tolist() == build([s])[0]["prompt_id"].tolist()
