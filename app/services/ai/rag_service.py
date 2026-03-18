import json
import logging
import time
from app.models.chat import ChatRequest
from app.models.chunk import ChunkSearchResult
from app.services.ai import search_service
from app.services.ai import search_service
from app.models.search import SearchRequest
from app.services.llm.factory import get_chat_provider
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """Sei un assistente per team di sviluppo.
Rispondi alla domanda usando SOLO le informazioni fornite nel contesto.
Se il contesto è vuoto o non contiene informazioni rilevanti, rispondi:
"Non ho trovato informazioni su questo argomento nella knowledge base."
Cita le fonti usando ESCLUSIVAMENTE il titolo tra parentesi quadre \
esattamente come appare nel contesto, es. [Titolo della nota].
Non inventare titoli. Non aggiungere informazioni esterne al contesto.
Rispondi in italiano."""

def _build_context_message(question: str, results: list[ChunkSearchResult]) -> str:
    """
    Costruisce il messaggio USER: solo contesto + domanda.
    Le istruzioni di comportamento sono nel system prompt, non qui.
    """
    seen: dict[str, int] = {}
    unique_chunks: list[tuple[int, ChunkSearchResult]] = []
    for chunk in results:
        eid = str(chunk.entry_id)
        if eid not in seen:
            seen[eid] = len(seen) + 1
        unique_chunks.append((seen[eid], chunk))

    context_parts = []
    for _, chunk in unique_chunks:
        section_label = chunk.heading if chunk.heading else "Contenuto"
        context_parts.append(
            f"[{chunk.entry_title}] — {section_label}\n{chunk.text}"
        )
    context = "\n\n---\n\n".join(context_parts)

    logger.info(
        f"[rag] Context built — {len(unique_chunks)} chunk(s), "
        f"{len(seen)} source(s), {len(context)} chars"
    )

    return f"CONTESTO:\n{context}\n\nDOMANDA: {question}"


async def stream_rag(request: ChatRequest):
    t0 = time.perf_counter()
    logger.info(f"[chat] START — question: {request.question!r}, project: {request.project!r}")
    search_request = SearchRequest(
        query=request.question,
        project=request.project or None,
        top_k=request.top_k,
    )
    results = await search_service.search_chunks(search_request)
    logger.info(f"[chat] Vector search done — {len(results)} chunk(s) retrieved ({time.perf_counter()-t0:.2f}s)")

    sources = [
        {
            "entry_id": str(chunk.entry_id),
            "title": chunk.entry_title,
            "entry_type": chunk.entry_type,
            "section": chunk.heading,
        }
        for chunk in results
    ]
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

    user_message = _build_context_message(request.question, results)
    provider = get_chat_provider()

    async for token in provider.stream_chat(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=RAG_SYSTEM_PROMPT,
    ):
        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"

    logger.info(f"[chat] STREAM DONE — total time: {time.perf_counter()-t0:.2f}s")
