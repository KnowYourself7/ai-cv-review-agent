from __future__ import annotations

import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from cv_review_agent.schemas import CandidateProfile, JobScore, JobTemplate, ResumeFile


LOCAL_DB_PATH = Path("data/cv_review.sqlite3")
REQUIRED_TABLES = {"job_templates", "candidates", "scores", "resume_files"}


def get_default_db_path() -> Path:
    configured_path = os.getenv("CV_REVIEW_DB_PATH", "").strip()
    if configured_path:
        return Path(configured_path)
    return LOCAL_DB_PATH


def validate_template_limit(templates: Iterable[JobTemplate]) -> None:
    count = len(list(templates))
    if count < 1 or count > 3:
        raise ValueError("Expected 1 to 3 job templates")


def init_db(db_path: Path | None = None) -> None:
    db_path = db_path or get_default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_templates (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                candidate_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (candidate_id, job_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resume_files (
                candidate_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content BLOB NOT NULL,
                uploaded_at TEXT NOT NULL
            )
            """
        )


def import_database(content: bytes, db_path: Path | None = None) -> Path:
    db_path = db_path or get_default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = db_path.with_suffix(f"{db_path.suffix}.upload")
    backup_path = db_path.with_name(
        f"{db_path.stem}.before-import-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{db_path.suffix}"
    )
    temp_path.write_bytes(content)
    try:
        _validate_import_database(temp_path)
        if db_path.exists():
            shutil.copy2(db_path, backup_path)
        else:
            backup_path.write_bytes(b"")
        temp_path.replace(db_path)
        return backup_path
    finally:
        temp_path.unlink(missing_ok=True)


def _validate_import_database(db_path: Path) -> None:
    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    except sqlite3.DatabaseError as exc:
        raise ValueError("Uploaded file is not a valid SQLite database") from exc
    missing = REQUIRED_TABLES - {row[0] for row in rows}
    if missing:
        raise ValueError("Uploaded database is missing required CV review tables")


def save_job_templates(templates: List[JobTemplate], db_path: Path | None = None) -> None:
    db_path = db_path or get_default_db_path()
    validate_template_limit(templates)
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM job_templates")
        conn.executemany(
            "INSERT INTO job_templates (id, payload) VALUES (?, ?)",
            [(template.id, json.dumps(_dump_model(template))) for template in templates],
        )


def load_job_templates(db_path: Path | None = None) -> List[JobTemplate]:
    db_path = db_path or get_default_db_path()
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT payload FROM job_templates ORDER BY id").fetchall()
    return [JobTemplate.model_validate_json(row[0]) for row in rows]


def save_candidate(candidate: CandidateProfile, db_path: Path | None = None) -> None:
    db_path = db_path or get_default_db_path()
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO candidates (id, payload) VALUES (?, ?)",
            (candidate.id, json.dumps(_dump_model(candidate))),
        )


def load_candidates(db_path: Path | None = None) -> List[CandidateProfile]:
    db_path = db_path or get_default_db_path()
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT payload FROM candidates ORDER BY id").fetchall()
    return [CandidateProfile.model_validate_json(row[0]) for row in rows]


def save_score(score: JobScore, db_path: Path | None = None) -> None:
    db_path = db_path or get_default_db_path()
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO scores (candidate_id, job_id, payload) VALUES (?, ?, ?)",
            (score.candidate_id, score.job_id, json.dumps(_dump_model(score))),
        )


def load_scores(db_path: Path | None = None) -> List[JobScore]:
    db_path = db_path or get_default_db_path()
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT payload FROM scores ORDER BY job_id, candidate_id").fetchall()
    return [JobScore.model_validate_json(row[0]) for row in rows]


def save_resume_file(
    candidate_id: str,
    filename: str,
    content_type: str,
    content: bytes,
    db_path: Path | None = None,
) -> None:
    db_path = db_path or get_default_db_path()
    init_db(db_path)
    uploaded_at = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO resume_files
                (candidate_id, filename, content_type, content, uploaded_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (candidate_id, filename, content_type, content, uploaded_at),
        )


def load_resume_file(candidate_id: str, db_path: Path | None = None) -> Optional[ResumeFile]:
    db_path = db_path or get_default_db_path()
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT candidate_id, filename, content_type, content, uploaded_at
            FROM resume_files
            WHERE candidate_id = ?
            """,
            (candidate_id,),
        ).fetchone()
    if row is None:
        return None
    return ResumeFile(
        candidate_id=row[0],
        filename=row[1],
        content_type=row[2],
        content=row[3],
        uploaded_at=row[4],
    )


def _dump_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
