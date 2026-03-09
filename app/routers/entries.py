from fastapi import APIRouter, Query, HTTPException, Response
from app.models.entry import EntryResponse, EntryDocument, EntryCreate, EntryUpdate
from app.db import mongo
from typing import List, Optional
from app.services import entry_service


router = APIRouter()

@router.get("", response_model=List[EntryResponse])
async def get_entries(
    project: Optional[str] = Query(default=None, description="Filter entries by project"),
    type: Optional[str] = Query(default=None, description="Filter entries by type"),
    week: Optional[str] = Query(default=None, description="Filter entries by week (format: YYYY-Www)"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of entries to return"),
    skip: int = Query(default=0, ge=0, description="Number of entries to skip for pagination")
):
    return await entry_service.get_entries(project=project, type=type, week=week, limit=limit, skip=skip)

@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry_by_id(entry_id: str):
    entry = await entry_service.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.post("", response_model=EntryResponse, status_code=201)
async def create_entry(entry: EntryCreate):
    saved = await entry_service.create_entry(entry)
    return saved

@router.put("/{entry_id}", response_model=EntryResponse)
async def update_entry(entry_id: str, update: EntryUpdate):
    updated = await entry_service.update_entry(entry_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="Entry not found")
    return updated

@router.delete("/{entry_id}", status_code=204)
async def delete_entry(entry_id: str):
    deleted = await entry_service.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return Response(status_code=204)

@router.post("/{entry_id}/index", response_model=EntryResponse)
async def index_entry(entry_id: str):
    indexed = await entry_service.index_entry(entry_id)
    if not indexed:
        raise HTTPException(status_code=404, detail="Entry not found")
    return indexed