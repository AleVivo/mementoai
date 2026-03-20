from bson import ObjectId
from bson.errors import InvalidId
from app.models.chunk import ChunkDocument, ChunkSearchResult
from app.db.client import get_db

async def insert_chunks(chunks: list[ChunkDocument]) -> None:
    if not chunks:
        return
    
    documents = [chunk.model_dump(by_alias=True, exclude_none=True) for chunk in chunks]
    await get_db().chunks.insert_many(documents)

async def delete_chunks_by_entry_id(entry_id: str) -> int:
    try:
        oid = ObjectId(entry_id)
    except InvalidId:
        return 0
    
    result = await get_db().chunks.delete_many({"entry_id": oid})
    return result.deleted_count

async def vector_search_chunks(
    embedding: list[float],
    project_ids: list[str] | None = None,
    top_k: int = 5
) -> list[ChunkSearchResult]:
    inner = {
        "exact": False,
        "index": "chunks_vector_index",
        "queryVector": embedding,
        "path": "embedding",
        "numCandidates": top_k * 20,
        "limit": top_k,
    }

    if project_ids:
        inner["filter"] = {"project_id": {"$in": project_ids}}

    pipeline = [
        {"$vectorSearch": inner},
        {
            "$project": {
                "embedding": 0,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    cursor = await get_db().chunks.aggregate(pipeline)
    docs = await cursor.to_list(length=top_k)
    return [
        ChunkSearchResult(
            chunk_id=r["_id"],
            entry_id=r["entry_id"],
            chunk_index=r["chunk_index"],
            heading=r.get("heading"),
            text=r["text"],
            score=r["score"],
            project_id=r["project_id"],
            entry_type=r["entry_type"],
            entry_title=r["entry_title"],
        )
        for r in docs
    ]

async def delete_chunks_by_project_id(project_id: str) -> int:
    result = await get_db().chunks.delete_many({"project_id": project_id})
    return result.deleted_count