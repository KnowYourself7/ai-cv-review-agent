from cv_review_agent.schemas import DimensionScores, JobScore
from cv_review_agent.scoring import apply_final_score, rank_scores


def make_score(candidate_id: str, disqualified: bool = False) -> JobScore:
    return JobScore(
        candidate_id=candidate_id,
        job_id="job-1",
        dimension_scores=DimensionScores(
            required_match=8,
            relevant_experience=7,
            skills_match=6,
            achievements=5,
            education_extras=4,
        ),
        disqualified=disqualified,
        strengths=[],
        gaps=[],
        risks=[],
        evidence=[],
        needs_human_review=False,
    )


def test_apply_final_score_uses_fixed_weights():
    score = apply_final_score(make_score("candidate-1"))

    assert score.total_score == 67
    assert score.recommendation == "review"


def test_rank_scores_keeps_disqualified_candidates_below_qualified():
    qualified = apply_final_score(make_score("qualified"))
    disqualified = apply_final_score(make_score("disqualified", disqualified=True))
    disqualified.total_score = 100

    ranked = rank_scores([disqualified, qualified])

    assert [score.candidate_id for score in ranked] == ["qualified", "disqualified"]
