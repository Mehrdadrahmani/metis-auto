"""Embedder wrapper (fake model) and Qdrant store (in-memory) tests."""

import hashlib
from pathlib import Path

import numpy as np
import pytest

from metis.embed.embedder import Embedder
from metis.embed.store import VectorStore, point_id


class FakeModel:
    """Deterministic: vector from the text hash; records what it was asked."""

    def __init__(self, dim=8):
        self.dim = dim
        self.calls = []

    def encode(self, sentences, **kw):
        self.calls.append((list(sentences), kw))
        out = []
        for s in sentences:
            seed = int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)
            out.append(np.random.default_rng(seed).normal(size=self.dim) * 5)
        return np.array(out)


def emb(**kw):
    return Embedder("org/fake-model", "abc123def4567890", model=FakeModel(), **kw)


def test_l2_normalized_float32():
    v = emb().encode(["سلام", "hello", "x"])
    assert v.dtype == np.float32
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-6)


def test_deterministic():
    e = emb()
    assert np.array_equal(e.encode(["سفارش من کجاست؟"]), e.encode(["سفارش من کجاست؟"]))


def test_prefix_and_task_passed():
    e = emb(prefix="query: ", task="clustering")
    e.encode(["a"])
    sentences, kw = e.model.calls[-1]
    assert sentences == ["query: a"]
    assert kw["task"] == "clustering" and kw["normalize_embeddings"] is False
    assert kw["prompt_name"] == "document"
    e2 = emb(task=None, prompt_name=None)
    e2.encode(["a"])
    assert "task" not in e2.model.calls[-1][1] and "prompt_name" not in e2.model.calls[-1][1]


def test_embedder_id_changes_with_preprocessing():
    a, b, c, d = emb(), emb(prefix="q: "), emb(task="retrieval"), emb(prompt_name="query")
    assert a.embedder_id.startswith("fake-model@abc123def456#")
    assert len({a.embedder_id, b.embedder_id, c.embedder_id, d.embedder_id}) == 4
    assert a.embedder_id == emb().embedder_id


def test_empty_input():
    assert emb().encode([]).shape[0] == 0


def unit(rng, n, d):
    x = rng.normal(size=(n, d)).astype(np.float32)
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def test_store_exact_search_equals_numpy():
    rng = np.random.default_rng(20261020)
    d, n = 16, 300
    vecs = unit(rng, n, d)
    ids = [f"p{i}" for i in range(n)]
    st = VectorStore("test@x#y", d, path=None)
    st.upsert(
        ids, vecs, [{"split": "val" if i % 2 else "train", "cluster": i % 4} for i in range(n)]
    )
    assert st.count() == n
    for q in unit(rng, 5, d):
        got = st.search(q, k=10, exact=True)
        sims = vecs @ q
        want = [ids[i] for i in np.argsort(-sims, kind="stable")[:10]]
        assert [g[0] for g in got] == want
        assert np.allclose([g[1] for g in got], np.sort(sims)[::-1][:10], atol=1e-5)
        got_f = st.search(q, k=5, filter={"split": "val"}, exact=True)
        val = [i for i in range(n) if i % 2]
        want_f = [ids[val[j]] for j in np.argsort(-(vecs[val] @ q), kind="stable")[:5]]
        assert [g[0] for g in got_f] == want_f


def test_store_upsert_idempotent_and_guards():
    st = VectorStore("t2", 4, path=None)
    v = np.eye(4, dtype=np.float32)
    st.upsert(["a", "b", "c", "d"], v)
    st.upsert(["a", "b", "c", "d"], v)
    assert st.count() == 4
    with pytest.raises(ValueError, match="looks like text"):
        st.upsert(["e"], v[:1], [{"note": "x" * 100}])
    with pytest.raises(ValueError, match="shape"):
        st.upsert(["e"], v)


def test_point_id_stable():
    assert point_id("abc") == point_id("abc") != point_id("abd")


class FakeTokModel(FakeModel):
    """FakeModel with a tokenizer: one token per character."""

    def tokenizer(self, texts):
        return {"input_ids": [list(t) for t in texts]}


def test_token_budget_batches_keep_order():
    m = FakeTokModel()
    e = Embedder("org/fake-model", "abc123def4567890", model=m, max_batch_tokens=100)
    texts = ["a" * 90, "b" * 10, "c" * 40, "d" * 5, "e" * 30]
    v = e.encode(texts, batch_size=64)
    ref = Embedder("org/fake-model", "abc123def4567890", model=FakeModel(), max_batch_tokens=None)
    assert np.array_equal(v, ref.encode(texts))
    assert all(len(s) * max(map(len, s)) <= 100 for s, _ in m.calls)


NANO = Path(__file__).parents[1] / "models/jina_v5_text_nano_8a7f00aac812"


@pytest.mark.skipif(not NANO.exists(), reason="local nano model not downloaded")
def test_merged_adapter_gives_same_vectors():
    texts = ["سلام، وقت بخیر", "سفارشم کی به دستم می‌رسه؟", "How do I sort a list in Python?"]
    kw = {"name": "jinaai/jina-embeddings-v5-text-nano", "revision": "8a7f00aac812"}
    kw["path"] = str(NANO)
    plain = Embedder(**kw).encode(texts)
    merged = Embedder(**kw, merge_adapter=True)
    assert np.abs(merged.encode(texts) - plain).max() < 1e-5
    assert merged.embedder_id != Embedder(**kw, model=FakeModel()).embedder_id
    with pytest.raises(ValueError, match="merged"):
        merged.model[0].model.set_adapter("retrieval")
