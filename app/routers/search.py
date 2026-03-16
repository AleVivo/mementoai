from app.models.search import SearchRequest, SearchResult
from app.models.user import UserResponse
from fastapi import APIRouter, Depends
from app.services import search_service
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("", response_model=list[SearchResult])
async def search_entries(request: SearchRequest, current_user: UserResponse = Depends(get_current_user)):
    return await search_service.search_entries(request)
