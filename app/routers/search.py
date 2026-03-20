from app.models.search import SearchRequest, SearchResult
from app.models.user import UserResponse
from fastapi import APIRouter, Depends
from app.services.ai import search_service
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("", response_model=list[SearchResult])
async def search_entries(request: SearchRequest, current_user: UserResponse = Depends(get_current_user)):
    chunks = await search_service.vector_search_chunks(request, current_user)
    return [
        SearchResult(
            entry_id=str(chunk.entry_id),
            entry_type=chunk.entry_type,
            entry_title=chunk.entry_title,
            project_id=chunk.project_id,
            heading=chunk.heading,
            text=chunk.text,
            score=chunk.score,
        )
        for chunk in chunks
    ]
