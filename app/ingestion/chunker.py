import json
from pathlib import Path

CHUNKS_DIR = Path("data/chunks")

DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 50


def chunk_text(
    document_id: str,
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[dict]:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    index = 0
    while start < len(words):
        end = start
        length = 0
        while end < len(words) and length < chunk_size:
            length += len(words[end]) + 1
            end += 1

        chunks.append(
            {
                "chunk_id": f"{document_id}_{index}",
                "document_id": document_id,
                "chunk_index": index,
                "text": " ".join(words[start:end]),
            }
        )
        index += 1

        if end >= len(words):
            break

        overlap_len = 0
        overlap_start = end
        while overlap_start > start and overlap_len < overlap:
            overlap_start -= 1
            overlap_len += len(words[overlap_start]) + 1
        start = overlap_start

    return chunks


def save_chunks(document_id: str, chunks: list[dict]) -> Path:
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CHUNKS_DIR / f"{document_id}.json"
    output_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
