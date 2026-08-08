"""Repository interfaces and in-memory implementations for interview state."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models import InterviewSession, InterviewFeedback


class InterviewRepository(ABC):
    """Abstract repository for interview session persistence."""

    @abstractmethod
    async def create(self, session: InterviewSession) -> InterviewSession:
        ...

    @abstractmethod
    async def get(self, interview_id: str) -> Optional[InterviewSession]:
        ...

    @abstractmethod
    async def update(self, session: InterviewSession) -> InterviewSession:
        ...

    @abstractmethod
    async def delete(self, interview_id: str) -> bool:
        ...


class FeedbackRepository(ABC):
    """Abstract repository for feedback persistence."""

    @abstractmethod
    async def save(self, feedback: InterviewFeedback) -> InterviewFeedback:
        ...

    @abstractmethod
    async def get(self, interview_id: str) -> Optional[InterviewFeedback]:
        ...


class InMemoryInterviewRepository(InterviewRepository):
    """In-memory implementation for development and testing."""

    def __init__(self):
        self._store: dict[str, InterviewSession] = {}

    async def create(self, session: InterviewSession) -> InterviewSession:
        self._store[session.interview_id] = session
        return session

    async def get(self, interview_id: str) -> Optional[InterviewSession]:
        return self._store.get(interview_id)

    async def update(self, session: InterviewSession) -> InterviewSession:
        if session.interview_id not in self._store:
            raise ValueError(f"Interview {session.interview_id} not found")
        # Optimistic concurrency check
        existing = self._store[session.interview_id]
        if existing.state_version >= session.state_version:
            session.state_version = existing.state_version + 1
        self._store[session.interview_id] = session
        return session

    async def delete(self, interview_id: str) -> bool:
        if interview_id in self._store:
            del self._store[interview_id]
            return True
        return False


class InMemoryFeedbackRepository(FeedbackRepository):
    """In-memory feedback repository."""

    def __init__(self):
        self._store: dict[str, InterviewFeedback] = {}

    async def save(self, feedback: InterviewFeedback) -> InterviewFeedback:
        self._store[feedback.interview_id] = feedback
        return feedback

    async def get(self, interview_id: str) -> Optional[InterviewFeedback]:
        return self._store.get(interview_id)
