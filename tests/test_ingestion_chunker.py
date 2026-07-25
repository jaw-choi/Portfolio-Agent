import json

from app.ingestion import chunker


def test_chunk_text_returns_empty_list_for_empty_text():
    assert chunker.chunk_text("doc1", "") == []


def test_chunk_text_single_chunk_when_short():
    chunks = chunker.chunk_text("doc1", "hello world", chunk_size=500, overlap=50)

    assert len(chunks) == 1
    assert chunks[0] == {
        "chunk_id": "doc1_0",
        "document_id": "doc1",
        "chunk_index": 0,
        "text": "hello world",
    }


def test_chunk_text_splits_long_text_with_unique_ids():
    text = " ".join(f"word{i}" for i in range(200))

    chunks = chunker.chunk_text("doc1", text, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    chunk_ids = [c["chunk_id"] for c in chunks]
    assert chunk_ids == [f"doc1_{i}" for i in range(len(chunks))]
    assert len(set(chunk_ids)) == len(chunk_ids)
    for i, c in enumerate(chunks):
        assert c["chunk_index"] == i
        assert c["document_id"] == "doc1"


def test_chunk_text_overlap_repeats_trailing_words():
    text = " ".join(f"word{i}" for i in range(200))

    chunks = chunker.chunk_text("doc1", text, chunk_size=100, overlap=20)

    first_words = chunks[0]["text"].split()
    second_words = chunks[1]["text"].split()
    assert first_words[-1] in second_words[: len(second_words) // 2 + 1]


def test_save_chunks_writes_json_file(tmp_path, monkeypatch):
    monkeypatch.setattr(chunker, "CHUNKS_DIR", tmp_path)
    chunks = chunker.chunk_text("doc123", "hello world")

    output_path = chunker.save_chunks("doc123", chunks)

    assert output_path == tmp_path / "doc123.json"
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved == chunks
