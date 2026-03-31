"""
Funzioni Python che l'agente può invocare come tool.

Ogni funzione delega al codice esistente — nessuna pipeline duplicata:
- search_semantic  → retrieval/retriever.py (LlamaIndex: embedding + $vectorSearch)
- filter_entries   → entry_repository.get_entries
- get_entry        → entry_repository.get_entry_by_id
- count_entries    → aggregazione $facet diretta su MongoDB
"""

from typing import Annotated, Literal, Optional

from app.db.client import get_db
from app.db.repositories import entry_repository
from app.mappers import entry_mapper
from app.services.retrieval import reranker, retriever as retriever_module

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState


# ---------------------------------------------------------------------------
# TOOL 1 — Ricerca semantica
#
# Prima: embedder.generate_embedding() + chunks_repository.vector_search_chunks()
# Ora:   get_retriever().aretrieve() — LlamaIndex gestisce embedding e search
#
# Il disaccoppiamento è completo: questo tool non sa che sotto c'è LlamaIndex.
# Se domani cambia il retriever, cambia solo retriever.py.
# ---------------------------------------------------------------------------

@tool
async def search_semantic(
    query: str,
    limit: int = 5,
    project_ids: Annotated[list[str] | None, InjectedState("project_ids")] = None,
) -> list[dict]:
    """
    Cerca nella knowledge base per significato semantico.
    USA QUESTO TOOL per domande su contenuto, tecnologie, decisioni,
    problemi — qualsiasi domanda aperta su "cosa", "perché", "come".
    Esempi: "usiamo qualche db?", "quali problemi abbiamo avuto con Redis?",
    "come gestiamo l'autenticazione?".
    NON usare per conteggi o per recuperare entry per data/tipo esatto.
    """
    retriever_instance = retriever_module.get_retriever(project_ids=project_ids, top_k=limit * 2)
    nodes = await retriever_instance.aretrieve(query)
    nodes = reranker.get_reranker().postprocess_nodes(nodes, query_str=query)

    return [
        {
            "node_id":    node.node.node_id,
            "entry_id":   node.node.metadata.get("entry_id", ""),
            "entry_title": node.node.metadata.get("entry_title", ""),
            "entry_type": node.node.metadata.get("entry_type", ""),
            "project_id": node.node.metadata.get("project_id", ""),
            "heading":    node.node.metadata.get("heading"),
            "chunk_index": node.node.metadata.get("chunk_index", 0),
            "text":       node.node.get_content(),
            "score":      node.score or 0.0,
        }
        for node in nodes
    ]


# ---------------------------------------------------------------------------
# TOOL 2 — Filtro per campi esatti (invariato)
# ---------------------------------------------------------------------------

@tool
async def filter_entries(
    project_ids: Annotated[list[str] | None, InjectedState("project_ids")] = None,
    entry_type: Literal["adr", "postmortem", "update"] | None = None,
    week: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Filtra entry per criteri esatti: tipo (adr/postmortem/update) e settimana.
    USA QUESTO TOOL solo quando la domanda specifica criteri strutturati,
    NON per domande sul contenuto.
    Esempi corretti: "tutti gli ADR", "gli update di questa settimana", "l'ultimo postmortem".
    Esempi sbagliati: "usiamo qualche db?", "quali problemi abbiamo avuto?" — per questi usa search_semantic.
    """
    results = await entry_repository.get_entries(
        project_ids=project_ids,
        entry_type=entry_type,
        week=week,
        limit=limit,
        skip=0,
    )
    return [entry_mapper.doc_to_response(r).model_dump(mode="json") for r in results]


# ---------------------------------------------------------------------------
# TOOL 3 — Recupero singola entry per ID (invariato)
# ---------------------------------------------------------------------------

@tool
async def get_entry(
    entry_id: str,
    project_ids: Annotated[list[str] | None, InjectedState("project_ids")] = None
) -> Optional[dict]:
    """Recupera una singola entry completa tramite il suo ID MongoDB. 
    Usa questo tool SOLO dopo search_semantic, quando il chunk 
    restituito non contiene abbastanza contesto e vuoi leggere 
    il contenuto completo dell'entry originale. 
    NON usarlo dopo filter_entries — quelle entry sono già complete. 
    IMPORTANTE: usa SOLO ID reali ottenuti dal campo entry_id 
    di search_semantic — non inventare mai un ID.""" 
    result = await entry_repository.get_entry_by_id_and_project_id(entry_id, project_ids or [])
    if result is None:
        return None
    return entry_mapper.doc_to_response(result).model_dump(mode="json")


# ---------------------------------------------------------------------------
# TOOL 4 — Conteggio e aggregazione (invariato)
# ---------------------------------------------------------------------------

@tool
async def count_entries(
    project_ids: Annotated[list[str] | None, InjectedState("project_ids")] = None,
    entry_type: Optional[str] = None,
    week: Optional[str] = None,
) -> dict:
    """Conta le entry che corrispondono ai filtri e restituisce 
    un breakdown per tipo e per progetto. 
    Usa questo tool per domande quantitative: 'quanti post-mortem', 
    'qual è il progetto più attivo', 'quanto spesso scriviamo ADR'."""
    match_stage: dict = {}
    if project_ids:
        match_stage["project_id"] = {"$in": project_ids}
    if entry_type:
        match_stage["entry_type"] = entry_type
    if week:
        match_stage["week"] = week

    pipeline = [
        {"$match": match_stage},
        {
            "$facet": {
                "total":      [{"$count": "count"}],
                "by_type":    [{"$group": {"_id": "$entry_type",  "count": {"$sum": 1}}}],
                "by_project": [{"$group": {"_id": "$project_id", "count": {"$sum": 1}}}],
            }
        },
    ]

    cursor = await get_db().entries.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        return {"total": 0, "by_type": {}, "by_project": {}}

    facets = result[0]
    total      = facets["total"][0]["count"] if facets["total"] else 0
    by_type    = {item["_id"]: item["count"] for item in facets["by_type"]    if item["_id"]}
    by_project = {item["_id"]: item["count"] for item in facets["by_project"] if item["_id"]}

    return {"total": total, "by_type": by_type, "by_project": by_project}