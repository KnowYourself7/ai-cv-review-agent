from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ParseResult(BaseModel):
    ok: bool
    text: str = ""
    error: Optional[str] = None


class JobTemplate(BaseModel):
    id: str
    title: str
    required_conditions: List[str] = Field(default_factory=list)
    bonus_conditions: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    minimum_years: int = 0
    disqualifiers: List[str] = Field(default_factory=list)
    notes: str = ""

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Job title is required")
        return value.strip()


class CandidateProfile(BaseModel):
    id: str
    source_filename: str
    name: str = "Unknown"
    contact_summary: str = ""
    skills: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    estimated_years: Optional[float] = None
    evidence_snippets: List[str] = Field(default_factory=list)
    raw_text: str = ""


class ResumeFile(BaseModel):
    candidate_id: str
    filename: str
    content_type: str
    content: bytes
    uploaded_at: str


class DimensionScores(BaseModel):
    required_match: int = Field(ge=0, le=10)
    relevant_experience: int = Field(ge=0, le=10)
    skills_match: int = Field(ge=0, le=10)
    achievements: int = Field(ge=0, le=10)
    education_extras: int = Field(ge=0, le=10)


class JobScore(BaseModel):
    candidate_id: str
    job_id: str
    dimension_scores: DimensionScores
    total_score: int = 0
    recommendation: str = "review"
    disqualified: bool = False
    disqualification_reasons: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    needs_human_review: bool = False


class ReviewResult(BaseModel):
    candidate: CandidateProfile
    scores: List[JobScore]
