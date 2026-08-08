"""Domain enumerations for the AI Interview Agent."""

from enum import Enum


class InterviewState(str, Enum):
    """Interview state machine states."""
    INITIALIZING = "initializing"
    PLANNING = "planning"
    INTRODUCTION = "introduction"
    BASELINE_ASSESSMENT = "baseline_assessment"
    DEEP_DIVE = "deep_dive"
    FOLLOW_UP = "follow_up"
    CHALLENGE = "challenge"
    TOPIC_TRANSITION = "topic_transition"
    WEAKNESS_PROBE = "weakness_probe"
    CROSS_TOPIC_REASONING = "cross_topic_reasoning"
    FINAL_REVIEW = "final_review"
    COMPLETED = "completed"


class InterviewStatus(str, Enum):
    """Overall interview status."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SkillDimension(str, Enum):
    """Skill dimensions evaluated during interview."""
    CONCEPTUAL_UNDERSTANDING = "conceptual_understanding"
    SYSTEM_DESIGN = "system_design"
    IMPLEMENTATION = "implementation"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    TRADE_OFF_REASONING = "trade_off_reasoning"
    PRODUCTION_READINESS = "production_readiness"
    SECURITY = "security"
    RELIABILITY = "reliability"
    EVALUATION = "evaluation"
    OBSERVABILITY = "observability"
    COST_OPTIMIZATION = "cost_optimization"
    COMMUNICATION = "communication"
    PROBLEM_SOLVING = "problem_solving"


class QuestionType(str, Enum):
    """Types of questions the interviewer can ask."""
    CONCEPTUAL = "conceptual"
    EXPLAIN = "explain"
    IMPLEMENTATION = "implementation"
    DEBUGGING = "debugging"
    SYSTEM_DESIGN = "system_design"
    TRADE_OFF = "trade_off"
    ARCHITECTURE = "architecture"
    PRODUCTION = "production"
    SECURITY = "security"
    COST_OPTIMIZATION = "cost_optimization"
    CROSS_TOPIC = "cross_topic"
    PROJECT_BASED = "project_based"


class AnswerQuality(str, Enum):
    """Classification of candidate answer quality."""
    EXCELLENT = "excellent"
    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    INCORRECT = "incorrect"
    VAGUE = "vague"
    SUPERFICIAL = "superficial"
    DEEP = "deep"
    CONFUSED = "confused"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    OFF_TOPIC = "off_topic"


class DifficultyLevel(int, Enum):
    """Question difficulty levels."""
    DEFINITION = 1
    EXPLANATION = 2
    IMPLEMENTATION = 3
    SCENARIO = 4
    PRODUCTION_ARCHITECTURE = 5


class FollowUpStrategy(str, Enum):
    """Strategy for follow-up after evaluating an answer."""
    DEEPEN = "deepen"
    PROBE_MISSING = "probe_missing"
    CHALLENGE = "challenge"
    SIMPLIFY = "simplify"
    CHANGE_TOPIC = "change_topic"
    REVISIT_LATER = "revisit_later"
    CONCLUDE_TOPIC = "conclude_topic"


class PerformanceLevel(str, Enum):
    """Performance level classification."""
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    COMPETENT = "competent"
    STRONG = "strong"
    EXCELLENT = "excellent"
