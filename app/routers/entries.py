from fastapi import APIRouter, Query, HTTPException, Response, Depends

from app.dependencies.entries import get_entry_and_verify_membership
from app.dependencies.project import require_project_member
from app.mappers import entry_mapper
from app.models.entry import EntryResponse, EntryCreate, EntryUpdate, EntryDocument
from app.models.user import UserResponse
from typing import List, Optional
from app.services.domain import entry_service
from app.dependencies.auth import get_current_user


router = APIRouter()

@router.get("", response_model=List[EntryResponse])
async def get_entries(
    project_id: Optional[str] = Query(default=None, description="Filter entries by project"),
    entry_type: Optional[str] = Query(default=None, description="Filter entries by entry_type"),
    week: Optional[str] = Query(default=None, description="Filter entries by week (format: YYYY-Www)"),
    folder_id: Optional[str] = Query(default=None, description="Filter entries by folder (direct children only unless recursive=true)"),
    recursive: bool = Query(default=False, description="Include entries in all descendant folders"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of entries to return"),
    skip: int = Query(default=0, ge=0, description="Number of entries to skip for pagination"),
    _member: tuple = Depends(require_project_member)
):
    return await entry_service.get_entries(
        project_id=project_id,
        entry_type=entry_type,
        week=week,
        limit=limit,
        skip=skip,
        folder_id=folder_id,
        recursive=recursive,
    )

@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry_by_id(entry: EntryDocument = Depends(get_entry_and_verify_membership),
):
    return entry_mapper.doc_to_response(entry)


@router.post("", response_model=EntryResponse, status_code=201)
async def create_entry(entry: EntryCreate, current_user: UserResponse = Depends(get_current_user)):
    saved = await entry_service.create_entry(entry, current_user)
    return saved

@router.put("/{entry_id}", response_model=EntryResponse)
async def update_entry(entry_id: str, update: EntryUpdate, current_user: UserResponse = Depends(get_current_user)):
    updated = await entry_service.update_entry(entry_id, update, current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Entry not found")
    return updated

@router.delete("/{entry_id}", status_code=204)
async def delete_entry(entry_id: str, current_user: UserResponse = Depends(get_current_user)):
    deleted = await entry_service.delete_entry(entry_id, current_user)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return Response(status_code=204)

@router.post("/{entry_id}/index", response_model=EntryResponse)
async def index_entry(entry_id: str, current_user: UserResponse = Depends(get_current_user)):
    indexed = await entry_service.index_entry(entry_id, current_user)
    if not indexed:
        raise HTTPException(status_code=404, detail="Entry not found")
    return indexed

    return indexed