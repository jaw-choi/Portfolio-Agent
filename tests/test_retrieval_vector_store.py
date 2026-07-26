from app.retrieval import vector_store


def fake_embed_texts(texts):
    return [[float(len(t)), 0.0] for t in texts]


def test_add_chunks_upserts_into_collection(tmp_path, monkeypatch):
    monkeypatch.setattr(vector_store, "VECTOR_STORE_DIR", tmp_path / "vector_store")
    monkeypatch.setattr(vector_store, "embed_texts", fake_embed_texts)

    chunks = [
        {"chunk_id": "doc1_0", "document_id": "doc1", "chunk_index": 0, "text": "hello"},
        {"chunk_id": "doc1_1", "document_id": "doc1", "chunk_index": 1, "text": "world!"},
    ]

    vector_store.add_chunks(chunks)

    collection = vector_store._get_collection()
    result = collection.get(ids=["doc1_0", "doc1_1"], include=["documents", "metadatas"])

    assert result["documents"] == ["hello", "world!"]
    assert result["metadatas"][0] == {"document_id": "doc1", "chunk_index": 0}
    assert result["metadatas"][1] == {"document_id": "doc1", "chunk_index": 1}


def test_add_chunks_with_empty_list_does_not_call_embedder(tmp_path, monkeypatch):
    monkeypatch.setattr(vector_store, "VECTOR_STORE_DIR", tmp_path / "vector_store")
    calls = []
    monkeypatch.setattr(
        vector_store, "embed_texts", lambda texts: calls.append(texts) or []
    )

    vector_store.add_chunks([])

    assert calls == []
