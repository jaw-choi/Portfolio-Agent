from app.retrieval import search as search_module


def test_search_joins_metadata_and_returns_ordered_results(monkeypatch):
    monkeypatch.setattr(search_module, "embed_text", lambda query: [0.1, 0.2])

    raw_result = {
        "ids": [["doc1_0", "doc1_1"]],
        "documents": [["첫 번째 청크", "두 번째 청크"]],
        "metadatas": [
            [
                {"document_id": "doc1", "chunk_index": 0},
                {"document_id": "doc1", "chunk_index": 1},
            ]
        ],
        "distances": [[0.1, 0.5]],
    }
    monkeypatch.setattr(
        search_module, "query_vector_store", lambda embedding, top_k: raw_result
    )

    metadata_lookup = {
        "doc1": {"filename": "노트.md", "source_url": "https://example.com/doc1"}
    }
    monkeypatch.setattr(
        search_module, "get_document_metadata", lambda doc_id: metadata_lookup.get(doc_id)
    )

    results = search_module.search("싱글톤이 뭐야?", top_k=2)

    assert len(results) == 2
    assert results[0]["chunk_id"] == "doc1_0"
    assert results[0]["text"] == "첫 번째 청크"
    assert results[0]["similarity"] == 0.9
    assert results[0]["filename"] == "노트.md"
    assert results[0]["source_url"] == "https://example.com/doc1"
    assert results[1]["chunk_index"] == 1


def test_search_handles_missing_metadata_gracefully(monkeypatch):
    monkeypatch.setattr(search_module, "embed_text", lambda query: [0.1, 0.2])

    raw_result = {
        "ids": [["doc1_0"]],
        "documents": [["청크 내용"]],
        "metadatas": [[{"document_id": "doc1", "chunk_index": 0}]],
        "distances": [[0.2]],
    }
    monkeypatch.setattr(
        search_module, "query_vector_store", lambda embedding, top_k: raw_result
    )
    monkeypatch.setattr(search_module, "get_document_metadata", lambda doc_id: None)

    results = search_module.search("질문")

    assert results[0]["filename"] is None
    assert results[0]["source_url"] is None


def test_search_returns_empty_list_when_no_results(monkeypatch):
    monkeypatch.setattr(search_module, "embed_text", lambda query: [0.1, 0.2])
    monkeypatch.setattr(
        search_module,
        "query_vector_store",
        lambda embedding, top_k: {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        },
    )

    assert search_module.search("아무거나") == []
