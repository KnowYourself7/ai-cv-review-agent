import json

from cv_review_agent.export import export_scores_csv, export_scores_json
from cv_review_agent.schemas import CandidateProfile, DimensionScores, JobScore, JobTemplate
from cv_review_agent.scoring import apply_final_score


def make_candidate() -> CandidateProfile:
    return CandidateProfile(
        id="candidate-1",
        source_filename="resume.pdf",
        name="Alex Chen",
        contact_summary="email present",
        skills=["Python"],
        experience=["Built review workflow"],
        education=[],
        projects=[],
        certifications=[],
        estimated_years=4,
        evidence_snippets=["Built review workflow"],
        raw_text="Alex Chen Python",
    )


def make_job() -> JobTemplate:
    return JobTemplate(
        id="job-1",
        title="AI Engineer",
        required_conditions=["Python"],
        bonus_conditions=[],
        responsibilities=[],
        minimum_years=3,
        disqualifiers=[],
        notes="",
    )


def make_score() -> JobScore:
    return apply_final_score(
        JobScore(
            candidate_id="candidate-1",
            job_id="job-1",
            dimension_scores=DimensionScores(
                required_match=8,
                relevant_experience=8,
                skills_match=8,
                achievements=8,
                education_extras=8,
            ),
            disqualified=False,
            strengths=["Strong Python"],
            gaps=[],
            risks=[],
            evidence=["Python listed"],
            needs_human_review=False,
        )
    )


def test_export_scores_csv_contains_screening_columns():
    csv_text = export_scores_csv([make_score()], {"candidate-1": make_candidate()}, {"job-1": make_job()})

    assert "job_title,candidate_name,total_score,recommendation,disqualified" in csv_text
    assert "AI Engineer,Alex Chen,80,strong,False" in csv_text


def test_export_scores_json_preserves_full_review_details():
    payload = json.loads(export_scores_json([make_score()], {"candidate-1": make_candidate()}, {"job-1": make_job()}))

    assert payload["results"][0]["candidate"]["name"] == "Alex Chen"
    assert payload["results"][0]["job"]["title"] == "AI Engineer"
    assert payload["results"][0]["score"]["evidence"] == ["Python listed"]
