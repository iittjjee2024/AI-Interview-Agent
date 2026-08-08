"""FastAPI dependency injection for services."""

from functools import lru_cache

from app.core.config import get_settings
from app.llm.factory import create_llm_provider
from app.memory.repositories import (
    InMemoryFeedbackRepository,
    InMemoryInterviewRepository,
)
from app.retrieval.curriculum_retriever import CurriculumRetriever
from app.services.candidate_service import CandidateService
from app.services.curriculum_service import CurriculumService
from app.services.evaluation_service import EvaluationService
from app.services.interview_service import InterviewService
from app.services.question_service import QuestionService

# Singleton instances
_interview_repo = InMemoryInterviewRepository()
_feedback_repo = InMemoryFeedbackRepository()
_curriculum_service = CurriculumService()
_candidate_service = CandidateService()
_question_service = QuestionService()
_curriculum_retriever = CurriculumRetriever()


def get_interview_service() -> InterviewService:
    """Provide the interview service with all dependencies."""
    settings = get_settings()
    llm = create_llm_provider()
    evaluation_service = EvaluationService(llm=llm)

    return InterviewService(
        llm=llm,
        interview_repo=_interview_repo,
        feedback_repo=_feedback_repo,
        curriculum_service=_curriculum_service,
        candidate_service=_candidate_service,
        question_service=_question_service,
        evaluation_service=evaluation_service,
        curriculum_retriever=_curriculum_retriever,
    )
