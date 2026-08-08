"""Candidate service for loading and analyzing candidate profiles."""

import json
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger
from app.domain.models import CandidateProfile, Curriculum

logger = get_logger(__name__)


class CandidateAnalysis:
    """Analysis of a candidate's strengths, weaknesses, and coverage."""

    def __init__(self, profile: CandidateProfile, curriculum: Curriculum):
        self.profile = profile
        self.curriculum = curriculum
        self.strong_areas: list[str] = []
        self.weak_areas: list[str] = []
        self.unknown_areas: list[str] = []
        self.skipped_areas: list[str] = []
        self.completed_days: list[int] = []
        self.recommended_topics: list[int] = []
        self._analyze()

    def _analyze(self):
        """Perform candidate analysis."""
        # Completed days
        self.completed_days = [
            m.day for m in self.profile.completed_missions
            if m.status == "completed"
        ]

        # Strong areas: high score, few attempts
        for signal in self.profile.learning_signals:
            if signal.signal_type == "strong":
                self.strong_areas.append(signal.concept)
            elif signal.signal_type in ("weak", "confused"):
                self.weak_areas.append(signal.concept)

        # From performance scores
        for skill, score in self.profile.performance.items():
            if score >= 0.8 and skill not in self.strong_areas:
                self.strong_areas.append(skill)
            elif score < 0.6 and score > 0 and skill not in self.weak_areas:
                self.weak_areas.append(skill)

        # Skipped areas
        for day_num in self.profile.skipped_topics:
            day = self.curriculum.get_day(day_num)
            if day:
                self.skipped_areas.extend(day.concepts[:2])

        # Unknown areas: curriculum days with no evidence
        all_days = {d.day for d in self.curriculum.days}
        covered_days = set(self.completed_days) | set(self.profile.skipped_topics)
        unknown_days = all_days - covered_days
        for day_num in unknown_days:
            day = self.curriculum.get_day(day_num)
            if day:
                self.unknown_areas.extend(day.concepts[:1])

        # Recommended topics to probe
        self.recommended_topics = sorted(
            [m.day for m in self.profile.completed_missions if m.status == "completed"],
            key=lambda d: next(
                (m.score or 0 for m in self.profile.completed_missions if m.day == d),
                0
            ),
        )

    def get_interview_focus_areas(self) -> list[int]:
        """Get curriculum days that should be focused on during interview."""
        focus = []
        # Strong areas (validate depth)
        for day_num in self.completed_days:
            focus.append(day_num)
        # Weak areas (probe understanding)
        for signal in self.profile.learning_signals:
            if signal.signal_type in ("weak", "confused") and signal.day not in focus:
                focus.append(signal.day)
        return focus[:10]  # Cap at 10 focus areas


class CandidateService:
    """Service for loading and managing candidate profiles."""

    def __init__(self, candidates_path: str = "data/candidates.json"):
        self._candidates: dict[str, CandidateProfile] = {}
        self._path = candidates_path

    async def load(self) -> None:
        """Load candidates from JSON file."""
        path = Path(self._path)
        if not path.exists():
            raise FileNotFoundError(f"Candidates file not found: {self._path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for candidate_data in data.get("candidates", []):
            profile = CandidateProfile.model_validate(candidate_data)
            self._candidates[profile.candidate_id] = profile

        logger.info("candidates_loaded", count=len(self._candidates))

    async def get_candidate(self, candidate_id: str) -> Optional[CandidateProfile]:
        """Get a candidate profile by ID."""
        if not self._candidates:
            await self.load()
        return self._candidates.get(candidate_id)

    async def get_all_candidates(self) -> list[CandidateProfile]:
        """Get all candidate profiles."""
        if not self._candidates:
            await self.load()
        return list(self._candidates.values())

    async def analyze_candidate(
        self, candidate_id: str, curriculum: Curriculum
    ) -> Optional[CandidateAnalysis]:
        """Analyze a candidate's profile against the curriculum."""
        profile = await self.get_candidate(candidate_id)
        if not profile:
            return None
        return CandidateAnalysis(profile, curriculum)
