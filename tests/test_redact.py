"""Redaction tests. Fake keys are assembled at runtime so the source never looks like a key
(the pre-commit secret scan would block it)."""

import pytest

from metis.data.redact import redact, redact_counts, redact_message
from metis.data.schema import Attachment, InputWidget, Message, Rag

A = "a1B2c3D4e5F6g7H8i9J0kLmNoPqRsTuV"  # 32 key-like characters


def fake(prefix: str, body: str = A) -> str:
    return prefix + body


CASES = {
    "anthropic": f"use {fake('sk-' + 'ant-api03-')} here",
    "openai": f"key is {fake('sk-' + 'proj-')}",
    "google": f"gemini {fake('AI' + 'za', 'SyA' + A)} ok",
    "github": f"token {fake('gh' + 'p_')}",
    "slack": f"bot {fake('xo' + 'xb-', '123456-' + A)}",
    "aws": "id " + "AK" + "IA" + "ABCDEFGHIJKLMNOP" + " end",
    "jwt": "auth " + "ey" + "J" + A[:20] + "." + A[:20] + "." + A[:12],
    "bearer": "Authorization: " + "Bear" + "er " + A,
    "url_param": "https://api.example.com/v1?model=x&" + "key=" + A + "&q=1",
    "api_key": "GEMINI_" + 'API_KEY="' + "abc123xyz" + '"',
    "password": "db " + "pass" + "word: hunter2secret",
    "credential": "client_" + "secret = " + A,
    "long_token": 'config = {"x": "' + "0123456789abcdef" * 3 + '"}',
    "opaque_value": "license: " + "ABCD1234EFGH5678IJKL9012MN",
}


@pytest.mark.parametrize("kind", sorted(CASES))
def test_each_kind_redacted(kind):
    text = CASES[kind]
    out, counts = redact_counts(text)
    assert counts[kind] >= 1, (kind, dict(counts))
    assert f"[REDACTED:{kind}]" in out
    assert A not in out


@pytest.mark.parametrize("kind", sorted(CASES))
def test_idempotent(kind):
    once, n1 = redact(CASES[kind])
    twice, n2 = redact(once)
    assert n1 >= 1
    assert twice == once
    assert n2 == 0


def test_key_inside_assignment_counted_once():
    text = 'OPENAI_API_KEY="' + fake("sk-" + "proj-") + '"'
    out, counts = redact_counts(text)
    assert sum(counts.values()) == 1
    assert counts["openai"] == 1
    assert redact(out)[1] == 0


@pytest.mark.parametrize(
    "text",
    [
        "سلام، قیمت این محصول ۱۲۵۰۰۰ تومان است و شماره تماس ۰۹۱۲۳۴۵۶۷۸۹ می‌باشد.",
        "سفارش شماره 4567891234 در تاریخ 1403/05/12 ثبت شد. کد پیگیری: 98765432",
        "Price is 1,250,000 rials; call 09123456789 or visit https://example.com/page?id=42",
        "رمز عبور خود را فراموش کرده‌ام. چطور توکن جدید بگیرم؟",
        'session "3f2b8c1e-9a4d-4e2b-8f1c-0d9e8a7b6c5d" started',
        "The password field must not be empty. Tokens are counted per request.",
        "----------------------------------------------",
        "meeting at 12:30, ratio 16:9, see https://example.com/abcdefghijklmnopqrstuvwxyz123",
        "slug: my-long-product-name-2024-edition-v2",
    ],
)
def test_no_false_positive(text):
    out, n = redact(text)
    assert n == 0
    assert out == text


def test_empty_and_none_like():
    assert redact("") == ("", 0)


def test_redact_message_all_fields():
    k = fake("sk-" + "proj-")
    m = Message(
        role="bot",
        content="answer " + k,
        model="m",
        instructions="system " + k,
        rag=Rag(query="q " + k, context=["c " + k, {"text": "d " + k}]),
        input=[InputWidget(type="SINGLE_CHOICE", label="l " + k, choices=["x " + k])],
        attachments=[Attachment(content_type="IMAGE", content="https://x.com/a.png?token=" + A)],
    )
    red, hits = redact_message(m)
    assert hits == {
        "content": 1,
        "instructions": 1,
        "rag.query": 1,
        "rag.context": 2,
        "attachments": 1,
        "input": 2,
        "extra": 0,
    }
    assert k not in red.content + red.instructions + red.rag.query
    assert k not in str(red.rag.context) + str(red.input[0].choices) + red.input[0].label
    assert A not in red.attachments[0].content
    assert m.content.endswith(k)  # original untouched
    # second pass: nothing left
    assert sum(redact_message(red)[1].values()) == 0


def test_repr_hides_content():
    m = Message(role="user", content="SECRET-TEXT", instructions="SYS")
    assert "SECRET-TEXT" not in repr(m)
    assert "SYS" not in repr(m)
