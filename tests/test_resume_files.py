from pathlib import Path

from cv_review_agent.storage import load_resume_file, save_resume_file


def test_save_and_load_resume_file_round_trips_original_bytes(tmp_path: Path):
    db_path = tmp_path / "cv_review.sqlite3"

    save_resume_file(
        candidate_id="candidate-1",
        filename="resume.pdf",
        content_type="application/pdf",
        content=b"%PDF sample",
        db_path=db_path,
    )

    stored = load_resume_file("candidate-1", db_path=db_path)

    assert stored is not None
    assert stored.candidate_id == "candidate-1"
    assert stored.filename == "resume.pdf"
    assert stored.content_type == "application/pdf"
    assert stored.content == b"%PDF sample"
    assert stored.uploaded_at


def test_load_resume_file_returns_none_when_missing(tmp_path: Path):
    db_path = tmp_path / "cv_review.sqlite3"

    stored = load_resume_file("missing", db_path=db_path)

    assert stored is None
