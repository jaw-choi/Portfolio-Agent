from app.ingestion import metadata_db


def test_save_and_get_document_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(metadata_db, "DB_PATH", tmp_path / "metadata.db")

    metadata_db.save_document_metadata(
        document_id="doc1",
        filename="notes.txt",
        size_bytes=11,
        status="uploaded",
        text_length=11,
        chunk_count=1,
    )

    record = metadata_db.get_document_metadata("doc1")

    assert record["document_id"] == "doc1"
    assert record["filename"] == "notes.txt"
    assert record["size_bytes"] == 11
    assert record["status"] == "uploaded"
    assert record["text_length"] == 11
    assert record["chunk_count"] == 1
    assert record["uploaded_at"] is not None


def test_get_document_metadata_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(metadata_db, "DB_PATH", tmp_path / "metadata.db")

    assert metadata_db.get_document_metadata("missing") is None


def test_save_document_metadata_upserts_existing_id(tmp_path, monkeypatch):
    monkeypatch.setattr(metadata_db, "DB_PATH", tmp_path / "metadata.db")

    metadata_db.save_document_metadata(
        document_id="doc1",
        filename="v1.txt",
        size_bytes=5,
        status="uploaded",
        text_length=5,
        chunk_count=1,
    )
    metadata_db.save_document_metadata(
        document_id="doc1",
        filename="v2.txt",
        size_bytes=8,
        status="uploaded",
        text_length=8,
        chunk_count=2,
    )

    records = metadata_db.list_documents()

    assert len(records) == 1
    assert records[0]["filename"] == "v2.txt"


def test_database_url_env_var_overrides_db_path(tmp_path, monkeypatch):
    alt_db_path = tmp_path / "alt.db"
    unused_db_path = tmp_path / "should_not_be_used.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{alt_db_path}")
    monkeypatch.setattr(metadata_db, "DB_PATH", unused_db_path)

    metadata_db.save_document_metadata(
        document_id="doc1",
        filename="a.txt",
        size_bytes=1,
        status="uploaded",
        text_length=1,
        chunk_count=1,
    )

    assert alt_db_path.exists()
    assert not unused_db_path.exists()


def test_list_documents_orders_most_recent_first(tmp_path, monkeypatch):
    monkeypatch.setattr(metadata_db, "DB_PATH", tmp_path / "metadata.db")

    metadata_db.save_document_metadata(
        document_id="doc1",
        filename="first.txt",
        size_bytes=1,
        status="uploaded",
        text_length=1,
        chunk_count=1,
    )
    metadata_db.save_document_metadata(
        document_id="doc2",
        filename="second.txt",
        size_bytes=1,
        status="uploaded",
        text_length=1,
        chunk_count=1,
    )

    records = metadata_db.list_documents()

    assert [r["document_id"] for r in records] == ["doc2", "doc1"]
