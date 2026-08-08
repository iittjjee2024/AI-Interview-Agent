"""API request/response schemas for the AI Interview Agent."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Request Schemas ──────────────────────────────────────────────────────────


class StartInterviewRequest(BaseModel):
    """Request to start a new interview."""
    candidate_id: str
    config: Optional[dict[str, Any]] = None


class SubmitAnswerRequest(BaseModel):
    """Request to submit a candidate answer."""
    interview_id: str
    answer: str
    turn_id: Optional[str] = None  # idempotency key


class CompleteInterviewRequest(BaseModel):
    """Request to complete an interview."""
    interview_id: str


# ─── Response Schemas ─────────────────────────────────────────────────────────


class InterviewStartResponse(BaseModel):
    """Response after starting an interview."""
    interview_id: str
    status: str
    message: str
    question: str
    turn: int
    curriculum_days_covered: int = 0


class InterviewAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    interview_id: str
    status: str
    message: str
    turn: int
    curriculum_days_covered: int = 0
    is_complete: bool = False


class InterviewStateResponse(BaseModel):
    """Response for interview state query."""
    interview_id: str
    candidate_id: str
    status: str
    turn: int
    questions_asked: int
    curriculum_days_covered: int
    state: str
    started_at: datetime


class SkillScoreResponse(BaseModel):
    """Skill score in feedback."""
    skill: str
    score: int
    level: str
    evidence: list[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    """Complete feedback response."""
    interview_id: str
    candidate_id: str
    status: str = "completed"
    overall_score: int
    overall_level: str
    strengths: list[dict[str, Any]] = Field(default_factory=list)
    weaknesses: list[dict[str, Any]] = Field(default_factory=list)
    skill_scores: dict[str, int] = Field(default_factory=dict)
    communication_score: int = 0
    system_design_score: int = 0
    production_readiness_score: int = 0
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    detailed_feedback: str = ""
    curriculum_coverage: list[int] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str = ""
    status_code: int = 500
