"""Curriculum RAG retriever — chunks, indexes, and retrieves curriculum content."""

from typing import Optional

from app.core.logging import get_logger
from app.domain.models import Curriculum, CurriculumDay
from app.retrieval.embeddings import EmbeddingService

logger = get_logger(__name__)


class CurriculumChunk:
    """A chunk of curriculum content with metadata."""

    def __init__(
        self,
        text: str,
        day: int,
        module: str,
        topic: str,
        concepts: list[str],
        chunk_type: str,  # overview, objective, concept, tool, project, skill
    ):
        self.text = text
        self.day = day
        self.module = module
        self.topic = topic
        self.concepts = concepts
        self.chunk_type = chunk_type

    def __repr__(self):
        return f"CurriculumChunk(day={self.day}, type={self.chunk_type}, text={self.text[:50]}...)"


class CurriculumRetriever:
    """RAG retriever that chunks curriculum data and retrieves relevant context.

    Pipeline:
        Curriculum JSON → Chunking → TF-IDF Embeddings → Similarity Search → Context
    """

    def __init__(self):
        self._embedding_service = EmbeddingService()
        self._chunks: list[CurriculumChunk] = []
        self._indexed = False

    def index_curriculum(self, curriculum: Curriculum) -> None:
        """Chunk and index the entire curriculum for retrieval."""
        self._chunks = self._chunk_curriculum(curriculum)
        documents = [chunk.text for chunk in self._chunks]
        self._embedding_service.fit(documents)
        self._indexed = True
        logger.info("curriculum_indexed", chunks=len(self._chunks))

    def _chunk_curriculum(self, curriculum: Curriculum) -> list[CurriculumChunk]:
        """Break curriculum into retrievable chunks with rich metadata."""
        chunks = []

        for day in curriculum.days:
            # Chunk 1: Day overview
            overview = (
                f"Day {day.day} — Module: {day.module} — Topic: {day.topic}. "
                f"Subtopics covered: {', '.join(day.subtopics)}. "
                f"Difficulty level: {day.difficulty}. "
                f"Prerequisites: days {day.prerequisites if day.prerequisites else 'none'}."
            )
            chunks.append(CurriculumChunk(
                text=overview, day=day.day, module=day.module,
                topic=day.topic, concepts=day.concepts, chunk_type="overview",
            ))

            # Chunk 2: Learning objectives
            if day.learning_objectives:
                objectives_text = (
                    f"Day {day.day} ({day.topic}) learning objectives: "
                    f"{'; '.join(day.learning_objectives)}."
                )
                chunks.append(CurriculumChunk(
                    text=objectives_text, day=day.day, module=day.module,
                    topic=day.topic, concepts=day.concepts, chunk_type="objective",
                ))

            # Chunk 3: Concepts (one chunk per 2-3 concepts for granularity)
            if day.concepts:
                concept_text = (
                    f"Day {day.day} ({day.topic}) key concepts: "
                    f"{', '.join(day.concepts)}. "
                    f"These are part of the {day.module} module at {day.difficulty} difficulty."
                )
                chunks.append(CurriculumChunk(
                    text=concept_text, day=day.day, module=day.module,
                    topic=day.topic, concepts=day.concepts, chunk_type="concept",
                ))

            # Chunk 4: Tools and projects
            if day.tools or day.projects:
                tools_text = (
                    f"Day {day.day} ({day.topic}) — "
                    f"Tools: {', '.join(day.tools)}. "
                    f"Projects: {', '.join(day.projects)}."
                )
                chunks.append(CurriculumChunk(
                    text=tools_text, day=day.day, module=day.module,
                    topic=day.topic, concepts=day.concepts, chunk_type="tool",
                ))

            # Chunk 5: Expected skills
            if day.expected_skills:
                skills_text = (
                    f"After Day {day.day} ({day.topic}), learners should be able to: "
                    f"{'; '.join(day.expected_skills)}."
                )
                chunks.append(CurriculumChunk(
                    text=skills_text, day=day.day, module=day.module,
                    topic=day.topic, concepts=day.concepts, chunk_type="skill",
                ))

        return chunks

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        day_filter: Optional[int] = None,
        module_filter: Optional[str] = None,
    ) -> list[CurriculumChunk]:
        """Retrieve relevant curriculum chunks for a query.

        Args:
            query: Natural language query (e.g., "RAG retrieval quality evaluation")
            top_k: Number of chunks to return
            day_filter: Optional filter to specific curriculum day
            module_filter: Optional filter to specific module

        Returns:
            List of relevant CurriculumChunks ranked by relevance.
        """
        if not self._indexed:
            return []

        # Get more results than needed so we can filter
        search_k = top_k * 3 if (day_filter or module_filter) else top_k
        results = self._embedding_service.search(query, top_k=search_k)

        retrieved = []
        for idx, score in results:
            chunk = self._chunks[idx]

            # Apply metadata filters
            if day_filter and chunk.day != day_filter:
                continue
            if module_filter and chunk.module.lower() != module_filter.lower():
                continue

            retrieved.append(chunk)
            if len(retrieved) >= top_k:
                break

        return retrieved

    def retrieve_for_concept(self, concept: str, top_k: int = 3) -> list[CurriculumChunk]:
        """Retrieve curriculum context for a specific concept."""
        query = f"{concept} implementation details objectives skills"
        return self.retrieve(query, top_k=top_k)

    def retrieve_for_question_planning(
        self,
        concept: str,
        skill_dimension: str,
        difficulty: int,
    ) -> str:
        """Retrieve formatted context for question generation.

        Returns a formatted string ready to inject into the LLM prompt.
        """
        query = f"{concept} {skill_dimension} level {difficulty}"
        chunks = self.retrieve(query, top_k=4)

        if not chunks:
            return ""

        context_parts = []
        for chunk in chunks:
            context_parts.append(
                f"[Day {chunk.day} | {chunk.module} | {chunk.topic}]\n{chunk.text}"
            )

        return "\n\n".join(context_parts)

    def retrieve_for_evaluation(
        self,
        concept: str,
        curriculum_day: int,
    ) -> str:
        """Retrieve curriculum context to help evaluate an answer.

        Returns formatted context about what the candidate should know.
        """
        # First: get day-specific content
        day_chunks = self.retrieve(concept, top_k=3, day_filter=curriculum_day)

        # Then: broader concept context
        concept_chunks = self.retrieve(concept, top_k=2)

        all_chunks = day_chunks + [c for c in concept_chunks if c not in day_chunks]
        all_chunks = all_chunks[:5]

        if not all_chunks:
            return ""

        parts = ["CURRICULUM REFERENCE:"]
        for chunk in all_chunks:
            parts.append(f"- [{chunk.chunk_type.upper()}] {chunk.text}")

        return "\n".join(parts)

    def get_chunk_count(self) -> int:
        """Get total number of indexed chunks."""
        return len(self._chunks)
