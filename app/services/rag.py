import json
import logging
import time
from app.models.chunk import ChunkSearchResult
from app.services import ollama
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

def build_prompt(question: str, results: list[ChunkSearchResult]) -> str:
    # De-duplica i chunk per entry prima di costruire il contesto
    # così ogni fonte ha un ref_num univoco e stabile
    seen: dict[str, int] = {}
    unique_chunks: list[tuple[int, ChunkSearchResult]] = []
    for chunk in results:
        eid = str(chunk.entry_id)
        if eid not in seen:
            seen[eid] = len(seen) + 1
        unique_chunks.append((seen[eid], chunk))

    context_parts = []
    for ref, chunk in unique_chunks:
        section_label = chunk.heading if chunk.heading else "Contenuto"
        context_parts.append(
            f"[{chunk.entry_title}] — {section_label}\n"
            f"{chunk.text}"
        )
    context = "\n\n---\n\n".join(context_parts)
    logger.info(f"[rag] Context built — {len(unique_chunks)} chunk(s), {len(seen)} source(s), prompt context length: {len(context)} chars")

    prompt = f"""Sei un assistente per team di sviluppo. Rispondi alla domanda usando SOLO le informazioni fornite nel contesto.
        Se la risposta non è nel contesto, dillo esplicitamente.
        Cita le fonti usando ESCLUSIVAMENTE il titolo tra parentesi quadre esattamente come appare nel contesto, es. [Titolo della nota]. Non inventare titoli.

        CONTESTO:
        {context}

        DOMANDA: {question}

        RISPOSTA:"""
    return prompt
        
# DEPRECATED: this was the original non-streaming implementation of the RAG response generation, kept here for reference until we are sure we won't need it anymore. The streaming version is now the default and only implementation used in the chat endpoint.
async def return_chat_response(question: str, results: list[ChunkSearchResult]) -> dict:
    if not results:
        logger.warning("[rag] No chunks retrieved — returning empty answer")
        return {
            "answer": "Nessuna informazione rilevante trovata nella knowledge base.",
            "sources": [],
        }
    
    prompt = build_prompt(question, results)
    logger.info(f"[rag] Calling Ollama generate — prompt length: {len(prompt)} chars")
    t0 = time.perf_counter()
    answer = await ollama.generate_by_prompt(prompt)
    logger.info(f"[rag] Ollama generate done ({time.perf_counter()-t0:.2f}s) — answer length: {len(answer)} chars")
    return {
        "answer": answer,
    }

async def stream_chat_response(
    question: str, 
    results: list[ChunkSearchResult]) -> AsyncGenerator[str,None]:
    """
    Async generator che yielda eventi SSE per POST /chat.
    Ogni yield è una stringa nel formato "data: {...}\n\n".
    """
    # if not results:
    #     logger.warning("[rag] No chunks retrieved — returning empty answer")
    #     return {
    #         "answer": "Nessuna informazione rilevante trovata nella knowledge base.",
    #         "sources": [],
    #     }
    prompt = build_prompt(question, results)
    async for token in ollama.stream_by_prompt(prompt):
        event = {"type": "token", "content": token}
        yield f"data: {json.dumps(event)}\n\n"
        
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

