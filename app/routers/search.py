from app.models.search import SearchRequest, SearchResult
from fastapi import APIRouter
from app.services import search_service

router = APIRouter()

@router.post("", response_model=list[SearchResult])
async def search_entries(request: SearchRequest):
    return await search_service.search_entries(request)