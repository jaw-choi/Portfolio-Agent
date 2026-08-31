from app.ingestion import chunker, metadata_db, parser, seed, storage
from app.ingestion.pipeline import ingest_text
from app.ingestion.seed import seed_sample_documents
from app.retrieval import vector_store


def _patch_data_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(parser, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(chunker, "CHUNKS_DIR", tmp_path / "chunks")
    monkeypatch.setattr(metadata_db, "DB_PATH", tmp_path / "metadata.db")
    monkeypatch.setattr(vector_store, "VECTOR_STORE_DIR", tmp_path / "vector_store")


def test_seed_sample_documents_populates_empty_store(tmp_path, monkeypatch):
    _patch_data_dirs(tmp_path, monkeypatch)
    samples_dir = tmp_path / "samples"
    samples_dir.mkdir()
    (samples_dir / "note_a.md").write_text("싱글톤 패턴 노트", encoding="utf-8")
    (samples_dir / "note_b.md").write_text("데이터 파이프라인 노트", encoding="utf-8")
    monkeypatch.setattr(seed, "SAMPLES_DIR", samples_dir)

    seeded = seed_sample_documents()

    assert seeded == 2
    documents = metadata_db.list_documents()
    assert {doc["filename"] for doc in documents} == {"note_a.md", "note_b.md"}
    assert all(doc["status"] == "uploaded" for doc in documents)


def test_seed_sample_documents_skips_when_store_not_empty(tmp_path, monkeypatch):
    _patch_data_dirs(tmp_path, monkeypatch)
    samples_dir = tmp_path / "samples"
    samples_dir.mkdir()
    (samples_dir / "note_a.md").write_text("싱글톤 패턴 노트", encoding="utf-8")
    monkeypatch.setattr(seed, "SAMPLES_DIR", samples_dir)

    ingest_text(
        document_id="existing-doc",
        filename="existing.md",
        text="기존 문서",
        status="uploaded",
        size_bytes=10,
    )

    seeded = seed_sample_documents()

    assert seeded == 0
    documents = metadata_db.list_documents()
    assert [doc["filename"] for doc in documents] == ["existing.md"]


def test_seed_sample_documents_noop_when_samples_dir_missing(tmp_path, monkeypatch):
    _patch_data_dirs(tmp_path, monkeypatch)
    monkeypatch.setattr(seed, "SAMPLES_DIR", tmp_path / "no_such_dir")

    seeded = seed_sample_documents()

    assert seeded == 0
    assert metadata_db.list_documents() == []
