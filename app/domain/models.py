"""Domain models for the AI Interview Agent."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.domain.enums import (
    AnswerQuality,
    DifficultyLevel,
    FollowUpStrategy,
    InterviewState,
    InterviewStatus,
    PerformanceLevel,
    QuestionType,
    SkillDimension,
)


# ─── Curriculum Models ────────────────────────────────────────────────────────


class CurriculumDay(BaseModel):
    """Represents a single day in the curriculum."""
    day: int
    module: str
    topic: str
    subtopics: list[str] = Field(default_factory=list)
    learning_objectives: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    difficulty: str = "intermediate"
    prerequisites: list[int] = Field(default_factory=list)
    expected_skills: list[str] = Field(default_factory=list)


class Curriculum(BaseModel):
    """Complete curriculum data."""
    days: list[CurriculumDay]

    def get_day(self, day_number: int) -> Optional[CurriculumDay]:
        for d in self.days:
            if d.day == day_number:
                return d
        return None

    def get_all_concepts(self) -> list[str]:
        concepts = []
        for d in self.days:
            concepts.extend(d.concepts)
        return list(set(concepts))

    def get_days_for_concept(self, concept: str) -> list[int]:
        return [d.day for d in self.days if concept.lower() in [c.lower() for c in d.concepts]]


# ─── Candidate Models ─────────────────────────────────────────────────────────


class MissionAttempt(BaseModel):
    """A candidate's attempt at a mission/task."""
    day: int
    mission: str
    status: str  # completed, failed, partial
    score: Optional[float] = None
    attempts: int = 1


class LearningSignal(BaseModel):
    """A signal about the candidate's learning."""
    concept: str
    signal_type: str  # strong, weak, confused, improving
    evidence: str = ""
    day: int = 0


class CandidateProfile(BaseModel):
    """Represents a candidate's profile and learning history."""
    candidate_id: str
    name: str = ""
    completed_missions: list[MissionAttempt] = Field(default_factory=list)
    skipped_topics: list[int] = Field(default_factory=list)
    learning_signals: list[LearningSignal] = Field(default_factory=list)
    performance: dict[str, float] = Field(default_factory=dict)
    projects: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)


# ─── Question Models ──────────────────────────────────────────────────────────


class QuestionPlan(BaseModel):
    """Internal plan for what question to ask next."""
    curriculum_day: int
    concept: str
    skill_dimension: SkillDimension
    difficulty: int = Field(ge=1, le=5)
    question_type: QuestionType
    rationale: str
    expected_evidence: list[str] = Field(default_factory=list)
    follow_up_strategy: FollowUpStrategy = FollowUpStrategy.DEEPEN


class GeneratedQuestion(BaseModel):
    """A generated interview question."""
    question_id: str
    question_text: str
    curriculum_day: int
    concept: str
    skill_dimension: SkillDimension
    difficulty: int = Field(ge=1, le=5)
    question_type: QuestionType
    expected_evidence: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Evaluation Models ────────────────────────────────────────────────────────


class AnswerEvaluation(BaseModel):
    """Evaluation of a candidate's answer."""
    question_id: str
    quality: AnswerQuality
    correctness: float = Field(ge=0.0, le=1.0)
    technical_depth: float = Field(ge=0.0, le=1.0)
    reasoning: float = Field(ge=0.0, le=1.0)
    communication: float = Field(ge=0.0, le=1.0)
    production_awareness: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    missing_concepts: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    recommended_next_action: FollowUpStrategy = FollowUpStrategy.DEEPEN


class Claim(BaseModel):
    """A technical claim made by the candidate."""
    claim: str
    concept: str
    status: str = "unverified"  # unverified, verified, questionable, incorrect
    evidence_needed: bool = False
    detected_at_turn: int = 0


class Misconception(BaseModel):
    """A detected misconception."""
    concept: str
    misconception: str
    severity: str = "medium"  # low, medium, high
    detected_at_turn: int = 0
    revisited: bool = False


# ─── Interview State Models ───────────────────────────────────────────────────


class CoverageState(BaseModel):
    """Tracks interview coverage."""
    curriculum_days_covered: list[int] = Field(default_factory=list)
    concepts_covered: list[str] = Field(default_factory=list)
    skill_dimensions_covered: list[SkillDimension] = Field(default_factory=list)
    questions_by_day: dict[int, int] = Field(default_factory=dict)
    questions_by_concept: dict[str, int] = Field(default_factory=dict)


class InterviewMemory(BaseModel):
    """Structured interview memory maintained across turns."""
    candidate_summary: str = ""
    topics_discussed: list[str] = Field(default_factory=list)
    strengths_detected: list[str] = Field(default_factory=list)
    weaknesses_detected: list[str] = Field(default_factory=list)
    misconceptions: list[Misconception] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    projects_mentioned: list[str] = Field(default_factory=list)
    questions_asked: list[GeneratedQuestion] = Field(default_factory=list)
    answers: list[dict[str, Any]] = Field(default_factory=list)
    evaluations: list[AnswerEvaluation] = Field(default_factory=list)
    skill_scores: dict[str, float] = Field(default_factory=dict)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    coverage: CoverageState = Field(default_factory=CoverageState)
    current_topic: str = ""
    current_difficulty: int = 3
    interview_phase: InterviewState = InterviewState.INITIALIZING


class InterviewSession(BaseModel):
    """Complete interview session state."""
    interview_id: str
    candidate_id: str
    status: InterviewStatus = InterviewStatus.IN_PROGRESS
    state: InterviewState = InterviewState.INITIALIZING
    state_version: int = 0
    turn: int = 0
    memory: InterviewMemory = Field(default_factory=InterviewMemory)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    config: dict[str, Any] = Field(default_factory=dict)


# ─── Feedback Models ──────────────────────────────────────────────────────────


class SkillFeedback(BaseModel):
    """Feedback for a specific skill."""
    skill: str
    score: int = Field(ge=0, le=100)
    level: PerformanceLevel
    evidence: list[str] = Field(default_factory=list)


class StrengthWeakness(BaseModel):
    """A detected strength or weakness."""
    area: str
    description: str
    evidence: list[str] = Field(default_factory=list)
    curriculum_days: list[int] = Field(default_factory=list)


class StudyRecommendation(BaseModel):
    """A recommended study topic."""
    curriculum_day: int
    topic: str
    reason: str
    priority: str = "medium"  # low, medium, high


class InterviewFeedback(BaseModel):
    """Complete interview feedback report."""
    interview_id: str
    candidate_id: str
    overall_score: int = Field(ge=0, le=100)
    overall_level: PerformanceLevel
    strengths: list[StrengthWeakness] = Field(default_factory=list)
    weaknesses: list[StrengthWeakness] = Field(default_factory=list)
    skill_scores: dict[str, int] = Field(default_factory=dict)
    communication_score: int = Field(ge=0, le=100)
    system_design_score: int = Field(ge=0, le=100)
    production_readiness_score: int = Field(ge=0, le=100)
    recommendations: list[StudyRecommendation] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    curriculum_coverage: list[int] = Field(default_factory=list)
    summary: str = ""
    detailed_feedback: str = ""
