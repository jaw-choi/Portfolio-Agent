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


def test_query_returns_closest_chunk_first(tmp_path, monkeypatch):
    monkeypatch.setattr(vector_store, "VECTOR_STORE_DIR", tmp_path / "vector_store")
    monkeypatch.setattr(vector_store, "embed_texts", fake_embed_texts)

    chunks = [
        {"chunk_id": "doc1_0", "document_id": "doc1", "chunk_index": 0, "text": "hi"},
        {"chunk_id": "doc1_1", "document_id": "doc1", "chunk_index": 1, "text": "hi there"},
    ]
    vector_store.add_chunks(chunks)

    result = vector_store.query([2.0, 0.0], top_k=1)

    assert result["ids"][0] == ["doc1_0"]


def test_query_on_empty_collection_returns_empty_results(tmp_path, monkeypatch):
    monkeypatch.setattr(vector_store, "VECTOR_STORE_DIR", tmp_path / "vector_store")

    result = vector_store.query([0.1, 0.2], top_k=5)

    assert result["ids"] == [[]]
