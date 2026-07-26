from pathlib import Path

from sqlalchemy import Column, DateTime, Integer, String, create_engine, func, text
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = Path("data/metadata.db")

Base = declarative_base()


class DocumentMetadata(Base):
    __tablename__ = "documents"

    document_id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    text_length = Column(Integer, nullable=False)
    chunk_count = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


def _get_session():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def save_document_metadata(
    document_id: str,
    filename: str,
    size_bytes: int,
    status: str,
    text_length: int,
    chunk_count: int,
) -> None:
    with _get_session() as session:
        session.merge(
            DocumentMetadata(
                document_id=document_id,
                filename=filename,
                size_bytes=size_bytes,
                status=status,
                text_length=text_length,
                chunk_count=chunk_count,
            )
        )
        session.commit()


def get_document_metadata(document_id: str) -> dict | None:
    with _get_session() as session:
        record = session.get(DocumentMetadata, document_id)
        return _to_dict(record) if record else None


def list_documents() -> list[dict]:
    with _get_session() as session:
        records = (
            session.query(DocumentMetadata)
            .order_by(text("rowid DESC"))
            .all()
        )
        return [_to_dict(record) for record in records]


def _to_dict(record: DocumentMetadata) -> dict:
    return {
        "document_id": record.document_id,
        "filename": record.filename,
        "size_bytes": record.size_bytes,
        "status": record.status,
        "text_length": record.text_length,
        "chunk_count": record.chunk_count,
        "uploaded_at": record.uploaded_at.isoformat() if record.uploaded_at else None,
    }
