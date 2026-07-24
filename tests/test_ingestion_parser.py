import pypdf

from app.ingestion import parser


def test_extract_text_from_txt_cleans_whitespace(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("  hello world  \n\n  second line  \n", encoding="utf-8")

    result = parser.extract_text(file_path)

    assert result == "hello world\nsecond line"


def test_extract_text_from_pdf_does_not_error_on_blank_page(tmp_path):
    pdf_path = tmp_path / "doc.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with pdf_path.open("wb") as f:
        writer.write(f)

    result = parser.extract_text(pdf_path)

    assert result == ""


def test_save_processed_text_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(parser, "PROCESSED_DIR", tmp_path)

    output_path = parser.save_processed_text("doc123", "hello")

    assert output_path == tmp_path / "doc123.txt"
    assert output_path.read_text(encoding="utf-8") == "hello"
