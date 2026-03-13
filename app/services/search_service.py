import logging
import time
from app.models.search import SearchRequest
from app.models.chunk import ChunkSearchResult
from app.services import embedding as embedding_service
from app.db import mongo, chunks_mongo

logger = logging.getLogger(__name__)


async def search_entries(request: SearchRequest) -> list[ChunkSearchResult]:
    logger.info(f"[search] Generating embedding for query: {request.query!r}")
    t0 = time.perf_counter()
    embedding = await embedding_service.generate_embedding(request.query)
    logger.info(f"[search] Embedding done ({time.perf_counter()-t0:.2f}s) — running vector search (top_k={request.top_k}, project={request.project!r})")

    t1 = time.perf_counter()
    results = await chunks_mongo.vector_search_chunks(
        embedding,
        request.project,
        request.top_k,
    )
    logger.info(f"[search] Vector search done ({time.perf_counter()-t1:.2f}s) — {len(results)} chunk(s) found")
    for r in results:
        logger.info(f"  chunk: entry={r.entry_title!r}, heading={r.heading!r}, score={r.score:.4f}, chars={len(r.text)}")
    return results