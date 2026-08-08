"""Integration tests for the interview API."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.llm.base import LLMResponse


@pytest.fixture
def mock_llm_response():
    """Mock LLM to avoid real API calls in tests."""
    responses = [
        "Let's start with something you've built. Walk me through the RAG system you worked on.",
        "Good. Now suppose the retrieval is returning similar but irrelevant chunks. How would you debug that?",
        "That's useful. Let's make it harder — how would you handle this at scale with 10M documents?",
    ]
    call_count = {"n": 0}

    async def mock_generate(messages, temperature=None, max_tokens=None):
        idx = min(call_count["n"], len(responses) - 1)
        call_count["n"] += 1
        return LLMResponse(content=responses[idx], model="test", tokens_used=50)

    return mock_generate


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_start_interview(mock_llm_response):
    """Test starting an interview."""
    mock_provider = AsyncMock()
    mock_provider.generate = mock_llm_response

    with patch("app.api.dependencies.create_llm_provider", return_value=mock_provider):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/interview/start",
                json={"candidate_id": "candidate_001"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "interview_id" in data
            assert data["status"] == "in_progress"
            assert data["turn"] == 1
            assert len(data["message"]) > 0


@pytest.mark.asyncio
async def test_invalid_candidate():
    """Test starting with invalid candidate."""
    with patch("app.api.dependencies.create_llm_provider") as mock_factory:
        mock_factory.return_value = AsyncMock()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/interview/start",
                json={"candidate_id": "nonexistent"},
            )
            assert response.status_code == 404
