from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List

from cv_review_agent.schemas import CandidateProfile, JobTemplate, ReviewResult
from cv_review_agent.scoring import apply_final_score


SYSTEM_INSTRUCTIONS = """
You review resumes for job fit. Extract only evidence present in the resume.
Do not infer or score protected or job-irrelevant traits such as age, gender,
race, marital status, family status, photo, nationality, hometown, or religion.
If evidence is missing, say that it was not found. The output supports human
screening and must not claim to make a final hiring decision.
"""


async def review_resume_text(
    resume_text: str,
    source_filename: str,
    job_templates: List[JobTemplate],
) -> ReviewResult:
    _load_local_openai_key()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required to run AI review")
    if not job_templates:
        raise ValueError("At least one job template is required")

    from agents import Agent, Runner

    agent = Agent(
        name="CV Review Agent",
        instructions=SYSTEM_INSTRUCTIONS,
        output_type=ReviewResult,
    )
    prompt = _build_prompt(resume_text, source_filename, job_templates)
    result = await Runner.run(agent, prompt)
    review = _coerce_review_result(result.final_output)
    return finalize_review_result(review, source_filename, resume_text)


def finalize_review_result(
    review: ReviewResult,
    source_filename: str,
    resume_text: str,
    candidate_id: str | None = None,
) -> ReviewResult:
    local_candidate_id = candidate_id or str(uuid.uuid4())
    review.candidate.id = local_candidate_id
    review.candidate.source_filename = source_filename
    review.candidate.raw_text = resume_text
    for score in review.scores:
        score.candidate_id = local_candidate_id
    review.scores = [apply_final_score(score) for score in review.scores]
    return review


def _build_prompt(resume_text: str, source_filename: str, job_templates: List[JobTemplate]) -> str:
    jobs = "\n\n".join(template.model_dump_json(indent=2) for template in job_templates)
    return f"""
Source filename: {source_filename}

Job templates:
{jobs}

Resume text:
{resume_text}

Return one candidate profile and one score for each job template.
Use the exact job IDs provided. Use dimension scores from 0 to 10 only.
"""


def _coerce_review_result(value) -> ReviewResult:
    if isinstance(value, ReviewResult):
        return value
    return ReviewResult.model_validate(value)


def _load_local_openai_key() -> None:
    if os.getenv("OPENAI_API_KEY"):
        return
    env_path = Path(".env.local")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "OPENAI_API_KEY" and value.strip():
            os.environ["OPENAI_API_KEY"] = value.strip().strip('"').strip("'")
            return
