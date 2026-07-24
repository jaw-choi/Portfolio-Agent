from unittest.mock import patch

from fastapi.testclient import TestClient

from app.ingestion import storage
from app.main import app

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
    monkeypatch.setattr(storage, "RAW_DIR", tmp_path)

    response = client.post(
        "/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "notes.txt"
    assert body["size_bytes"] == 5
    assert body["status"] == "uploaded"


def test_upload_document_rejects_unsupported_type():
    response = client.post(
        "/documents",
        files={"file": ("virus.exe", b"data", "application/octet-stream")},
    )

    assert response.status_code == 400
