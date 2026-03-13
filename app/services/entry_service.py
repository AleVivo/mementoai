import logging
from bson import ObjectId

from app.models.entry import EntryDocument, EntryResponse, EntryCreate, EntryUpdate, VectorStatus
from app.db import mongo, chunks_mongo
from app.mappers import entry_mapper
from app.services import embedding, chunker
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def get_entries(project: str | None, entry_type: str | None, week: str | None, limit: int, skip: int) -> list[EntryResponse]:
    entries = await mongo.get_entries(project=project, entry_type=entry_type, week=week, limit=limit, skip=skip)
    return entry_mapper.list_docs_to_responses(entries)

async def get_entry_by_id(entry_id: str) -> EntryResponse | None:
    entry = await mongo.get_entry_by_id(entry_id)
    return entry_mapper.doc_to_response(entry) if entry else None

async def create_entry(entry: EntryCreate) -> EntryResponse:
    now = datetime.now(timezone.utc)
    week = now.strftime("%Y-W%W")

    entryDocument = EntryDocument(
        content=entry.content,
        entry_type=entry.entry_type,
        title=entry.title,
        project=entry.project,
        author=entry.author,
        tags=entry.tags or [],
        summary=entry.summary or "",
        created_at=now,
        week=week,
        vector_status=VectorStatus.pending,
    )

    saved = await mongo.create_entry(entryDocument)
    return entry_mapper.doc_to_response(saved)

async def update_entry(entry_id: str, update: EntryUpdate) -> EntryResponse | None:
    existing = await mongo.get_entry_by_id(entry_id)
    if not existing:
        return None

    fields = update.model_dump(exclude_unset=True)    
    if fields:
        fields["vector_status"] = VectorStatus.outdated

    updated = await mongo.update_entry(entry_id, fields)
    return entry_mapper.doc_to_response(updated) if updated else None

async def index_entry(entry_id: str) -> EntryResponse | None:
    logger.info(f"[index] START entry_id={entry_id}")

    existing = await mongo.get_entry_by_id(entry_id)
    if not existing:
        logger.warning(f"[index] Entry {entry_id} not found")
        return None
    logger.info(f"[index] Loaded entry — title: {existing.title!r}, content: {len(existing.content)} chars")

    # Step 1 — Persist vector_status=indexed (enrichment via classifier rimosso dalla pipeline)
    logger.info("[index] Step 1/3 — Persisting vector_status=indexed to MongoDB")
    fields = {"vector_status": VectorStatus.indexed}
    updated = await mongo.update_entry(entry_id, fields)
    logger.info("[index] Metadata persisted.")

    # Step 2 — Chunk HTML
    logger.info("[index] Step 2/3 — Chunking HTML content")
    await chunks_mongo.delete_chunks_by_entry_id(entry_id)
    raw_chunks = chunker.chunk_html(
        content=existing.content,
        entry_id=ObjectId(entry_id),
        project=existing.project,
        entry_type=existing.entry_type,
        entry_title=existing.title,
        created_at=existing.created_at,
    )
    logger.info(f"[index] Chunking done — {len(raw_chunks)} chunk(s) produced")

    # Step 3 — Embed each chunk
    logger.info(f"[index] Step 3/3 — Embedding {len(raw_chunks)} chunk(s)")
    for i, chunk in enumerate(raw_chunks):
        logger.info(f"[index] Embedding chunk {i+1}/{len(raw_chunks)} — {len(chunk.text)} chars")
        vector = await embedding.generate_embedding(chunk.text)
        chunk.embedding = vector
    logger.info("[index] All chunks embedded.")

    await chunks_mongo.insert_chunks(raw_chunks)
    logger.info(f"[index] DONE entry_id={entry_id} — {len(raw_chunks)} chunk(s) stored.")

    return entry_mapper.doc_to_response(updated) if updated else None

async def delete_entry(entry_id: str) -> bool:
    await chunks_mongo.delete_chunks_by_entry_id(entry_id)
    return await mongo.delete_entry_by_id(entry_id)