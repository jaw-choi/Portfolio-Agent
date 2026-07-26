from app.ingestion.chunker import chunk_text, save_chunks
from app.ingestion.metadata_db import save_document_metadata
from app.ingestion.parser import save_processed_text


def ingest_text(
    document_id: str,
    filename: str,
    text: str,
    status: str,
    size_bytes: int,
    source_url: str | None = None,
) -> dict:
    save_processed_text(document_id, text)

    chunks = chunk_text(document_id, text)
    save_chunks(document_id, chunks)

    save_document_metadata(
        document_id=document_id,
        filename=filename,
        size_bytes=size_bytes,
        status=status,
        text_length=len(text),
        chunk_count=len(chunks),
        source_url=source_url,
    )

    return {"text_length": len(text), "chunk_count": len(chunks)}
