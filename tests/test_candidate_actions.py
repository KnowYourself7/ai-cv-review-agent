from pathlib import Path

from cv_review_agent.schemas import CandidateProfile, DimensionScores, JobScore
from cv_review_agent.storage import (
    archive_candidate,
    delete_candidate,
    load_archived_candidate_ids,
    load_candidates,
    load_resume_file,
    load_scores,
    save_candidate,
    save_resume_file,
    save_score,
    unarchive_candidate,
)


def make_candidate(candidate_id: str = "candidate-1") -> CandidateProfile:
    return CandidateProfile(
        id=candidate_id,
        source_filename="resume.pdf",
        name="Alex Chen",
        raw_text="Alex Chen Python",
    )


def make_score(candidate_id: str = "candidate-1") -> JobScore:
    return JobScore(
        candidate_id=candidate_id,
        job_id="job-1",
        dimension_scores=DimensionScores(
            required_match=8,
            relevant_experience=8,
            skills_match=8,
            achievements=8,
            education_extras=8,
        ),
        total_score=80,
    )


def test_archive_hides_candidate_until_restored(tmp_path: Path):
    db_path = tmp_path / "cv_review.sqlite3"
    save_candidate(make_candidate(), db_path=db_path)

    archive_candidate("candidate-1", db_path=db_path)

    assert load_candidates(db_path=db_path) == []
    assert [candidate.id for candidate in load_candidates(db_path=db_path, include_archived=True)] == ["candidate-1"]
    assert load_archived_candidate_ids(db_path=db_path) == {"candidate-1"}

    unarchive_candidate("candidate-1", db_path=db_path)

    assert [candidate.id for candidate in load_candidates(db_path=db_path)] == ["candidate-1"]
    assert load_archived_candidate_ids(db_path=db_path) == set()


def test_delete_candidate_removes_related_records(tmp_path: Path):
    db_path = tmp_path / "cv_review.sqlite3"
    save_candidate(make_candidate(), db_path=db_path)
    save_score(make_score(), db_path=db_path)
    save_resume_file(
        candidate_id="candidate-1",
        filename="resume.pdf",
        content_type="application/pdf",
        content=b"%PDF",
        db_path=db_path,
    )
    archive_candidate("candidate-1", db_path=db_path)

    delete_candidate("candidate-1", db_path=db_path)

    assert load_candidates(db_path=db_path, include_archived=True) == []
    assert load_scores(db_path=db_path) == []
    assert load_resume_file("candidate-1", db_path=db_path) is None
    assert load_archived_candidate_ids(db_path=db_path) == set()
