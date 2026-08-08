"""Quick test of Groq API connectivity."""
import asyncio
import httpx

API_KEY = "gsk_YOUR_GROQ_KEY_HERE"

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "Say hello in one sentence."}],
                "max_tokens": 30,
            },
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Response: {data['choices'][0]['message']['content']}")
        else:
            print(f"Error: {resp.text[:300]}")

asyncio.run(main())
