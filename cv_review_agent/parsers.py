from __future__ import annotations

from pathlib import Path

from cv_review_agent.schemas import ParseResult


SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def parse_resume_file(path: Path) -> ParseResult:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return ParseResult(ok=False, error=f"Unsupported file type: {suffix}")
    if not path.exists() or path.stat().st_size == 0:
        return ParseResult(ok=False, error="Resume file is empty")

    try:
        if suffix == ".pdf":
            text = _parse_pdf(path)
        else:
            text = _parse_docx(path)
    except Exception as exc:
        return ParseResult(ok=False, error=f"Could not parse resume: {exc}")

    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not normalized:
        return ParseResult(ok=False, error="No extractable text found. OCR is not supported in v1.")
    return ParseResult(ok=True, text=normalized)


def _parse_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_docx(path: Path) -> str:
    from docx import Document

    document = Document(str(path))
    parts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(parts)
