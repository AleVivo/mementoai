from app.models.entry import EntryDocument, EntryResponse, EntryCreate, EntryUpdate
from app.db import mongo
from app.mappers import entry_mapper
from app.services import classifier, embedding
from datetime import datetime, timezone

async def get_entries(project: str | None, type: str | None, week: str | None, limit: int, skip: int) -> list[EntryResponse]:
    entries = await mongo.get_entries(project=project, type=type, week=week, limit=limit, skip=skip)
    return entry_mapper.list_docs_to_responses(entries)

async def get_entry_by_id(entry_id: str) -> EntryResponse | None:
    entry = await mongo.get_entry_by_id(entry_id)
    return entry_mapper.doc_to_response(entry) if entry else None

async def create_entry(entry: EntryCreate) -> EntryResponse:
    enriched = await classifier.enrich_entry(entry.raw_text, entry.tags, entry.summary)
    vector = await embedding.generate_embedding(entry.raw_text)
    now = datetime.now(timezone.utc)
    week = now.strftime("%Y-W%W")

    entryDocument = EntryDocument(
        raw_text=entry.raw_text,
        type=entry.type,
        title=entry.title,
        project=entry.project,
        author=entry.author,
        tags=enriched["tags"],
        summary=enriched["summary"],
        embedding=vector,
        created_at=now,
        week=week
    )

    saved = await mongo.create_entry(entryDocument)
    return entry_mapper.doc_to_response(saved)

async def update_entry(entry_id: str, update: EntryUpdate) -> EntryResponse | None:
    existing = await mongo.get_entry_by_id(entry_id)
    if not existing:
        return None
    
    fields = update.model_dump(exclude_unset=True)

    if "raw_text" in fields:
        fields["embedding"] = await embedding.generate_embedding(fields["raw_text"])
        
    updated = await mongo.update_entry(entry_id, fields)
    return entry_mapper.doc_to_response(updated) if updated else None

async def delete_entry(entry_id: str) -> bool:
    return await mongo.delete_entry_by_id(entry_id)