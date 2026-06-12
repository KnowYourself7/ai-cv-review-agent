from __future__ import annotations

from typing import Iterable, List

from cv_review_agent.schemas import JobScore


WEIGHTS = {
    "required_match": 40,
    "relevant_experience": 20,
    "skills_match": 15,
    "achievements": 15,
    "education_extras": 10,
}


def apply_final_score(score: JobScore) -> JobScore:
    dimensions = score.dimension_scores
    total = 0
    for field_name, weight in WEIGHTS.items():
        total += round((getattr(dimensions, field_name) / 10) * weight)
    score.total_score = int(total)
    score.recommendation = recommendation_for(score)
    return score


def recommendation_for(score: JobScore) -> str:
    if score.disqualified:
        return "disqualified"
    if score.total_score >= 75:
        return "strong"
    if score.total_score >= 55:
        return "review"
    return "weak"


def rank_scores(scores: Iterable[JobScore]) -> List[JobScore]:
    return sorted(
        scores,
        key=lambda score: (score.disqualified, -score.total_score, score.candidate_id),
    )
