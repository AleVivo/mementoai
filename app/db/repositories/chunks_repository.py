import asyncio

from app.models.chunk import ChunkSearchResult, MetadataFields
from app.db.client import get_db


async def delete_chunks_by_entry_id(entry_id: str) -> int:
    result = await get_db().chunks.delete_many(
        {f"metadata.{MetadataFields.ENTRY_ID}": entry_id}
    )
    return result.deleted_count


async def delete_chunks_by_project_id(project_id: str) -> int:
    result = await get_db().chunks.delete_many(
        {f"metadata.{MetadataFields.PROJECT_ID}": project_id}
    )
    return result.deleted_count


async def delete_docstore_nodes_by_entry_id(entry_id: str) -> None:
    """
    Elimina i nodi padre (root + intermedi) da MongoDocumentStore per l'entry indicata.

    Richiesto prima di re-indicizzare una entry per evitare nodi orfani nella
    collection node_docstore/data. Usa delete_ref_doc() di LlamaIndex che rimuove
    tutti i nodi il cui ref_doc_id corrisponde all'entry_id (= Document.id_ impostato
    in html_reader.py).

    Il metodo è sync lato LlamaIndex — viene eseguito in un thread separato
    per non bloccare l'event loop di FastAPI/uvicorn.
    """
    from app.services.retrieval.llama_store import get_docstore
    docstore = get_docstore()
    await asyncio.to_thread(
        docstore.delete_ref_doc,
        entry_id,
        raise_error=False,
    )