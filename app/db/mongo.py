from typing import Optional
from app.models.search import SearchResult
from pymongo import AsyncMongoClient
from bson import ObjectId
from app.config import settings
from app.models.entry import EntryDocument
from datetime import datetime, timezone

##MongoDB client setup

client = AsyncMongoClient(
    settings.mongodb_url,
    username=settings.mongodb_user,
    password=settings.mongodb_password,
    directConnection=True)

db = client[settings.mongodb_db]
entries_collection = db["entries"]

##Methods to interact with the database

async def create_entry(entryDocument: EntryDocument) -> EntryDocument:
    document = entryDocument.model_dump(by_alias=True, exclude_none=True)
    result = await entries_collection.insert_one(document)
    saved = await entries_collection.find_one({"_id": result.inserted_id})
    return EntryDocument.model_validate(saved)

async def get_entries(
        project: Optional[str],
        entry_type: Optional[str],
        week: Optional[str],
        limit: int,
        skip: int) -> list[EntryDocument]:
    query = {}
    if project:
        query["project"] = project
    if entry_type:
        query["entry_type"] = entry_type
    if week:
        query["week"] = week

    cursor = db.entries.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [EntryDocument.model_validate(doc) for doc in docs]

async def get_entry_by_id(entry_id: str) -> Optional[EntryDocument]:
    try:
        oid = ObjectId(entry_id)
    except Exception:
        return None
    
    entry = await entries_collection.find_one({"_id": oid})
    return EntryDocument.model_validate(entry) if entry else None

async def delete_entry_by_id(entry_id: str) -> bool:
    try:
        oid = ObjectId(entry_id)
    except Exception:
        return False
    
    result = await entries_collection.delete_one({"_id": oid})
    return result.deleted_count == 1

async def update_entry(entry_id: str, fields: dict) -> Optional[EntryDocument]:
    try:
        oid = ObjectId(entry_id)
    except Exception:
        return None
    
    if not fields:
        return await get_entry_by_id(entry_id)
    
    doc = await entries_collection.find_one_and_update(
        {"_id": oid},
        {"$set": fields},
        return_document=True,
    )
    return EntryDocument.model_validate(doc) if doc else None