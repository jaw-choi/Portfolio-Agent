import numpy as np

from app.retrieval import embedder


class FakeModel:
    def encode(self, texts, convert_to_numpy=True):
        return np.array([[float(len(t)), 0.0] for t in texts])


def test_embed_texts_returns_list_of_lists(monkeypatch):
    monkeypatch.setattr(embedder, "_get_model", lambda: FakeModel())

    result = embedder.embed_texts(["안녕", "안녕하세요"])

    assert result == [[2.0, 0.0], [5.0, 0.0]]


def test_embed_text_returns_single_vector(monkeypatch):
    monkeypatch.setattr(embedder, "_get_model", lambda: FakeModel())

    result = embedder.embed_text("테스트")

    assert result == [3.0, 0.0]
