import json

from app.core import chat_log


def test_log_chat_writes_jsonl_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(chat_log, "LOG_FILE_PATH", tmp_path / "chat.jsonl")

    chat_log.log_chat("질문", "답변", 123.4)

    lines = chat_log.LOG_FILE_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["message"] == "질문"
    assert entry["answer"] == "답변"
    assert entry["response_time_ms"] == 123.4
    assert "timestamp" in entry


def test_get_logs_returns_most_recent_entries_up_to_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(chat_log, "LOG_FILE_PATH", tmp_path / "chat.jsonl")

    for i in range(5):
        chat_log.log_chat(f"q{i}", f"a{i}", float(i))

    logs = chat_log.get_logs(limit=2)

    assert [entry["message"] for entry in logs] == ["q3", "q4"]


def test_get_logs_returns_empty_list_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(chat_log, "LOG_FILE_PATH", tmp_path / "missing.jsonl")

    assert chat_log.get_logs() == []
