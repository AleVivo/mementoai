from bson import ObjectId
from app.models.chunk import ChunkDocument, ChunkSearchResult
from app.db.mongo import db

chunks_collection = db["chunks"]

async def insert_chunks(chunks: list[ChunkDocument]) -> None:
    if not chunks:
        return
    
    documents = [chunk.model_dump(by_alias=True, exclude_none=True) for chunk in chunks]
    await chunks_collection.insert_many(documents)

async def delete_chunks_by_entry_id(entry_id: str) -> int:
    try:
        oid = ObjectId(entry_id)
    except Exception:
        return 0
    
    result = await chunks_collection.delete_many({"entry_id": oid})
    return result.deleted_count

async def vector_search_chunks(
    embedding: list[float],
    project: str | None = None,
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

    if project:
        inner["filter"] = {"project": {"$eq": project}}

    pipeline = [
        {"$vectorSearch": inner},
        {
            "$project": {
                "embedding": 0,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    cursor = await chunks_collection.aggregate(pipeline)
    docs = await cursor.to_list(length=top_k)
    return [
        ChunkSearchResult(
            chunk_id=r["_id"],
            entry_id=r["entry_id"],
            chunk_index=r["chunk_index"],
            heading=r.get("heading"),
            text=r["text"],
            score=r["score"],
            project=r["project"],
            entry_type=r["entry_type"],
            entry_title=r["entry_title"],
        )
        for r in docs
    ]