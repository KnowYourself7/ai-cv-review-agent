from pathlib import Path

import pytest

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
