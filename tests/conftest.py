"""Test configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.models import (
    CandidateProfile,
    Curriculum,
    CurriculumDay,
    MissionAttempt,
    LearningSignal,
)
from app.llm.base import LLMProvider, LLMResponse
from app.memory.repositories import InMemoryInterviewRepository, InMemoryFeedbackRepository


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    provider = AsyncMock(spec=LLMProvider)
    provider.generate = AsyncMock(return_value=LLMResponse(
        content="Let's start. Walk me through the RAG system you built during the cohort.",
        model="test-model",
        tokens_used=50,
    ))
    provider.structured_generate = AsyncMock()
    return provider


@pytest.fixture
def sample_curriculum():
    """Create a sample curriculum for testing."""
    return Curriculum(days=[
        CurriculumDay(
            day=1, module="Foundations", topic="AI Engineering",
            concepts=["AI engineering", "LLMs"],
            learning_objectives=["Understand AI engineering"],
            tools=["Python"], projects=["Analysis"],
            difficulty="beginner", expected_skills=["Explain AI role"],
        ),
        CurriculumDay(
            day=7, module="Retrieval", topic="RAG Fundamentals",
            concepts=["RAG", "Retrieval-augmented generation"],
            learning_objectives=["Build RAG pipeline"],
            tools=["LangChain"], projects=["Basic RAG"],
            difficulty="intermediate", expected_skills=["Build RAG"],
        ),
        CurriculumDay(
            day=10, module="Agents", topic="AI Agents",
            concepts=["AI agents", "Tool use"],
            learning_objectives=["Build agents"],
            tools=["LangChain Agents"], projects=["ReAct agent"],
            difficulty="intermediate", expected_skills=["Build agents"],
        ),
        CurriculumDay(
            day=18, module="Production", topic="AI Deployment",
            concepts=["Deployment", "Docker"],
            learning_objectives=["Deploy AI apps"],
            tools=["Docker"], projects=["Pipeline"],
            difficulty="advanced", expected_skills=["Deploy apps"],
        ),
        CurriculumDay(
            day=21, module="Production", topic="Security",
            concepts=["AI security", "Prompt injection"],
            learning_objectives=["Secure AI systems"],
            tools=["Guardrails"], projects=["Security"],
            difficulty="advanced", expected_skills=["Secure systems"],
        ),
    ])


@pytest.fixture
def sample_candidate():
    """Create a sample candidate profile."""
    return CandidateProfile(
        candidate_id="test_001",
        name="Test User",
        completed_missions=[
            MissionAttempt(day=1, mission="Analysis", status="completed", score=0.9),
            MissionAttempt(day=7, mission="RAG", status="completed", score=0.85),
            MissionAttempt(day=10, mission="Agent", status="completed", score=0.7),
            MissionAttempt(day=18, mission="Deploy", status="partial", score=0.5),
        ],
        skipped_topics=[14, 15, 16],
        learning_signals=[
            LearningSignal(concept="RAG", signal_type="strong", day=7),
            LearningSignal(concept="Deployment", signal_type="weak", day=18),
        ],
        performance={"retrieval": 0.85, "agents": 0.7, "deployment": 0.5},
        projects=["RAG documentation system"],
        tools_used=["LangChain", "ChromaDB"],
    )


@pytest.fixture
def interview_repo():
    return InMemoryInterviewRepository()


@pytest.fixture
def feedback_repo():
    return InMemoryFeedbackRepository()
