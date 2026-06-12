from __future__ import annotations

import csv
import io
import json
from typing import Dict, Iterable

from cv_review_agent.schemas import CandidateProfile, JobScore, JobTemplate


def export_scores_csv(
    scores: Iterable[JobScore],
    candidates: Dict[str, CandidateProfile],
    jobs: Dict[str, JobTemplate],
) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "job_title",
            "candidate_name",
            "total_score",
            "recommendation",
            "disqualified",
            "needs_human_review",
            "strengths",
            "gaps",
            "risks",
        ],
    )
    writer.writeheader()
    for score in scores:
        candidate = candidates[score.candidate_id]
        job = jobs[score.job_id]
        writer.writerow(
            {
                "job_title": job.title,
                "candidate_name": candidate.name,
                "total_score": score.total_score,
                "recommendation": score.recommendation,
                "disqualified": score.disqualified,
                "needs_human_review": score.needs_human_review,
                "strengths": "; ".join(score.strengths),
                "gaps": "; ".join(score.gaps),
                "risks": "; ".join(score.risks),
            }
        )
    return output.getvalue()


def export_scores_json(
    scores: Iterable[JobScore],
    candidates: Dict[str, CandidateProfile],
    jobs: Dict[str, JobTemplate],
) -> str:
    results = []
    for score in scores:
        results.append(
            {
                "candidate": _dump_model(candidates[score.candidate_id]),
                "job": _dump_model(jobs[score.job_id]),
                "score": _dump_model(score),
            }
        )
    return json.dumps({"results": results}, ensure_ascii=False, indent=2)


def _dump_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
