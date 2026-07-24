import uuid
from pathlib import Path

RAW_DIR = Path("data/raw")
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


class UnsupportedFileTypeError(Exception):
    """지원하지 않는 파일 확장자일 때 발생하는 예외."""


def save_upload(filename: str, content: bytes) -> dict:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"지원하지 않는 파일 형식입니다: {extension or '(확장자 없음)'} "
            f"(허용: {', '.join(sorted(ALLOWED_EXTENSIONS))})"
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    document_id = uuid.uuid4().hex
    stored_path = RAW_DIR / f"{document_id}{extension}"
    stored_path.write_bytes(content)

    return {
        "document_id": document_id,
        "filename": filename,
        "size_bytes": len(content),
        "status": "uploaded",
        "path": stored_path,
    }
