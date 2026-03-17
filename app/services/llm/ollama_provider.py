"""
Implementazione concreta dei provider LLM per Ollama.

Questo file contiene TUTTA la logica specifica di Ollama:
- gli endpoint (/api/embeddings, /api/chat, /api/generate)
- il formato dei chunk in streaming
- preload/unload dei modelli

Il resto del codice non importa da questo file direttamente —
usa la factory in factory.py.
"""

import json
import logging
import httpx
from typing import AsyncGenerator, Optional

from app.config import settings
from app.services.llm.base import EmbeddingProvider, ToolChatProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifecycle (preload / unload) — specifico di Ollama, non è nell'ABC
# ---------------------------------------------------------------------------

async def preload_models() -> None:
    """
    Carica entrambi i modelli in memoria Ollama al bootstrap dell'app.
    keep_alive=-1 li mantiene caricati indefinitamente.

    Questa funzione NON fa parte dell'interfaccia ABC perché è specifica
    di Ollama — altri provider (OpenAI, Anthropic) non hanno bisogno
    di pre-caricare nulla.
    Viene chiamata esplicitamente da main.py nel lifespan solo se il provider è Ollama.
    """
    logger.info("[ollama] Preloading models...")
    async with httpx.AsyncClient(timeout=300.0) as client:

        if settings.llm_provider.lower() == "ollama":
            logger.info(f"[ollama] Loading {settings.ollama_chat_model}...")
            await client.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": settings.ollama_chat_model, "keep_alive": -1},
            )

        if settings.embedding_provider.lower() == "ollama":
            logger.info(f"[ollama] Loading {settings.ollama_embed_model}...")
            await client.post(
                f"{settings.ollama_url}/api/embeddings",
                json={"model": settings.ollama_embed_model, "prompt": "", "keep_alive": -1},
            )

    logger.info("[ollama] All models ready.")


async def unload_models() -> None:
    """Scarica i modelli dalla memoria Ollama allo shutdown dell'app."""
    logger.info("[ollama] Unloading models...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        if settings.llm_provider.lower() == "ollama":
            await client.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": settings.ollama_chat_model, "keep_alive": 0},
            )

        if settings.embedding_provider.lower() == "ollama":
            await client.post(
                f"{settings.ollama_url}/api/embeddings",
                json={"model": settings.ollama_embed_model, "prompt": "", "keep_alive": 0},
            )
            
    logger.info("[ollama] Models unloaded.")


# ---------------------------------------------------------------------------
# EmbeddingProvider — Ollama
# ---------------------------------------------------------------------------

class OllamaEmbeddingProvider(EmbeddingProvider):

    async def embed(self, text: str) -> list[float]:
        logger.debug(f"[ollama] embed — text length: {len(text)} chars")
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/embeddings",
                json={"model": settings.ollama_embed_model, "prompt": text, "keep_alive": -1},
            )
            response.raise_for_status()
            embedding = response.json()["embedding"]
            logger.debug(f"[ollama] embed — vector dims: {len(embedding)}")
            return embedding


# ---------------------------------------------------------------------------
# ToolChatProvider — Ollama
# ---------------------------------------------------------------------------

class OllamaChatProvider(ToolChatProvider):
    """
    ToolChatProvider implementato su Ollama /api/chat.

    Differenza chiave rispetto al vecchio ollama.py:
    - Il vecchio codice usava /api/generate con un prompt stringa
    - Qui usiamo /api/chat con messages array — più corretto per conversazioni
      multi-turno e necessario per il function calling

    Come Ollama gestisce lo streaming con tool_calls (marzo 2026):
    - I chunk done=false con content="" e tool_calls=[...] contengono la decisione
    - I chunk done=false con content="token" contengono il testo (reasoning o risposta)
    - Il chunk done=true è sempre vuoto quando ci sono tool_calls
    """

    async def stream_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming senza tool — usato da rag.py per la risposta RAG.
        Yields: token di testo (str)
        """
        full_messages = self._build_messages(messages, system_prompt)

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_url}/api/chat",
                json={
                    "model": settings.ollama_chat_model,
                    "messages": full_messages,
                    "stream": True,
                    "keep_alive": -1,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break

    async def stream_chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Streaming con tool — usato da agent.py nel ReAct loop.
        Yields: dict normalizzati {"type": "token"|"tool_call"|"done", ...}

        La normalizzazione qui è importante: agent.py non deve sapere che
        Ollama mette i tool_calls in chunk intermedi con done=false.
        """
        full_messages = self._build_messages(messages, system_prompt)

        buffer = ""
        tool_calls_found = None

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_url}/api/chat",
                json={
                    "model": settings.ollama_chat_model,
                    "messages": full_messages,
                    "tools": tools,
                    "stream": True,
                    "keep_alive": -1,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    msg = chunk.get("message", {})

                    token = msg.get("content", "")
                    if token:
                        buffer += token
                        # Emetti subito come reasoning
                        yield {"type": "token", "content": token}

                    if msg.get("tool_calls"):
                        tool_calls_found = msg["tool_calls"]

                    if chunk.get("done"):
                        break

        # Dopo lo stream: se ci sono tool_calls, emetti un evento per ciascuno
        if tool_calls_found:
            for tc in tool_calls_found:
                raw_args = tc["function"]["arguments"]
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                yield {
                    "type": "tool_call",
                    "name": tc["function"]["name"],
                    "args": args,
                    # Mettiamo anche l'id se presente — utile per debug
                    "id": tc.get("id"),
                }

        yield {"type": "done", "buffer": buffer, "has_tool_calls": bool(tool_calls_found)}

    # ---------------------------------------------------------------------------
    # Helper privato
    # ---------------------------------------------------------------------------

    @staticmethod
    def _build_messages(messages: list[dict], system_prompt: Optional[str]) -> list[dict]:
        """
        Prepend il system prompt come primo messaggio se fornito.

        Perché un metodo separato?
        Tutti i provider OpenAI-compatibili (Ollama incluso) accettano il system
        prompt come messaggio con role="system" in testa all'array.
        Centralizzare questo evita duplicazione in stream_chat e stream_chat_with_tools.
        """
        if system_prompt:
            return [{"role": "system", "content": system_prompt}, *messages]
        return messages
    
    def build_assistant_message(self, content: str, tool_calls: list[dict]) -> dict:
        """
        Formato Ollama — verificato sulla documentazione ufficiale (marzo 2026):
          - Nessun "type" al livello superiore (Ollama non lo produce, non lo richiede)
          - arguments è un dict nativo, NON una stringa JSON serializzata
          - id non esiste nel formato nativo di Ollama

        Fonte: https://docs.ollama.com/api/chat
        """
        return {
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["args"],  # dict, non stringa
                    },
                }
                for tc in tool_calls
            ],
        }

    def build_tool_message(self, tool_call: dict, result) -> dict:
        """
        Messaggio role="tool" per Ollama.
        Ollama non richiede tool_call_id — il messaggio è identificato
        dalla posizione nella conversazione.
        """
        return {
            "role": "tool",
            "content": json.dumps(result, ensure_ascii=False, default=str),
        }