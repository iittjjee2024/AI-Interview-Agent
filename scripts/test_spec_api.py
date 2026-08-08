"""Test the spec-compliant POST /api/interview endpoint with OpenRouter."""

import asyncio
import os

os.environ.setdefault("LLM_PROVIDER", "openrouter")
os.environ.setdefault("LLM_MODEL", "google/gemma-4-26b-a4b-it:free")

from app.core import config
config._settings = None

from httpx import AsyncClient, ASGITransport
from app.main import create_app


async def main():
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", timeout=60) as client:
        print("=" * 60)
        print("Testing POST /api/interview (Technical Spec)")
        print("=" * 60)

        # 1. Start interview
        print("\n--- START INTERVIEW ---")
        r = await client.post("/api/interview", json={
            "sessionId": "test-session-001",
            "candidate": {"candidate_id": "candidate_001"},
        })
        print(f"Status: {r.status_code}")
        data = r.json()
        if r.status_code != 200:
            print(f"Error: {data}")
            return
        print(f"Reply: {data['reply']}")
        print(f"Done: {data['done']}")

        # 2. Submit answer
        print("\n--- CANDIDATE RESPONDS ---")
        r2 = await client.post("/api/interview", json={
            "sessionId": "test-session-001",
            "message": (
                "I built a RAG system using LangChain and ChromaDB. I used recursive "
                "text splitting with 512-token chunks, OpenAI ada-002 embeddings, and "
                "similarity search with k=5. The generation step passes retrieved chunks "
                "as context to GPT-4. I would change the chunking to semantic chunking "
                "if I did it again because fixed-size splits break mid-sentence."
            ),
        })
        print(f"Status: {r2.status_code}")
        data2 = r2.json()
        if r2.status_code != 200:
            print(f"Error: {data2}")
            return
        print(f"Reply: {data2['reply']}")
        print(f"Done: {data2['done']}")

        print("\n" + "=" * 60)
        print("API SPEC TEST PASSED!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
