from app.models.search import SearchRequest, SearchResult
from app.services import embedding as embedding_service
from app.db import mongo

async def search_entries(request: SearchRequest) -> list[SearchResult]:
    embedding = await embedding_service.generate_embedding(request.query)
    results = await mongo.vector_search(embedding, request.project, request.top_k)
    return results