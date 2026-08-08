"""Evaluation service — assesses candidate answers using LLM."""

import json
from typing import Optional

from app.core.logging import get_logger
from app.domain.enums import AnswerQuality, FollowUpStrategy
from app.domain.models import (
    AnswerEvaluation,
    Claim,
    GeneratedQuestion,
    Misconception,
)
from app.llm.base import LLMProvider

logger = get_logger(__name__)

EVALUATOR_SYSTEM_PROMPT = """You are a technical interview answer evaluator for an AI engineering cohort.

Your task is to evaluate a candidate's answer to an interview question.

CONTEXT:
- The interview covers a 31-day AI engineering curriculum
- The candidate is being assessed on their understanding of AI engineering concepts
- You must be fair, evidence-based, and precise

EVALUATION CRITERIA:
1. Correctness: Is the answer factually and technically correct?
2. Technical Depth: Does the answer show deep understanding beyond surface level?
3. Reasoning: Does the candidate demonstrate sound reasoning and logic?
4. Communication: Is the answer clear and well-structured?
5. Production Awareness: Does the candidate consider real-world deployment concerns?

RESPONSE FORMAT:
You MUST respond with valid JSON matching this exact structure:
{
    "quality": "excellent|correct|partially_correct|incorrect|vague|superficial|deep|confused|unsupported_claim|off_topic",
    "correctness": 0.0-1.0,
    "technical_depth": 0.0-1.0,
    "reasoning": 0.0-1.0,
    "communication": 0.0-1.0,
    "production_awareness": 0.0-1.0,
    "confidence": 0.0-1.0,
    "missing_concepts": ["concept1", "concept2"],
    "misconceptions": ["misconception1"],
    "evidence": ["evidence of understanding 1", "evidence 2"],
    "claims": ["technical claim made by candidate"],
    "recommended_next_action": "deepen|probe_missing|challenge|simplify|change_topic|revisit_later|conclude_topic"
}

Be rigorous but fair. A partial answer that shows reasoning should score higher than a memorized correct answer with no depth."""


class EvaluationService:
    """Service for evaluating candidate answers."""

    def __init__(self, llm: LLMProvider):
        self._llm = llm

    async def evaluate_answer(
        self,
        question: GeneratedQuestion,
        answer: str,
        curriculum_context: str = "",
        conversation_context: str = "",
    ) -> AnswerEvaluation:
        """Evaluate a candidate's answer to an interview question."""
        messages = [
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": self._build_eval_prompt(
                question, answer, curriculum_context, conversation_context
            )},
        ]

        try:
            response = await self._llm.generate(
                messages, temperature=0.2, max_tokens=1024
            )
            evaluation = self._parse_evaluation(response.content, question.question_id)
            logger.info(
                "answer_evaluated",
                question_id=question.question_id,
                quality=evaluation.quality.value,
                correctness=evaluation.correctness,
            )
            return evaluation
        except Exception as e:
            logger.error("evaluation_failed", error=str(e))
            return self._fallback_evaluation(question.question_id)

    def _build_eval_prompt(
        self,
        question: GeneratedQuestion,
        answer: str,
        curriculum_context: str,
        conversation_context: str,
    ) -> str:
        """Build the evaluation prompt."""
        prompt = f"""Evaluate this candidate's answer:

QUESTION:
{question.question_text}

QUESTION METADATA:
- Concept: {question.concept}
- Skill Dimension: {question.skill_dimension.value}
- Difficulty: {question.difficulty}/5
- Expected Evidence: {', '.join(question.expected_evidence)}

CANDIDATE'S ANSWER:
{answer}
"""
        if curriculum_context:
            prompt += f"\nCURRICULUM CONTEXT:\n{curriculum_context}\n"

        if conversation_context:
            prompt += f"\nCONVERSATION CONTEXT (previous exchanges):\n{conversation_context}\n"

        prompt += "\nProvide your evaluation as JSON."
        return prompt

    def _parse_evaluation(self, content: str, question_id: str) -> AnswerEvaluation:
        """Parse LLM evaluation response into structured data."""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # Find JSON object
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            content = content[start:end]

        data = json.loads(content)

        # Map quality string
        quality_map = {v.value: v for v in AnswerQuality}
        quality = quality_map.get(data.get("quality", ""), AnswerQuality.PARTIALLY_CORRECT)

        # Map follow-up strategy
        action_map = {v.value: v for v in FollowUpStrategy}
        action = action_map.get(
            data.get("recommended_next_action", ""), FollowUpStrategy.DEEPEN
        )

        return AnswerEvaluation(
            question_id=question_id,
            quality=quality,
            correctness=float(data.get("correctness", 0.5)),
            technical_depth=float(data.get("technical_depth", 0.5)),
            reasoning=float(data.get("reasoning", 0.5)),
            communication=float(data.get("communication", 0.5)),
            production_awareness=float(data.get("production_awareness", 0.3)),
            confidence=float(data.get("confidence", 0.5)),
            missing_concepts=data.get("missing_concepts", []),
            misconceptions=data.get("misconceptions", []),
            evidence=data.get("evidence", []),
            recommended_next_action=action,
        )

    def _fallback_evaluation(self, question_id: str) -> AnswerEvaluation:
        """Provide a safe fallback evaluation when LLM fails."""
        return AnswerEvaluation(
            question_id=question_id,
            quality=AnswerQuality.PARTIALLY_CORRECT,
            correctness=0.5,
            technical_depth=0.5,
            reasoning=0.5,
            communication=0.5,
            production_awareness=0.3,
            confidence=0.5,
            missing_concepts=[],
            misconceptions=[],
            evidence=["Evaluation incomplete due to system error"],
            recommended_next_action=FollowUpStrategy.CHANGE_TOPIC,
        )

    def extract_claims(self, answer: str, question_concept: str, turn: int) -> list[Claim]:
        """Extract technical claims from candidate answer (heuristic-based)."""
        claims = []
        claim_indicators = [
            "always", "never", "best", "worst", "only way",
            "guaranteed", "impossible", "must", "should always",
        ]
        sentences = answer.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in claim_indicators):
                if len(sentence) > 15:
                    claims.append(Claim(
                        claim=sentence,
                        concept=question_concept,
                        status="questionable",
                        evidence_needed=True,
                        detected_at_turn=turn,
                    ))
        return claims[:3]  # Cap at 3 claims per answer

    def extract_misconceptions(
        self, evaluation: AnswerEvaluation, concept: str, turn: int
    ) -> list[Misconception]:
        """Extract misconceptions from evaluation."""
        misconceptions = []
        for m in evaluation.misconceptions:
            misconceptions.append(Misconception(
                concept=concept,
                misconception=m,
                severity="medium" if evaluation.correctness > 0.3 else "high",
                detected_at_turn=turn,
            ))
        return misconceptions
