"""Test the full /api/interview flow locally."""
import asyncio
import os

from app.core import config
config._settings = None

from httpx import AsyncClient, ASGITransport
from app.main import create_app


async def main():
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", timeout=90) as client:
        # Test candidates endpoint
        r = await client.get("/api/candidates")
        print(f"Candidates: {r.status_code} - {len(r.json().get('candidates', []))} found")

        # Start interview
        print("\nStarting interview with CAND-001...")
        r = await client.post("/api/interview", json={
            "sessionId": "test-123",
            "candidate": {"candidate_id": "CAND-001"},
        })
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")


if __name__ == "__main__":
    asyncio.run(main())
