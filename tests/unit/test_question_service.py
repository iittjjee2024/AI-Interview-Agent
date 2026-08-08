"""Unit tests for the question service."""

import pytest
from app.services.question_service import QuestionService
from app.services.candidate_service import CandidateAnalysis
from app.domain.models import InterviewMemory, CoverageState
from app.domain.enums import InterviewState


class TestQuestionService:
    def setup_method(self):
        self.service = QuestionService()

    def test_plan_selects_uncovered_day(self, sample_candidate, sample_curriculum):
        """Questions should target uncovered curriculum days."""
        analysis = CandidateAnalysis(sample_candidate, sample_curriculum)
        memory = InterviewMemory(
            interview_phase=InterviewState.BASELINE_ASSESSMENT,
            current_difficulty=3,
            coverage=CoverageState(curriculum_days_covered=[1]),
        )

        plan = self.service.plan_next_question(memory, analysis, sample_curriculum)
        # Should not pick day 1 again (already covered)
        assert plan.curriculum_day != 1 or plan.curriculum_day in [7, 10, 18, 21]

    def test_difficulty_bounded(self, sample_candidate, sample_curriculum):
        """Difficulty should always stay between 1 and 5."""
        analysis = CandidateAnalysis(sample_candidate, sample_curriculum)
        memory = InterviewMemory(
            interview_phase=InterviewState.DEEP_DIVE,
            current_difficulty=5,
        )

        plan = self.service.plan_next_question(memory, analysis, sample_curriculum)
        assert 1 <= plan.difficulty <= 5

    def test_similarity_detection(self):
        """Should detect similar questions."""
        prev = [
            "Walk me through your RAG system architecture",
            "How do you handle document chunking",
        ]
        similar = "Explain the architecture of your RAG system"
        different = "What security risks exist in agentic AI systems?"

        sim_score = self.service.check_similarity(similar, prev)
        diff_score = self.service.check_similarity(different, prev)
        assert sim_score > diff_score

    def test_should_not_end_early(self, sample_candidate, sample_curriculum):
        """Interview should not end before minimum requirements."""
        memory = InterviewMemory(
            questions_asked=[],
            coverage=CoverageState(curriculum_days_covered=[1]),
        )
        assert not self.service.should_end_interview(memory)

    def test_should_end_when_requirements_met(self, sample_candidate, sample_curriculum):
        """Interview should end when all requirements met."""
        from app.domain.models import GeneratedQuestion
        from app.domain.enums import SkillDimension, QuestionType

        questions = [
            GeneratedQuestion(
                question_id=f"q_{i}", question_text=f"Q{i}",
                curriculum_day=i, concept=f"c{i}",
                skill_dimension=SkillDimension.CONCEPTUAL_UNDERSTANDING,
                difficulty=3, question_type=QuestionType.CONCEPTUAL,
            )
            for i in range(8)
        ]
        memory = InterviewMemory(
            questions_asked=questions,
            coverage=CoverageState(curriculum_days_covered=[1, 7, 10, 18]),
            skill_scores={"a": 0.8, "b": 0.7, "c": 0.6, "d": 0.5},
        )
        assert self.service.should_end_interview(memory)
