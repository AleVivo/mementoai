import logging
import time
from app.models.chunk import ChunkSearchResult
from app.services import ollama

logger = logging.getLogger(__name__)


async def return_chat_response(question: str, results: list[ChunkSearchResult]) -> dict:
    if not results:
        logger.warning("[rag] No chunks retrieved — returning empty answer")
        return {
            "answer": "Nessuna informazione rilevante trovata nella knowledge base.",
            "sources": [],
        }
    
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
    
    logger.info(f"[rag] Calling Ollama generate — prompt length: {len(prompt)} chars")
    t0 = time.perf_counter()
    answer = await ollama.generate_by_prompt(prompt)
    logger.info(f"[rag] Ollama generate done ({time.perf_counter()-t0:.2f}s) — answer length: {len(answer)} chars")

    sources = []
    for eid, ref in seen.items():
        # Trova il primo chunk di questa entry per i metadati
        chunk = next(c for _, c in unique_chunks if str(c.entry_id) == eid)
        sources.append({
            "ref": ref,
            "entry_id": eid,
            "title": chunk.entry_title,
            "type": chunk.entry_type,
            "score": chunk.score,
            "section": chunk.heading,
        })

    return {
        "answer": answer,
        "sources": sources
    }