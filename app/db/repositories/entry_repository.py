from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId

from app.models.entry import EntryDocument
from app.db.client import get_db


async def create_entry(entry_document: EntryDocument) -> EntryDocument:
    document = entry_document.model_dump(by_alias=True, exclude_none=True)
    result = await get_db().entries.insert_one(document)
    saved = await get_db().entries.find_one({"_id": result.inserted_id})
    return EntryDocument.model_validate(saved)

async def get_entries(
        project_ids: Optional[list[str]],
        entry_type: Optional[str],
        week: Optional[str],
        limit: int,
        skip: int) -> list[EntryDocument]:
    query: dict = {}
    if project_ids:
        oids = [ObjectId(pid) for pid in project_ids]
        query["project_id"] = {"$in": oids} if len(oids) > 1 else oids[0]
    if entry_type:
        query["entry_type"] = entry_type
    if week:
        query["week"] = week

    cursor = get_db().entries.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [EntryDocument.model_validate(doc) for doc in docs]

async def get_entry_by_id(entry_id: str) -> Optional[EntryDocument]:
    try:
        oid = ObjectId(entry_id)
    except InvalidId:
        return None
    
    entry = await get_db().entries.find_one({"_id": oid})
    return EntryDocument.model_validate(entry) if entry else None

async def delete_entry_by_id(entry_id: str) -> bool:
    try:
        oid = ObjectId(entry_id)
    except InvalidId:
        return False
    
    result = await get_db().entries.delete_one({"_id": oid})
    return result.deleted_count == 1

async def update_entry(entry_id: str, fields: dict) -> Optional[EntryDocument]:
    try:
        oid = ObjectId(entry_id)
    except InvalidId:
        return None
    
    if not fields:
        return await get_entry_by_id(entry_id)
    
    doc = await get_db().entries.find_one_and_update(
        {"_id": oid},
        {"$set": fields},
        return_document=True,
    )
    return EntryDocument.model_validate(doc) if doc else None

async def delete_entries_by_project_id(project_id: str) -> int:
    result = await get_db().entries.delete_many({"project_id": project_id})
    return result.deleted_count