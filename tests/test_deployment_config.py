from pathlib import Path

from cv_review_agent.storage import get_default_db_path, import_database, save_job_templates
from cv_review_agent.schemas import JobTemplate


def test_hostinger_workflow_deploys_main_after_tests():
    workflow = Path(".github/workflows/deploy-hostinger.yml").read_text()

    assert "branches:\n      - main" in workflow
    assert "needs: test" in workflow
    assert "uses: appleboy/ssh-action@v1.2.0" in workflow
    assert "HOSTINGER_HOST" in workflow
    assert "APP_DIR=\"/root/apps/ai-cv-review-agent\"" in workflow
    assert "git clone https://github.com/KnowYourself7/ai-cv-review-agent.git" in workflow
    assert "git pull --ff-only origin main" in workflow
    assert "HOSTINGER_PASSWORD" in workflow
    assert "docker compose up -d --build" in workflow


def test_docker_compose_uses_persistent_server_data_dir():
    compose = Path("docker-compose.yml").read_text()

    assert "- .env.production" in compose
    assert "CV_REVIEW_DB_PATH: /var/data/cv_review.sqlite3" in compose
    assert "- ./data:/var/data" in compose


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


def test_import_database_replaces_existing_database(monkeypatch, tmp_path: Path):
    current_db = tmp_path / "current.sqlite3"
    uploaded_db = tmp_path / "uploaded.sqlite3"
    monkeypatch.setenv("CV_REVIEW_DB_PATH", str(current_db))

    save_job_templates(
        [
            JobTemplate(
                id="old-job",
                title="Old Role",
                required_conditions=["Old"],
            )
        ]
    )
    save_job_templates(
        [
            JobTemplate(
                id="new-job",
                title="New Role",
                required_conditions=["New"],
            )
        ],
        db_path=uploaded_db,
    )

    backup_path = import_database(uploaded_db.read_bytes())

    assert backup_path.exists()
    assert "before-import" in backup_path.name
    assert get_default_db_path().read_bytes() == uploaded_db.read_bytes()
