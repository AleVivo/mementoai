import json
import logging
import time

from langfuse import observe, get_client
from app.models.chat import ChatRequest
from app.models.chunk import ChunkSearchResult
from app.models.user import UserResponse
from app.services.ai import search_service
from app.services.ai import search_service
from app.models.search import SearchRequest
from app.services.ai.search_service import resolve_project_ids
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

@observe(name="execute_rag")
async def _execute_rag(
    question: str,
    project_id: str | None,
    top_k: int,
    current_user: UserResponse,
) -> tuple[list[dict], AsyncGenerator[str, None]]:
    t0 = time.perf_counter()
    logger.info(f"[rag] START — question: {question!r}, project: {project_id!r}")
 
    # vector_search_chunks è @observe — diventa span figlia automaticamente
    search_request = SearchRequest(query=question, top_k=top_k)
    results = await search_service.vector_search_chunks(search_request, current_user)
    logger.info(f"[rag] Vector search done — {len(results)} chunk(s) ({time.perf_counter()-t0:.2f}s)")
 
    sources = [
        {
            "entry_id": str(chunk.entry_id),
            "title": chunk.entry_title,
            "entry_type": chunk.entry_type,
            "section": chunk.heading,
        }
        for chunk in results
    ]
 
    user_message = _build_context_message(question, results)
    provider = get_chat_provider()
 
    # Aggiorna la span con metadata utili per la dashboard
    langfuse = get_client()
    langfuse.update_current_span(
        input={"question": question, "project_id": project_id},
        metadata={
            "chunks_retrieved": len(results),
            "sources_count": len(sources),
            "model": getattr(provider, "model", "unknown"),
        },
    )
 
    # Ritorna il generator LLM — i token vengono consumati da stream_rag
    token_stream = provider.stream_chat(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=RAG_SYSTEM_PROMPT,
    )
 
    return sources, token_stream

async def stream_rag(
    request: ChatRequest,
    current_user: UserResponse,
) -> AsyncGenerator[str, None]:
    t0 = time.perf_counter()
 
    sources, token_stream = await _execute_rag(
        question=request.question,
        project_id=request.project_id,
        top_k=request.top_k,
        current_user=current_user,
    )
 
    # Emette le sorgenti prima dei token — il FE le mostra subito
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
 
    # Emette i token man mano che arrivano dall'LLM
    async for token in token_stream:
        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
 
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
 
    logger.info(f"[rag] STREAM DONE — total time: {time.perf_counter()-t0:.2f}s")
