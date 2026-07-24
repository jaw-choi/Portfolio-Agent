import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE_PATH = Path("logs/chat.jsonl")


def log_chat(message: str, answer: str, response_time_ms: float) -> None:
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message,
        "answer": answer,
        "response_time_ms": response_time_ms,
    }
    with LOG_FILE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_logs(limit: int = 20) -> list[dict]:
    if not LOG_FILE_PATH.exists():
        return []
    with LOG_FILE_PATH.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines[-limit:]]
