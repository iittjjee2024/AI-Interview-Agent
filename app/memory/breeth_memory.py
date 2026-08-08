"""Breeth memory integration for persistent interview knowledge.

Write candidate insights, retrieve relevant context.
The loop: Write, Retrieve, Repeat.
"""

from typing import Any, Optional

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

BREETH_API_BASE = "https://api.thebreeth.com/v1"


class BreethMemory:
    """Client for Breeth memory API — long-term knowledge storage and retrieval."""

    def __init__(self, api_key: str, group_id: str = "default", timeout: int = 15):
        self.api_key = api_key
        self.group_id = group_id
        self.timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def write(
        self,
        content: str,
        group_id: Optional[str] = None,
        extract_intent: bool = True,
    ) -> dict[str, Any]:
        """Write an episode/fact to Breeth memory.

        Args:
            content: The knowledge to store (e.g. candidate insight, interview finding).
            group_id: Optional override for the memory group.
            extract_intent: Whether Breeth should extract intent from the content.

        Returns:
            API response dict.
        """
        payload = {
            "content": content,
            "group_id": group_id or self.group_id,
            "extract_intent": extract_intent,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{BREETH_API_BASE}/episodes",
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                logger.info("breeth_memory_write", group_id=payload["group_id"])
                return result
        except httpx.HTTPError as e:
            logger.error("breeth_memory_write_failed", error=str(e))
            return {"error": str(e)}

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search Breeth memory for relevant facts.

        Args:
            query: Natural language search query.
            limit: Maximum number of results to return.

        Returns:
            List of matching edges/facts.
        """
        payload = {
            "query": query,
            "limit": limit,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{BREETH_API_BASE}/search",
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                edges = data.get("edges", [])
                logger.info("breeth_memory_search", query=query[:50], results=len(edges))
                return edges
        except httpx.HTTPError as e:
            logger.error("breeth_memory_search_failed", error=str(e))
            return []

    async def store_candidate_insight(
        self,
        candidate_id: str,
        insight: str,
        interview_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Store a candidate-specific insight in memory.

        Args:
            candidate_id: The candidate identifier.
            insight: The insight/observation to store.
            interview_id: Optional interview session ID for context.
        """
        content = f"[Candidate: {candidate_id}]"
        if interview_id:
            content += f" [Interview: {interview_id}]"
        content += f" {insight}"

        return await self.write(
            content=content,
            group_id=f"candidate_{candidate_id}",
        )

    async def retrieve_candidate_context(
        self,
        candidate_id: str,
        query: str,
        limit: int = 5,
    ) -> list[str]:
        """Retrieve relevant context about a candidate.

        Args:
            candidate_id: The candidate identifier.
            query: What to search for about this candidate.
            limit: Max results.

        Returns:
            List of relevant facts as strings.
        """
        full_query = f"Candidate {candidate_id}: {query}"
        edges = await self.search(query=full_query, limit=limit)
        return [edge.get("fact", "") for edge in edges if edge.get("fact")]

    async def store_interview_event(
        self,
        interview_id: str,
        event: str,
    ) -> dict[str, Any]:
        """Store an interview event for future reference.

        Args:
            interview_id: The interview session ID.
            event: Description of what happened.
        """
        return await self.write(
            content=f"[Interview: {interview_id}] {event}",
            group_id=f"interview_{interview_id}",
        )
