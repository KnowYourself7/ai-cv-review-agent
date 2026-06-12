from cv_review_agent.agent import finalize_review_result
from cv_review_agent.schemas import CandidateProfile, DimensionScores, JobScore, ReviewResult


def test_finalize_review_result_replaces_model_candidate_id_for_history():
    review = ReviewResult(
        candidate=CandidateProfile(
            id="candidate-1",
            source_filename="model.pdf",
            name="Alex Chen",
        ),
        scores=[
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
            )
        ],
    )

    finalized = finalize_review_result(
        review,
        source_filename="alex.pdf",
        resume_text="resume text",
        candidate_id="local-candidate-id",
    )

    assert finalized.candidate.id == "local-candidate-id"
    assert finalized.candidate.source_filename == "alex.pdf"
    assert finalized.candidate.raw_text == "resume text"
    assert finalized.scores[0].candidate_id == "local-candidate-id"
    assert finalized.scores[0].total_score == 80
