import httpx
from app.config import settings

async def generate_by_prompt(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=240.0) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["response"]

async def generate_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": text
            }
        )
        response.raise_for_status()
        return response.json()["embedding"]