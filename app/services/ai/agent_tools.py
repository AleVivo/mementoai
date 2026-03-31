"""
Funzioni Python che l'agente può invocare come tool.

Ogni funzione delega al codice esistente — nessuna pipeline duplicata:
- search_semantic  → retrieval/retriever.py (LlamaIndex: embedding + $vectorSearch)
- filter_entries   → entry_repository.get_entries
- get_entry        → entry_repository.get_entry_by_id
- count_entries    → aggregazione $facet diretta su MongoDB
"""

from typing import Optional

from app.db.client import get_db
from app.db.repositories import entry_repository
from app.mappers import entry_mapper
from app.services.retrieval import reranker, retriever as retriever_module


# ---------------------------------------------------------------------------
# TOOL 1 — Ricerca semantica
#
# Prima: embedder.generate_embedding() + chunks_repository.vector_search_chunks()
# Ora:   get_retriever().aretrieve() — LlamaIndex gestisce embedding e search
#
# Il disaccoppiamento è completo: questo tool non sa che sotto c'è LlamaIndex.
# Se domani cambia il retriever, cambia solo retriever.py.
# ---------------------------------------------------------------------------

async def search_semantic(
    query: str,
    limit: int = 5,
    project_ids: list[str] | None = None,
) -> list[dict]:
    """
    Cerca nella knowledge base per significato semantico.
    Ritorna chunk di testo serializzati come dict JSON.

    Pipeline: $vectorSearch (top_k=limit*2) → AutoMerging → SentenceTransformerRerank (top_n=3)
    """
    # top_k moltiplicato per dare più candidati al reranker
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

async def filter_entries(
    project_ids: list[str] | None = None,
    entry_type: Optional[str] = None,
    week: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
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

async def get_entry(entry_id: str) -> Optional[dict]:
    result = await entry_repository.get_entry_by_id(entry_id)
    if result is None:
        return None
    return entry_mapper.doc_to_response(result).model_dump(mode="json")


# ---------------------------------------------------------------------------
# TOOL 4 — Conteggio e aggregazione (invariato)
# ---------------------------------------------------------------------------

async def count_entries(
    project_ids: list[str] | None = None,
    entry_type: Optional[str] = None,
    week: Optional[str] = None,
) -> dict:
    """
    Conta le entry con breakdown per tipo e progetto.
    Returns: {"total": N, "by_type": {...}, "by_project": {...}}
    """
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