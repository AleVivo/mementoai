"""
Funzioni Python che l'agente può invocare come tool.

Ogni funzione delega al codice esistente — nessuna pipeline duplicata:
- search_semantic  → embedding_service + chunks_mongo (come search_service.py)
- filter_entries   → mongo.get_entries
- get_entry        → mongo.get_entry_by_id
- count_entries    → aggregazione diretta su entries_collection (unico caso nuovo)
"""

from typing import Optional
from app.services import embedding as embedding_service
from app.db import chunks_mongo, mongo
from app.db.mongo import entries_collection


# ---------------------------------------------------------------------------
# TOOL 1 — Ricerca semantica
#
# Invece di riscrivere la pipeline $vectorSearch, deleghiamo agli stessi
# moduli che usa search_service.py: generate_embedding + vector_search_chunks.
#
# L'unica differenza rispetto a search_service.search_entries è che
# accettiamo parametri diretti invece di un SearchRequest — più comodo
# da chiamare dall'agente.
# ---------------------------------------------------------------------------

async def search_semantic(query: str, limit: int = 5, project: str | None = None) -> list[dict]:
    """
    Cerca chunk nella knowledge base per significato semantico.

    Args:
        query:   testo libero della domanda
        limit:   numero massimo di chunk da restituire (default 5)
        project: filtra per progetto (opzionale)

    Returns:
        lista di dict con i campi del chunk + score di similarità
    """
    embedding = await embedding_service.generate_embedding(query)
    results = await chunks_mongo.vector_search_chunks(embedding, project, limit)

    # ChunkSearchResult è un modello Pydantic — lo convertiamo in dict
    # perché l'agente lavorerà con dati JSON-serializzabili.
    # model_dump() è il metodo Pydantic v2 che sostituisce il vecchio .dict()
    return [r.model_dump() for r in results]


# ---------------------------------------------------------------------------
# TOOL 2 — Filtro per campi esatti
#
# Delega a mongo.get_entries che già costruisce il filtro MongoDB.
# Il parametro "author" non esiste in get_entries, quindi non lo esponiamo
# invece di inventare logica che non c'è.
# ---------------------------------------------------------------------------

async def filter_entries(
    project: Optional[str] = None,
    entry_type: Optional[str] = None,
    week: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Filtra entry per campi esatti.

    Args:
        project:    nome del progetto
        entry_type: "adr" | "postmortem" | "update"
        week:       formato YYYY-Www (es. "2026-W10")
        limit:      max risultati (default 20)

    Returns:
        lista di entry serializzate (senza embedding)
    """
    results = await mongo.get_entries(
        project=project,
        entry_type=entry_type,
        week=week,
        limit=limit,
        skip=0,
    )

    return [r.model_dump(mode="json", exclude={"embedding"}) for r in results]


# ---------------------------------------------------------------------------
# TOOL 3 — Recupero singola entry per ID
#
# Delega direttamente a mongo.get_entry_by_id.
# ---------------------------------------------------------------------------

async def get_entry(id: str) -> Optional[dict]:
    """
    Recupera una singola entry completa tramite il suo ID MongoDB.

    Args:
        id: stringa ObjectId MongoDB

    Returns:
        dict con tutti i campi dell'entry (escluso embedding), None se non trovata
    """
    result = await mongo.get_entry_by_id(id)
    if result is None:
        return None
    return result.model_dump(mode="json", exclude={"embedding"})


# ---------------------------------------------------------------------------
# TOOL 4 — Conteggio e aggregazione
#
# Unico tool che accede direttamente a entries_collection invece di
# passare per una funzione esistente — perché $facet non è implementato
# in mongo.py. La query è semplice e autocontenuta.
# ---------------------------------------------------------------------------

async def count_entries(
    project: Optional[str] = None,
    entry_type: Optional[str] = None,
    week: Optional[str] = None,
) -> dict:
    """
    Conta le entry che corrispondono ai filtri con breakdown per tipo e progetto.

    Args:
        project:    filtra per progetto
        entry_type: filtra per tipo ("adr" | "postmortem" | "update")
        week:       filtra per settimana YYYY-Www

    Returns:
        {"total": N, "by_type": {"adr": N, ...}, "by_project": {"X": N, ...}}
    """
    match_stage: dict = {}
    if project:
        match_stage["project"] = project
    if entry_type:
        match_stage["entry_type"] = entry_type  # coerente col tuo campo MongoDB
    if week:
        match_stage["week"] = week

    pipeline = [
        {"$match": match_stage},
        {
            "$facet": {
                "total": [{"$count": "count"}],
                "by_type": [{"$group": {"_id": "$entry_type", "count": {"$sum": 1}}}],
                "by_project": [{"$group": {"_id": "$project", "count": {"$sum": 1}}}],
            }
        },
    ]

    cursor = await entries_collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        return {"total": 0, "by_type": {}, "by_project": {}}

    facets = result[0]
    total = facets["total"][0]["count"] if facets["total"] else 0
    by_type = {item["_id"]: item["count"] for item in facets["by_type"] if item["_id"]}
    by_project = {item["_id"]: item["count"] for item in facets["by_project"] if item["_id"]}

    return {"total": total, "by_type": by_type, "by_project": by_project}