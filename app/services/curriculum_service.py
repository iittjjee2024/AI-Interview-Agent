"""Curriculum service for loading and querying curriculum data."""

import json
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger
from app.domain.models import Curriculum, CurriculumDay

logger = get_logger(__name__)


class CurriculumService:
    """Service for loading and retrieving curriculum data."""

    def __init__(self, curriculum_path: str = "data/curriculum.json"):
        self._curriculum: Optional[Curriculum] = None
        self._path = curriculum_path

    async def load(self) -> Curriculum:
        """Load curriculum from JSON file."""
        if self._curriculum is not None:
            return self._curriculum

        path = Path(self._path)
        if not path.exists():
            raise FileNotFoundError(f"Curriculum file not found: {self._path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        days = [CurriculumDay.model_validate(d) for d in data.get("days", [])]
        self._curriculum = Curriculum(days=days)
        logger.info("curriculum_loaded", days=len(days))
        return self._curriculum

    async def get_curriculum(self) -> Curriculum:
        """Get loaded curriculum."""
        if self._curriculum is None:
            return await self.load()
        return self._curriculum

    async def get_day(self, day_number: int) -> Optional[CurriculumDay]:
        """Get curriculum for a specific day."""
        curriculum = await self.get_curriculum()
        return curriculum.get_day(day_number)

    async def get_context_for_day(self, day_number: int) -> str:
        """Get formatted context string for a curriculum day."""
        day = await self.get_day(day_number)
        if not day:
            return ""
        return (
            f"Day {day.day} - {day.module}: {day.topic}\n"
            f"Concepts: {', '.join(day.concepts)}\n"
            f"Objectives: {', '.join(day.learning_objectives)}\n"
            f"Tools: {', '.join(day.tools)}\n"
            f"Difficulty: {day.difficulty}"
        )

    async def get_days_for_concepts(self, concepts: list[str]) -> list[CurriculumDay]:
        """Get curriculum days covering specific concepts."""
        curriculum = await self.get_curriculum()
        matching = []
        for day in curriculum.days:
            day_concepts_lower = [c.lower() for c in day.concepts]
            for concept in concepts:
                if concept.lower() in day_concepts_lower:
                    matching.append(day)
                    break
        return matching
