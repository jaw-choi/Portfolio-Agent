import json
from pathlib import Path

CONVERSATIONS_DIR = Path("data/conversations")


def append_turn(conversation_id: str, role: str, content: str) -> None:
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = CONVERSATIONS_DIR / f"{conversation_id}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"role": role, "content": content}, ensure_ascii=False) + "\n")


def get_history(conversation_id: str) -> list[dict]:
    path = CONVERSATIONS_DIR / f"{conversation_id}.jsonl"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
