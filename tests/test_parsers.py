from pathlib import Path

import pytest

from cv_review_agent import parsers
from cv_review_agent.parsers import parse_resume_file


def test_parse_resume_file_rejects_unsupported_extension(tmp_path: Path):
    resume = tmp_path / "resume.txt"
    resume.write_text("plain text", encoding="utf-8")

    result = parse_resume_file(resume)

    assert not result.ok
    assert "Unsupported" in result.error


def test_parse_resume_file_rejects_empty_supported_file(tmp_path: Path):
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"")

    result = parse_resume_file(resume)

    assert not result.ok
    assert "empty" in result.error.lower()


def test_parse_resume_file_rejects_gibberish_extracted_text(monkeypatch, tmp_path: Path):
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"%PDF sample")
    gibberish = "\n".join(["3d89dcd70a5a26041HF529m0FVFYw4W2VP-YWOGkmf7YMBRk3g~~"] * 12)
    monkeypatch.setattr(parsers, "_parse_pdf", lambda path: gibberish)

    result = parse_resume_file(resume)

    assert not result.ok
    assert "readable resume text" in result.error


def test_parse_resume_file_accepts_readable_resume_text(monkeypatch, tmp_path: Path):
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"%PDF sample")
    readable_text = """
    Resume
    Name: Alex Chen
    Email: alex@example.com
    Education: Bachelor of Business English
    Experience: Cross-border ecommerce operations internship with customer emails, product pages, and order tracking.
    Skills: English writing, SEO content, data reporting, AI prompt workflow interest.
    """
    monkeypatch.setattr(parsers, "_parse_pdf", lambda path: readable_text)

    result = parse_resume_file(resume)

    assert result.ok
    assert "Alex Chen" in result.text
