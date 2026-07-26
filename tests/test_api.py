from unittest.mock import patch

from fastapi.testclient import TestClient

from app.ingestion import chunker, metadata_db, parser, storage
from app.main import app
from app.retrieval import vector_store

client = TestClient(app)


def test_chat_success():
    mocked = {"answer": "안녕하세요!", "reason": "인사에 대한 응답", "sources": []}
    with (
        patch("app.main.get_completion", return_value=mocked),
        patch("app.main.log_chat") as mock_log_chat,
    ):
        response = client.post("/chat", json={"message": "안녕하세요"})

    assert response.status_code == 200
    assert response.json() == mocked
    mock_log_chat.assert_called_once()
    args, _ = mock_log_chat.call_args
    assert args[0] == "안녕하세요"
    assert args[1] == "안녕하세요!"


def test_chat_input_error():
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_server_error():
    with patch("app.main.get_completion", side_effect=RuntimeError("LLM failure")):
        response = client.post("/chat", json={"message": "안녕하세요"})

    assert response.status_code == 500
    assert "LLM failure" in response.json()["detail"]


def test_read_logs():
    mocked_logs = [
        {
            "timestamp": "2026-07-24T00:00:00+00:00",
            "message": "q",
            "answer": "a",
            "response_time_ms": 12.3,
        }
    ]
    with patch("app.main.get_logs", return_value=mocked_logs) as mock_get_logs:
        response = client.get("/logs?limit=5")

    assert response.status_code == 200
    assert response.json() == mocked_logs
    mock_get_logs.assert_called_once_with(5)


def test_upload_document_success(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(parser, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(chunker, "CHUNKS_DIR", tmp_path / "chunks")
    monkeypatch.setattr(metadata_db, "DB_PATH", tmp_path / "metadata.db")
    monkeypatch.setattr(vector_store, "VECTOR_STORE_DIR", tmp_path / "vector_store")

    response = client.post(
        "/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "notes.txt"
    assert body["size_bytes"] == 5
    assert body["status"] == "uploaded"
    assert body["text_length"] == len("hello")
    assert body["chunk_count"] == 1
    assert (tmp_path / "processed" / f"{body['document_id']}.txt").read_text(
        encoding="utf-8"
    ) == "hello"
    assert (tmp_path / "chunks" / f"{body['document_id']}.json").exists()

    stored = metadata_db.get_document_metadata(body["document_id"])
    assert stored["filename"] == "notes.txt"
    assert stored["chunk_count"] == 1


def test_upload_document_rejects_unsupported_type():
    response = client.post(
        "/documents",
        files={"file": ("virus.exe", b"data", "application/octet-stream")},
    )

    assert response.status_code == 400


def test_read_documents():
    mocked_documents = [
        {
            "document_id": "doc1",
            "filename": "notes.txt",
            "size_bytes": 5,
            "status": "uploaded",
            "text_length": 5,
            "chunk_count": 1,
            "uploaded_at": "2026-07-26T00:00:00+00:00",
        }
    ]
    with patch("app.main.list_documents", return_value=mocked_documents) as mock_list:
        response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == mocked_documents
    mock_list.assert_called_once()


def test_crawl_blog_success(tmp_path, monkeypatch):
    monkeypatch.setattr(parser, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(chunker, "CHUNKS_DIR", tmp_path / "chunks")
    monkeypatch.setattr(metadata_db, "DB_PATH", tmp_path / "metadata.db")
    monkeypatch.setattr(vector_store, "VECTOR_STORE_DIR", tmp_path / "vector_store")

    mocked_crawl_result = {
        "posts": [
            {
                "document_id": "doc1",
                "url": "https://example.tistory.com/1",
                "title": "글 제목",
                "text": "본문 내용",
            }
        ],
        "failed": [{"url": "https://example.tistory.com/2", "error": "timeout"}],
    }
    with patch("app.main.crawl_blog", return_value=mocked_crawl_result) as mock_crawl:
        response = client.post(
            "/blog/crawl", json={"blog_url": "https://example.tistory.com"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["blog_url"] == "https://example.tistory.com"
    assert body["crawled_count"] == 1
    assert body["posts"][0]["document_id"] == "doc1"
    assert body["posts"][0]["chunk_count"] == 1
    assert body["failed"] == [{"url": "https://example.tistory.com/2", "error": "timeout"}]
    mock_crawl.assert_called_once_with("https://example.tistory.com")

    assert (tmp_path / "processed" / "doc1.txt").read_text(encoding="utf-8") == "본문 내용"
    stored = metadata_db.get_document_metadata("doc1")
    assert stored["filename"] == "글 제목"
    assert stored["source_url"] == "https://example.tistory.com/1"
    assert stored["status"] == "crawled"


def test_crawl_portfolio_success(tmp_path, monkeypatch):
    monkeypatch.setattr(parser, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(chunker, "CHUNKS_DIR", tmp_path / "chunks")
    monkeypatch.setattr(metadata_db, "DB_PATH", tmp_path / "metadata.db")
    monkeypatch.setattr(vector_store, "VECTOR_STORE_DIR", tmp_path / "vector_store")

    mocked_sections = [
        {
            "document_id": "sec1",
            "url": "https://example.github.io#about",
            "title": "About",
            "text": "자기소개 내용",
        }
    ]
    with patch(
        "app.main.crawl_portfolio", return_value=mocked_sections
    ) as mock_crawl:
        response = client.post(
            "/portfolio/crawl", json={"portfolio_url": "https://example.github.io"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_url"] == "https://example.github.io"
    assert body["section_count"] == 1
    assert body["sections"][0]["document_id"] == "sec1"
    assert body["sections"][0]["title"] == "About"
    mock_crawl.assert_called_once_with("https://example.github.io")

    stored = metadata_db.get_document_metadata("sec1")
    assert stored["filename"] == "About"
    assert stored["source_url"] == "https://example.github.io#about"
    assert stored["status"] == "crawled"


def test_crawl_github_success(tmp_path, monkeypatch):
    monkeypatch.setattr(parser, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(chunker, "CHUNKS_DIR", tmp_path / "chunks")
    monkeypatch.setattr(metadata_db, "DB_PATH", tmp_path / "metadata.db")
    monkeypatch.setattr(vector_store, "VECTOR_STORE_DIR", tmp_path / "vector_store")

    mocked_result = {
        "documents": [
            {
                "document_id": "repo1",
                "url": "https://github.com/jaw-choi/repo1",
                "title": "repo1",
                "text": "README 내용",
            }
        ],
        "failed": [{"url": "https://github.com/jaw-choi/repo2", "error": "boom"}],
    }
    with patch("app.main.crawl_github", return_value=mocked_result) as mock_crawl:
        response = client.post("/github/crawl", json={"username": "jaw-choi"})

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "jaw-choi"
    assert body["crawled_count"] == 1
    assert body["repos"][0]["document_id"] == "repo1"
    assert body["failed"] == [{"url": "https://github.com/jaw-choi/repo2", "error": "boom"}]
    mock_crawl.assert_called_once_with("jaw-choi")

    stored = metadata_db.get_document_metadata("repo1")
    assert stored["filename"] == "repo1"
    assert stored["source_url"] == "https://github.com/jaw-choi/repo1"
