from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_success():
    mocked = {"answer": "안녕하세요!", "reason": "인사에 대한 응답", "sources": []}
    with patch("app.main.get_completion", return_value=mocked):
        response = client.post("/chat", json={"message": "안녕하세요"})

    assert response.status_code == 200
    assert response.json() == mocked


def test_chat_input_error():
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_server_error():
    with patch("app.main.get_completion", side_effect=RuntimeError("LLM failure")):
        response = client.post("/chat", json={"message": "안녕하세요"})

    assert response.status_code == 500
    assert "LLM failure" in response.json()["detail"]
