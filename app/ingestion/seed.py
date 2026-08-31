from pathlib import Path

from app.ingestion.metadata_db import list_documents
from app.ingestion.parser import extract_text
from app.ingestion.pipeline import ingest_text
from app.ingestion.storage import save_upload

SAMPLES_DIR = Path("data/samples")


def seed_sample_documents() -> int:
    """비어 있는 문서 저장소를 data/samples/의 샘플 노트로 채운다.

    data/는 gitignore 대상이라 새로 clone한 환경은 검색할 문서가 0개다 --
    리뷰어가 채팅 UI를 열자마자 빈 검색 결과만 보는 것을 막기 위한 1회성 자동 시딩.
    이미 문서가 하나라도 있으면(기존 로컬 데이터가 있는 환경) 아무 것도 하지 않는다.
    """
    if list_documents():
        return 0

    if not SAMPLES_DIR.is_dir():
        return 0

    seeded = 0
    for sample_path in sorted(SAMPLES_DIR.glob("*.md")):
        content = sample_path.read_bytes()
        result = save_upload(sample_path.name, content)
        text = extract_text(result["path"])
        ingest_text(
            document_id=result["document_id"],
            filename=result["filename"],
            text=text,
            status=result["status"],
            size_bytes=result["size_bytes"],
        )
        seeded += 1

    return seeded
