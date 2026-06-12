from pathlib import Path

from cv_review_agent.storage import get_default_db_path, save_job_templates
from cv_review_agent.schemas import JobTemplate


def test_get_default_db_path_uses_env_override(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "online.sqlite3"
    monkeypatch.setenv("CV_REVIEW_DB_PATH", str(db_path))

    assert get_default_db_path() == db_path


def test_get_default_db_path_falls_back_to_local_data(monkeypatch):
    monkeypatch.delenv("CV_REVIEW_DB_PATH", raising=False)

    assert get_default_db_path() == Path("data/cv_review.sqlite3")


def test_storage_default_path_uses_runtime_env_override(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "render" / "cv_review.sqlite3"
    monkeypatch.setenv("CV_REVIEW_DB_PATH", str(db_path))

    save_job_templates(
        [
            JobTemplate(
                id="job-1",
                title="Role",
                required_conditions=["Python"],
            )
        ]
    )

    assert db_path.exists()
