import pytest

from app.ingestion import storage


def test_save_upload_writes_file_and_returns_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "RAW_DIR", tmp_path)

    result = storage.save_upload("notes.txt", b"hello world")

    assert result["filename"] == "notes.txt"
    assert result["size_bytes"] == len(b"hello world")
    assert result["status"] == "uploaded"
    stored_files = list(tmp_path.glob(f"{result['document_id']}.txt"))
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == b"hello world"


def test_save_upload_rejects_unsupported_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "RAW_DIR", tmp_path)

    with pytest.raises(storage.UnsupportedFileTypeError):
        storage.save_upload("malware.exe", b"data")


def test_save_upload_accepts_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "RAW_DIR", tmp_path)

    result = storage.save_upload("note.md", b"# heading\ncontent")

    assert result["status"] == "uploaded"
    stored_files = list(tmp_path.glob(f"{result['document_id']}.md"))
    assert len(stored_files) == 1
