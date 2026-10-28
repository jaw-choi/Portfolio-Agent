import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE_PATH = Path("logs/search.jsonl")


def log_search(
    query: str, top_k: int, results: list[dict], response_time_ms: float
) -> None:
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "top_k": top_k,
        "result_count": len(results),
        "results": [
            {
                "chunk_id": result["chunk_id"],
                "document_id": result["document_id"],
                "filename": result["filename"],
                "source_url": result["source_url"],
                "similarity": result["similarity"],
            }
            for result in results
        ],
        "response_time_ms": response_time_ms,
    }
    with LOG_FILE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
