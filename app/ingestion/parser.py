from pathlib import Path

import pypdf

PROCESSED_DIR = Path("data/processed")


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        raw_text = _extract_pdf_text(path)
    else:
        raw_text = path.read_text(encoding="utf-8", errors="replace")
    return clean_text(raw_text)


def _extract_pdf_text(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def clean_text(text: str) -> str:
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def save_processed_text(document_id: str, text: str) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / f"{document_id}.txt"
    output_path.write_text(text, encoding="utf-8")
    return output_path
