import json

from app.core import search_log


def test_log_search_writes_jsonl_entry_without_chunk_text(tmp_path, monkeypatch):
    monkeypatch.setattr(search_log, "LOG_FILE_PATH", tmp_path / "search.jsonl")

    results = [
        {
            "chunk_id": "doc1_0",
            "document_id": "doc1",
            "chunk_index": 0,
            "text": "청크 내용",
            "similarity": 0.82,
            "filename": "노트.md",
            "source_url": None,
        }
    ]
    search_log.log_search("싱글톤이 뭐야?", 10, results, 12.5)

    lines = search_log.LOG_FILE_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["query"] == "싱글톤이 뭐야?"
    assert entry["top_k"] == 10
    assert entry["result_count"] == 1
    assert entry["results"] == [
        {
            "chunk_id": "doc1_0",
            "document_id": "doc1",
            "filename": "노트.md",
            "source_url": None,
            "similarity": 0.82,
        }
    ]
    assert entry["response_time_ms"] == 12.5
    assert "timestamp" in entry


def test_log_search_records_empty_results(tmp_path, monkeypatch):
    monkeypatch.setattr(search_log, "LOG_FILE_PATH", tmp_path / "search.jsonl")

    search_log.log_search("아무거나", 5, [], 1.0)

    entry = json.loads(search_log.LOG_FILE_PATH.read_text(encoding="utf-8"))
    assert entry["result_count"] == 0
    assert entry["results"] == []
