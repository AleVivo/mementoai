import logging
import httpx
import json
from app.config import settings
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

GENERATE_MODEL = "qwen2.5:7b"
EMBED_MODEL = "nomic-embed-text"


async def preload_models() -> None:
    """Carica entrambi i modelli in memoria Ollama al bootstrap dell'app.
    keep_alive=-1 li mantiene caricati indefinitamente."""
    logger.info("[ollama] Preloading models...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        logger.info(f"[ollama] Loading {GENERATE_MODEL}...")
        await client.post(
            f"{settings.ollama_url}/api/generate",
            json={"model": GENERATE_MODEL, "keep_alive": -1},
        )
        logger.info(f"[ollama] {GENERATE_MODEL} loaded.")

        logger.info(f"[ollama] Loading {EMBED_MODEL}...")
        await client.post(
            f"{settings.ollama_url}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": "", "keep_alive": -1},
        )
        logger.info(f"[ollama] {EMBED_MODEL} loaded.")
    logger.info("[ollama] All models ready.")


async def unload_models() -> None:
    """Scarica i modelli dalla memoria Ollama allo shutdown dell'app."""
    logger.info("[ollama] Unloading models...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            f"{settings.ollama_url}/api/generate",
            json={"model": GENERATE_MODEL, "keep_alive": 0},
        )
        await client.post(
            f"{settings.ollama_url}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": "", "keep_alive": 0},
        )
    logger.info("[ollama] Models unloaded.")


async def generate_by_prompt(prompt: str) -> str:
    logger.debug(f"[ollama] generate_by_prompt — prompt length: {len(prompt)} chars")
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/generate",
            json={
                "model": GENERATE_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": -1,
            },
        )
        response.raise_for_status()
        result = response.json()["response"]
        logger.debug(f"[ollama] generate_by_prompt — response length: {len(result)} chars")
        return result

async def stream_by_prompt(prompt: str) -> AsyncGenerator[str, None]:
    logger.debug(f"[ollama] stream_by_prompt — prompt length: {len(prompt)} chars")
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            f"{settings.ollama_url}/api/generate",
            json={
                "model": GENERATE_MODEL,
                "prompt": prompt,
                "stream": True,
                "keep_alive": -1,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break

async def generate_embedding(text: str) -> list[float]:
    logger.debug(f"[ollama] generate_embedding — text length: {len(text)} chars")
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/embeddings",
            json={
                "model": EMBED_MODEL,
                "prompt": text,
                "keep_alive": -1,
            },
        )
        response.raise_for_status()
        embedding = response.json()["embedding"]
        logger.debug(f"[ollama] generate_embedding — vector dims: {len(embedding)}")
        return embedding