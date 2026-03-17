"""
Implementazione concreta dei provider LLM per OpenAI (e compatibili: Groq, Together, ecc.).

Perché questa implementazione copre anche Groq e Together AI?
Tutti e tre espongono la stessa API OpenAI-compatibile — stesso endpoint /v1/chat/completions,
stesso formato streaming con Server-Sent Events, stessi parametri.
L'unica cosa che cambia è il base_url e l'api_key.

Modelli di riferimento:
- OpenAI:    gpt-4o-mini (chat) + text-embedding-3-small (embed, 1536 dim)
- Groq:      llama-3.3-70b-versatile (chat) — NO embedding nativo → usa Ollama
- Together:  meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo (chat)

    Il package `openai` funziona con qualsiasi provider compatibile — non è
    legato solo ad api.openai.com. Si configura il base_url nel costruttore.
"""

import logging
import json
from typing import AsyncGenerator, Optional, cast, Any

from app.config import settings
from app.services.llm.base import EmbeddingProvider, ToolChatProvider

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# EmbeddingProvider — OpenAI
# ---------------------------------------------------------------------------

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Embedding via OpenAI text-embedding-3-small.

    ⚠️  Dimensione vettori: 1536 (vs 768 di nomic-embed-text).
    Se si passa da Ollama a OpenAI embedding occorre:
    1. Ricreare l'indice vettoriale MongoDB con numDimensions=1536
    2. Re-indicizzare tutte le entry esistenti
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        self.model = model
        # Importazione lazy — evita errore di import se `openai` non è installato
        # e si sta usando solo Ollama
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        except ImportError:
            raise ImportError(
                "Il package 'openai' non è installato. "
                "Esegui: pip install openai>=1.0.0"
            )

    async def embed(self, text: str) -> list[float]:
        logger.debug(f"[openai] embed — text length: {len(text)} chars, model: {self.model}")
        response = await self._client.embeddings.create(
            model=self.model,
            input=text,
        )
        embedding = response.data[0].embedding
        logger.debug(f"[openai] embed — vector dims: {len(embedding)}")
        return embedding


# ---------------------------------------------------------------------------
# ToolChatProvider — OpenAI (e compatibili)
# ---------------------------------------------------------------------------

class OpenAIChatProvider(ToolChatProvider):
    """
    ChatProvider implementato su OpenAI /v1/chat/completions.

    Può essere usato anche con:
    - Groq:     base_url="https://api.groq.com/openai/v1"
    - Together: base_url="https://api.together.xyz/v1"
    - LM Studio locale: base_url="http://localhost:1234/v1"

    Come OpenAI gestisce lo streaming con tool_calls:
    - I chunk SSE hanno delta.content per i token di testo
    - I chunk SSE hanno delta.tool_calls per i pezzi della tool call
      (gli argomenti arrivano frammentati — vanno accumulati e poi parsati)
    - Il chunk con finish_reason="tool_calls" segnala la fine della tool call
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        self.model = model
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=api_key or settings.openai_api_key,
                base_url=base_url,  # None = default OpenAI
            )
        except ImportError:
            raise ImportError(
                "Il package 'openai' non è installato. "
                "Esegui: pip install openai>=1.0.0"
            )

    async def stream_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming senza tool — usato da rag.py."""
        full_messages = self._build_messages(messages, system_prompt)

        stream = await self._client.chat.completions.create(
        model=self.model,
        messages=cast(Any, full_messages),
        stream=True,
)
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    async def stream_chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Streaming con tool — usato da agent.py.

        La differenza principale rispetto a Ollama:
        OpenAI accumula gli argomenti della tool call in più chunk delta
        (ogni chunk ha un frammento di JSON). Bisogna accumulare tutto
        e poi fare json.loads alla fine.
        """
        full_messages = self._build_messages(messages, system_prompt)

        # Accumulatori per la tool call corrente
        tool_call_buffer: dict[int, dict] = {}  # index → {id, name, args_str}

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=cast(Any, full_messages),
            tools=cast(Any, tools),
            stream=True,
        )

        has_tool_calls = False

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            # Token di testo (reasoning o risposta finale)
            if delta.content:
                yield {"type": "token", "content": delta.content}

            # Frammenti di tool_call — vanno accumulati
            if delta.tool_calls:
                has_tool_calls = True
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_call_buffer:
                        tool_call_buffer[idx] = {"id": tc_delta.id, "name": "", "args_str": ""}
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_call_buffer[idx]["name"] += tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_call_buffer[idx]["args_str"] += tc_delta.function.arguments

            # Fine stream
            if finish_reason in ("stop", "tool_calls", "length"):
                break

        # Emetti le tool_calls complete
        for tc in tool_call_buffer.values():
            try:
                args = json.loads(tc["args_str"]) if tc["args_str"] else {}
            except json.JSONDecodeError:
                args = {"_raw": tc["args_str"]}
                logger.warning(f"[openai] tool_call args non parsabili: {tc['args_str']}")

            yield {
                "type": "tool_call",
                "name": tc["name"],
                "args": args,
                "id": tc["id"],
            }

        yield {"type": "done", "has_tool_calls": has_tool_calls}

    def build_assistant_message(self, content: str, tool_calls: list[dict]) -> dict:
        """
        Formato OpenAI — verificato sulla documentazione ufficiale (marzo 2026):
          - id obbligatorio — deve corrispondere all'id emesso durante lo streaming
          - type="function" obbligatorio al livello superiore
          - arguments è una stringa JSON serializzata (NON un dict)

        OpenAI restituisce errore 400 se id manca o non corrisponde al tool message.
        """
        return {
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": tc["id"] or f"call_{tc['name']}",  # fallback difensivo se id è None
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["args"], ensure_ascii=False),  # stringa, non dict
                    },
                }
                for tc in tool_calls
            ],
        }

    def build_tool_message(self, tool_call: dict, result) -> dict:
        """
        Messaggio role="tool" per OpenAI.
        tool_call_id è obbligatorio — deve referenziare l'id nell'assistant_message.
        Senza di esso OpenAI restituisce errore 400.
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call["id"] or f"call_{tool_call['name']}",
            "content": json.dumps(result, ensure_ascii=False, default=str),
        }

    @staticmethod
    def _build_messages(messages: list[dict], system_prompt: Optional[str]) -> list[dict]:
        if system_prompt:
            return [{"role": "system", "content": system_prompt}, *messages]
        return messages


# ---------------------------------------------------------------------------
# Convenience subclasses per provider compatibili
# ---------------------------------------------------------------------------

class GroqChatProvider(OpenAIChatProvider):
    """
    Groq è OpenAI-compatibile — cambia solo base_url e modello di default.
    Free tier disponibile su console.groq.com — ottimo per validare
    che un bug sia nel codice e non nel modello locale.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        super().__init__(
            api_key=api_key or settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            model=model,
        )