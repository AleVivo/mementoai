"""
Pipeline RAG completa con streaming SSE.

Responsabilità:
- Recupera i chunk rilevanti tramite retrieval/retriever.py
- Costruisce il contesto e il prompt
- Streamma la risposta dell'LLM via SSE

Separazione logica / trasporto SSE:
_execute_rag() contiene la logica tracciabile con @observe.
stream_rag() gestisce il trasporto SSE e consuma il generator.
Questa separazione è necessaria perché @observe non supporta AsyncGenerator.
"""

import json
import logging
import time
from typing import AsyncGenerator

from langfuse import get_client, observe
from llama_index.core.schema import NodeWithScore

from app.models.chat import ChatRequest
from app.models.user import UserResponse
from app.services.llm.factory import get_chat_provider
from app.services.retrieval import retriever, reranker
from app.services.domain import project_service

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """Sei un assistente per team di sviluppo.
Rispondi alla domanda usando SOLO le informazioni fornite nel contesto.
Se il contesto è vuoto o non contiene informazioni rilevanti, rispondi:
"Non ho trovato informazioni su questo argomento nella knowledge base."
Cita le fonti usando ESCLUSIVAMENTE il titolo tra parentesi quadre \
esattamente come appare nel contesto, es. [Titolo della nota].
Non inventare titoli. Non aggiungere informazioni esterne al contesto.
Rispondi in italiano."""


async def _execute_rag(
    question: str,
    project_ids: list[str],
    top_k: int,
) -> tuple[list[dict], AsyncGenerator[str, None]]:
    """
    Cuore della pipeline RAG — tracciato da Langfuse come span radice.

    Riceve project_ids già risolti e validati da stream_rag().
    Ritorna le sorgenti (per SSE immediato) e il generator dei token LLM.

    Separato da stream_rag() perché @observe non supporta AsyncGenerator —
    il generator viene creato qui ma consumato fuori dallo span.
    """
    t0 = time.perf_counter()
    logger.info(f"[rag] START — question: {question!r}, projects: {project_ids!r}")

    # Retrieval via LlamaIndex — embedding + $vectorSearch + AutoMerging
    retriever_instance = retriever.get_retriever(project_ids=project_ids, top_k=top_k)
    nodes: list[NodeWithScore] = await retriever_instance.aretrieve(question)
    logger.info(
        f"[rag] Retrieval done — {len(nodes)} chunk(s) "
        f"({time.perf_counter() - t0:.2f}s)"
    )

    # Re-ranking via SentenceTransformerRerank (cross-encoder locale, top_n=3)
    nodes = reranker.get_reranker().postprocess_nodes(nodes, query_str=question)
    logger.info(f"[rag] Reranking done — {len(nodes)} chunk(s) dopo rerank")

    sources = _build_sources(nodes)
    user_message = _build_context_message(question, nodes)
    provider = get_chat_provider()

    # Aggiorna la span Langfuse con metadata utili
    langfuse = get_client()
    langfuse.update_current_span(
        input={"question": question, "project_ids": project_ids},
        metadata={
            "chunks_retrieved": len(nodes),
            "sources_count": len(sources),
            "model": getattr(provider, "model", "unknown"),
        },
    )

    token_stream = provider.stream_chat(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=RAG_SYSTEM_PROMPT,
    )

    return sources, token_stream

@observe(name="stream_rag")
async def stream_rag(
    request: ChatRequest,
    current_user: UserResponse,
) -> AsyncGenerator[str, None]:
    """
    Entry point pubblico — chiamato dal router POST /chat.

    Gestisce autorizzazione, esecuzione RAG e trasporto SSE.
    L'ordine degli yield è deliberato: sources prima dei token
    così il frontend può mostrare le sorgenti mentre la risposta arriva.
    """
    t0 = time.perf_counter()

    project_ids = await project_service.resolve_project_ids(
        project_id=request.project_id,
        user_id=current_user.id,
    )

    sources, token_stream = await _execute_rag(
        question=request.question,
        project_ids=project_ids,
        top_k=request.top_k,
    )

    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

    async for token in token_stream:
        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"

    logger.info(f"[rag] STREAM DONE — total time: {time.perf_counter() - t0:.2f}s")


# ---------------------------------------------------------------------------
# Helpers privati
# ---------------------------------------------------------------------------

def _build_sources(nodes: list[NodeWithScore]) -> list[dict]:
    """
    Estrae le sorgenti uniche dai nodi recuperati.
    Deduplica per entry_id — più chunk della stessa entry diventano una sola sorgente.
    """
    seen: set[str] = set()
    sources: list[dict] = []

    for node_with_score in nodes:
        metadata = node_with_score.node.metadata
        entry_id = metadata.get("entry_id", "")

        if entry_id in seen:
            continue
        seen.add(entry_id)

        sources.append({
            "entry_id": entry_id,
            "title":      metadata.get("entry_title", ""),
            "entry_type": metadata.get("entry_type", ""),
            "section":    metadata.get("heading"),
        })

    return sources


def _build_context_message(question: str, nodes: list[NodeWithScore]) -> str:
    """
    Costruisce il messaggio utente con contesto + domanda.

    Ogni chunk include il titolo dell'entry e l'heading della sezione
    per dare all'LLM il contesto necessario per citare correttamente le fonti.
    """
    context_parts: list[str] = []

    for node_with_score in nodes:
        metadata = node_with_score.node.metadata
        title   = metadata.get("entry_title", "Senza titolo")
        heading = metadata.get("heading") or "Contenuto"
        text    = node_with_score.node.get_content()

        context_parts.append(f"[{title}] — {heading}\n{text}")

    context = "\n\n---\n\n".join(context_parts)

    logger.info(
        f"[rag] Context built — {len(nodes)} chunk(s), "
        f"{len(set(n.node.metadata.get('entry_id') for n in nodes))} source(s), "
        f"{len(context)} chars"
    )

    return f"CONTESTO:\n{context}\n\nDOMANDA: {question}"