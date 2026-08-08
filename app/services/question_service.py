"""Question service — planning, generation, validation, and anti-repetition."""

import random
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.enums import (
    FollowUpStrategy,
    InterviewState,
    QuestionType,
    SkillDimension,
)
from app.domain.models import (
    CandidateProfile,
    CoverageState,
    Curriculum,
    GeneratedQuestion,
    InterviewMemory,
    QuestionPlan,
)
from app.services.candidate_service import CandidateAnalysis

logger = get_logger(__name__)


class QuestionService:
    """Handles question planning, selection scoring, and repetition detection."""

    def __init__(self):
        self._settings = get_settings()
        self._vectorizer = TfidfVectorizer(stop_words="english")

    def plan_next_question(
        self,
        memory: InterviewMemory,
        analysis: CandidateAnalysis,
        curriculum: Curriculum,
    ) -> QuestionPlan:
        """Plan the next question based on coverage, weakness, and evidence needs."""
        coverage = memory.coverage
        turn = len(memory.questions_asked)

        # Determine which days still need coverage
        uncovered_days = self._get_uncovered_priority_days(coverage, analysis, curriculum)

        # Select target day
        target_day = self._select_target_day(
            uncovered_days, analysis, memory, curriculum
        )

        # Select concept from that day
        day_data = curriculum.get_day(target_day)
        concept = self._select_concept(day_data, memory, analysis)

        # Determine question type and skill dimension
        question_type = self._select_question_type(memory, analysis, turn)
        skill_dim = self._select_skill_dimension(memory, analysis, question_type)

        # Determine difficulty
        difficulty = self._calculate_difficulty(memory, analysis)

        # Determine follow-up strategy
        follow_up = self._determine_follow_up_strategy(memory)

        # Build rationale
        rationale = self._build_rationale(
            target_day, concept, analysis, memory, question_type
        )

        return QuestionPlan(
            curriculum_day=target_day,
            concept=concept,
            skill_dimension=skill_dim,
            difficulty=difficulty,
            question_type=question_type,
            rationale=rationale,
            expected_evidence=day_data.expected_skills[:3] if day_data else [],
            follow_up_strategy=follow_up,
        )

    def _get_uncovered_priority_days(
        self,
        coverage: CoverageState,
        analysis: CandidateAnalysis,
        curriculum: Curriculum,
    ) -> list[int]:
        """Get days that haven't been covered yet, prioritized."""
        all_focus_days = analysis.get_interview_focus_areas()
        covered = set(coverage.curriculum_days_covered)
        uncovered = [d for d in all_focus_days if d not in covered]

        if not uncovered:
            # Fall back to any curriculum day not yet covered
            all_days = [d.day for d in curriculum.days]
            uncovered = [d for d in all_days if d not in covered]

        return uncovered if uncovered else all_focus_days

    def _select_target_day(
        self,
        uncovered_days: list[int],
        analysis: CandidateAnalysis,
        memory: InterviewMemory,
        curriculum: Curriculum,
    ) -> int:
        """Score and select the best target day."""
        if not uncovered_days:
            return random.choice(analysis.completed_days) if analysis.completed_days else 1

        scored = []
        for day_num in uncovered_days:
            score = 0.0
            day_data = curriculum.get_day(day_num)
            if not day_data:
                continue

            # Weakness priority: +3 if candidate is weak here
            if any(c.lower() in [w.lower() for w in analysis.weak_areas]
                   for c in day_data.concepts):
                score += 3.0

            # Coverage need: +2 if we need more days for minimum
            min_days = self._settings.min_curriculum_days
            if len(memory.coverage.curriculum_days_covered) < min_days:
                score += 2.0

            # Strong area depth check: +1 (validate claimed strength)
            if any(c.lower() in [s.lower() for s in analysis.strong_areas]
                   for c in day_data.concepts):
                score += 1.0

            # Repetition penalty
            if day_num in memory.coverage.questions_by_day:
                score -= memory.coverage.questions_by_day[day_num] * 1.5

            # Curriculum relevance (completed missions = more relevant)
            if day_num in analysis.completed_days:
                score += 1.5

            scored.append((day_num, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Pick from top 3 with some randomness to avoid predictability
        top = scored[:3]
        if len(top) > 1:
            weights = [s + 1 for _, s in top]  # shift scores positive
            total = sum(weights)
            weights = [w / total for w in weights]
            idx = np.random.choice(len(top), p=weights)
            return top[idx][0]
        return top[0][0] if top else uncovered_days[0]

    def _select_concept(
        self,
        day_data,
        memory: InterviewMemory,
        analysis: CandidateAnalysis,
    ) -> str:
        """Select the best concept from a curriculum day."""
        if not day_data or not day_data.concepts:
            return "general"

        # Prefer concepts not yet covered
        covered = set(memory.coverage.concepts_covered)
        uncovered = [c for c in day_data.concepts if c not in covered]

        if uncovered:
            # Prefer weak concepts
            weak_overlap = [c for c in uncovered
                          if c.lower() in [w.lower() for w in analysis.weak_areas]]
            if weak_overlap:
                return random.choice(weak_overlap)
            return random.choice(uncovered)

        return random.choice(day_data.concepts)

    def _select_question_type(
        self,
        memory: InterviewMemory,
        analysis: CandidateAnalysis,
        turn: int,
    ) -> QuestionType:
        """Select appropriate question type based on interview phase."""
        phase = memory.interview_phase

        if phase == InterviewState.INTRODUCTION:
            return QuestionType.PROJECT_BASED
        elif phase == InterviewState.BASELINE_ASSESSMENT:
            return random.choice([QuestionType.CONCEPTUAL, QuestionType.EXPLAIN])
        elif phase == InterviewState.DEEP_DIVE:
            return random.choice([
                QuestionType.IMPLEMENTATION,
                QuestionType.SYSTEM_DESIGN,
                QuestionType.DEBUGGING,
            ])
        elif phase == InterviewState.CHALLENGE:
            return random.choice([
                QuestionType.TRADE_OFF,
                QuestionType.PRODUCTION,
                QuestionType.COST_OPTIMIZATION,
            ])
        elif phase == InterviewState.WEAKNESS_PROBE:
            return random.choice([QuestionType.CONCEPTUAL, QuestionType.DEBUGGING])
        elif phase == InterviewState.CROSS_TOPIC_REASONING:
            return QuestionType.CROSS_TOPIC
        elif phase == InterviewState.FINAL_REVIEW:
            return random.choice([QuestionType.TRADE_OFF, QuestionType.ARCHITECTURE])
        else:
            # Mix of types
            types = list(QuestionType)
            used_types = [q.question_type for q in memory.questions_asked[-3:]]
            available = [t for t in types if t not in used_types]
            return random.choice(available) if available else random.choice(types)

    def _select_skill_dimension(
        self,
        memory: InterviewMemory,
        analysis: CandidateAnalysis,
        question_type: QuestionType,
    ) -> SkillDimension:
        """Map question type to most relevant skill dimension."""
        type_to_skill = {
            QuestionType.CONCEPTUAL: SkillDimension.CONCEPTUAL_UNDERSTANDING,
            QuestionType.EXPLAIN: SkillDimension.COMMUNICATION,
            QuestionType.IMPLEMENTATION: SkillDimension.IMPLEMENTATION,
            QuestionType.DEBUGGING: SkillDimension.DEBUGGING,
            QuestionType.SYSTEM_DESIGN: SkillDimension.SYSTEM_DESIGN,
            QuestionType.TRADE_OFF: SkillDimension.TRADE_OFF_REASONING,
            QuestionType.ARCHITECTURE: SkillDimension.ARCHITECTURE,
            QuestionType.PRODUCTION: SkillDimension.PRODUCTION_READINESS,
            QuestionType.SECURITY: SkillDimension.SECURITY,
            QuestionType.COST_OPTIMIZATION: SkillDimension.COST_OPTIMIZATION,
            QuestionType.CROSS_TOPIC: SkillDimension.PROBLEM_SOLVING,
            QuestionType.PROJECT_BASED: SkillDimension.SYSTEM_DESIGN,
        }
        return type_to_skill.get(question_type, SkillDimension.CONCEPTUAL_UNDERSTANDING)

    def _calculate_difficulty(
        self,
        memory: InterviewMemory,
        analysis: CandidateAnalysis,
    ) -> int:
        """Calculate appropriate difficulty level (1-5)."""
        base = memory.current_difficulty

        # Adjust based on recent evaluations
        recent_evals = memory.evaluations[-3:]
        if recent_evals:
            avg_correctness = sum(e.correctness for e in recent_evals) / len(recent_evals)
            if avg_correctness > 0.8:
                base = min(5, base + 1)
            elif avg_correctness < 0.4:
                base = max(1, base - 1)

        # Adjust based on candidate profile strength
        avg_performance = sum(analysis.profile.performance.values()) / max(
            len(analysis.profile.performance), 1
        )
        if avg_performance > 0.85:
            base = max(base, 3)  # Strong candidates start at least level 3
        elif avg_performance < 0.5:
            base = min(base, 3)  # Weaker candidates capped at 3

        return max(1, min(5, base))

    def _determine_follow_up_strategy(self, memory: InterviewMemory) -> FollowUpStrategy:
        """Determine follow-up strategy based on last evaluation."""
        if not memory.evaluations:
            return FollowUpStrategy.DEEPEN

        last_eval = memory.evaluations[-1]
        if last_eval.correctness > 0.8:
            return FollowUpStrategy.CHALLENGE
        elif last_eval.correctness > 0.5:
            return FollowUpStrategy.DEEPEN
        elif last_eval.correctness > 0.3:
            return FollowUpStrategy.PROBE_MISSING
        else:
            return FollowUpStrategy.SIMPLIFY

    def _build_rationale(
        self,
        target_day: int,
        concept: str,
        analysis: CandidateAnalysis,
        memory: InterviewMemory,
        question_type: QuestionType,
    ) -> str:
        """Build a rationale for why this question is being asked."""
        parts = []
        if concept.lower() in [w.lower() for w in analysis.weak_areas]:
            parts.append(f"Probing weak area: {concept}")
        elif concept.lower() in [s.lower() for s in analysis.strong_areas]:
            parts.append(f"Validating claimed strength: {concept}")
        else:
            parts.append(f"Exploring: {concept}")

        if target_day not in memory.coverage.curriculum_days_covered:
            parts.append(f"Expanding coverage to day {target_day}")

        parts.append(f"Question type: {question_type.value}")
        return ". ".join(parts)

    def check_similarity(
        self,
        new_question: str,
        previous_questions: list[str],
    ) -> float:
        """Check semantic similarity between new question and previous ones."""
        if not previous_questions:
            return 0.0

        try:
            all_texts = previous_questions + [new_question]
            tfidf_matrix = self._vectorizer.fit_transform(all_texts)
            new_vec = tfidf_matrix[-1]
            prev_vecs = tfidf_matrix[:-1]
            similarities = cosine_similarity(new_vec, prev_vecs).flatten()
            return float(max(similarities)) if len(similarities) > 0 else 0.0
        except Exception:
            return 0.0

    def is_too_similar(self, new_question: str, previous_questions: list[str]) -> bool:
        """Check if a question is too similar to previously asked ones."""
        threshold = self._settings.question_similarity_threshold
        similarity = self.check_similarity(new_question, previous_questions)
        return similarity > threshold

    def should_end_interview(self, memory: InterviewMemory) -> bool:
        """Determine if the interview should end."""
        settings = self._settings
        questions_asked = len(memory.questions_asked)
        days_covered = len(memory.coverage.curriculum_days_covered)

        # Hard maximum
        if questions_asked >= settings.max_questions:
            return True

        # Minimum requirements met + sufficient evidence
        if (
            questions_asked >= settings.min_questions
            and days_covered >= settings.min_curriculum_days
        ):
            # Check if we have enough skill evidence
            skills_with_evidence = sum(
                1 for score in memory.skill_scores.values() if score > 0
            )
            if skills_with_evidence >= 4:
                return True

        return False
