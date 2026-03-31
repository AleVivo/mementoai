"""
Pipeline RAG completa con streaming SSE.

Responsabilità:
- Recupera i chunk rilevanti tramite retrieval/retriever.py
- Sintetizza la risposta tramite LlamaIndex QueryEngine + ResponseSynthesizer
- Streamma la risposta dell'LLM via SSE

Tracing Langfuse v4:
- stream_rag() è AsyncGenerator — NON supportato da @observe.
  Usa start_observation() manuale con try/finally per garantire
  la chiusura dello span anche in caso di disconnessione del client.
- _execute_rag() è una coroutine normale — usa @observe.
  Diventa automaticamente figlio dello span aperto in stream_rag().

Separazione logica / trasporto SSE:
- _execute_rag() contiene la logica: retrieval + reranking + QueryEngine.
  Ritorna AsyncStreamingResponse — non consuma il generator.
- stream_rag() gestisce il trasporto SSE: consuma il generator,
  estrae le sources dopo lo stream, chiude lo span Langfuse.
"""

import json
import logging
import time
from typing import AsyncGenerator

from langfuse import observe
from llama_index.core import ChatPromptTemplate
from llama_index.core.base.response.schema import AsyncStreamingResponse
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import ResponseMode, get_response_synthesizer
from llama_index.core.schema import NodeWithScore

from app.models.chat import ChatRequest
from app.models.user import UserResponse
from app.services.domain import project_service
from app.services.retrieval import reranker, retriever
from app.observability import langfuse_integration

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Prompt template
# ─────────────────────────────────────────────────────────────────────────────
# Separato dal codice per facilità di modifica e test.
# {context_str} e {query_str} sono i placeholder che LlamaIndex
# riempie automaticamente con i chunk recuperati e la domanda dell'utente.

_SYSTEM_PROMPT = ChatMessage(
    role=MessageRole.SYSTEM,
    content=(
        "Sei un assistente per team di sviluppo. "
        "Rispondi alla domanda usando SOLO le informazioni fornite nel contesto. "
        "Se il contesto è vuoto o non contiene informazioni rilevanti, rispondi: "
        '"Non ho trovato informazioni su questo argomento nella knowledge base." '
        "Cita le fonti usando ESCLUSIVAMENTE il titolo tra parentesi quadre "
        "esattamente come appare nel contesto, es. [Titolo della nota]. "
        "Non inventare titoli. Non aggiungere informazioni esterne al contesto. "
        "Rispondi in italiano."
    ),
)

_USER_TEMPLATE = ChatMessage(
    role=MessageRole.USER,
    content=(
        "Contesto dalla knowledge base:\n"
        "------------------------------\n"
        "{context_str}\n"
        "------------------------------\n"
        "Domanda: {query_str}\n"
        "Risposta:"
    ),
)

_RAG_PROMPT_TEMPLATE = ChatPromptTemplate(
    message_templates=[_SYSTEM_PROMPT, _USER_TEMPLATE]
)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline RAG
# ─────────────────────────────────────────────────────────────────────────────

async def _execute_rag(
    question: str,
    project_ids: list[str],
    top_k: int,
) -> AsyncStreamingResponse:
    """
    Cuore della pipeline RAG.

    Costruisce il QueryEngine con retriever, synthesizer e reranker,
    esegue aquery() e ritorna l'AsyncStreamingResponse.

    NON consuma il generator — questo è responsabilità di stream_rag()
    che gestisce anche il trasporto SSE e il tracing post-stream.

    @observe crea automaticamente uno span figlio dello span attivo
    in stream_rag() grazie alla propagazione del contesto OTel.

    Args:
        question:    domanda dell'utente
        project_ids: ID dei progetti su cui filtrare la ricerca
        top_k:       numero di chunk da recuperare prima del reranking
    """
    t0 = time.perf_counter()
    logger.info(f"[rag] START — question: {question!r}, projects: {project_ids!r}")

    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever.get_retriever(project_ids=project_ids, top_k=top_k),
        response_synthesizer=get_response_synthesizer(
            response_mode=ResponseMode.COMPACT,
            streaming=True,
            text_qa_template=_RAG_PROMPT_TEMPLATE,
        ),
        node_postprocessors=[reranker.get_reranker()],
    )

    response = await query_engine.aquery(question)

    # Verifica difensiva — se streaming=True è impostato correttamente
    # il tipo ritornato è sempre AsyncStreamingResponse. Se non lo è
    # significa che Settings.llm non è configurato o streaming è False.
    if not isinstance(response, AsyncStreamingResponse):
        raise RuntimeError(
            f"[rag] Risposta inattesa dal QueryEngine: {type(response)}. "
            "Verifica che streaming=True sia impostato nel ResponseSynthesizer "
            "e che Settings.llm sia configurato correttamente."
        )

    logger.info(f"[rag] QueryEngine pronto ({time.perf_counter() - t0:.2f}s)")
    return response


async def stream_rag(
    request: ChatRequest,
    current_user: UserResponse,
) -> AsyncGenerator[str, None]:
    """
    Entry point pubblico — chiamato dal router POST /chat.

    Gestisce: autorizzazione, esecuzione RAG, trasporto SSE, tracing Langfuse.

    Perché NON usa @observe:
    @observe non supporta AsyncGenerator (inspect.isgenerator() ritorna False
    per async generator in Python). Lo span viene aperto manualmente con
    start_observation() e chiuso in finally — garantito anche se il client
    disconnette prima della fine dello stream.

    Ordine eventi SSE:
    1. token (streaming) — il frontend mostra la risposta mentre arriva
    2. sources           — disponibili solo dopo aver consumato il generator
    3. done              — segnale di fine stream

    Args:
        request:      ChatRequest con question, project_id, top_k
        current_user: utente autenticato (per autorizzazione e tracing)
    """
    from langfuse import get_client

    langfuse = get_client()

    with langfuse.start_as_current_observation(
        name="rag_call",
        as_type="span",
        input={
            "question": request.question,
            "project_ids": request.project_id
            }
    ) as observation:
        
        full_response = ""
        t0 = time.perf_counter()


        project_ids = await project_service.resolve_project_ids(
            project_id=request.project_id,
            user_id=current_user.id,
        )
        
        sources: list[dict] = []

        try:
            # _execute_rag() crea uno span figlio di root_span tramite @observe
            streaming_response = await _execute_rag(
                question=request.question,
                project_ids=project_ids,
                top_k=request.top_k,
            )

            # Streaming token-by-token
            # source_nodes è popolato solo DOPO aver consumato tutto il generator
            async for token in streaming_response.async_response_gen():
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Dopo lo stream — source_nodes è ora popolato
            sources = _build_sources(streaming_response.source_nodes)
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            logger.info(f"[rag] STREAM DONE — total time: {time.perf_counter() - t0:.2f}s")

        except Exception as e:
            logger.exception(f"[rag] ERRORE durante lo stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            raise

        observation.update(output=full_response)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers privati
# ─────────────────────────────────────────────────────────────────────────────

def _build_sources(nodes: list[NodeWithScore]) -> list[dict]:
    """
    Estrae le sorgenti uniche dai nodi recuperati.

    Deduplica per entry_id — più chunk della stessa entry
    diventano una sola sorgente nel payload SSE.
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
            "entry_id":   entry_id,
            "title":      metadata.get("entry_title", ""),
            "entry_type": metadata.get("entry_type", ""),
            "section":    metadata.get("heading"),
        })

    return sources