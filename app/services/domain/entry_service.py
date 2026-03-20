import logging
from bson import ObjectId
from fastapi import HTTPException, status

from app.models.entry import EntryDocument, EntryResponse, EntryCreate, EntryUpdate, VectorStatus
from app.db.repositories import entry_repository, chunks_repository, project_repository
from app.mappers import entry_mapper
from datetime import datetime, timezone

from app.models.user import UserResponse
from app.services.processing import chunker, embedder

logger = logging.getLogger(__name__)

async def get_entries(project_id: str | None, entry_type: str | None, week: str | None, limit: int, skip: int) -> list[EntryResponse]:
    entries = await entry_repository.get_entries(project_ids=[project_id] if project_id else None, entry_type=entry_type, week=week, limit=limit, skip=skip)
    return entry_mapper.list_docs_to_responses(entries)


async def get_entry_by_id(entry_id: str) -> EntryResponse | None:
    entry = await entry_repository.get_entry_by_id(entry_id)
    return entry_mapper.doc_to_response(entry) if entry else None


async def create_entry(entry: EntryCreate, current_user: UserResponse) -> EntryResponse:
    role = await project_repository.get_user_role_in_project(entry.project_id, current_user.id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non sei membro di questo progetto.",
        )
    now = datetime.now(timezone.utc)
    week = now.strftime("%Y-W%W")
    author = f"{current_user.first_name} {current_user.last_name}".strip() or current_user.email

    entry_document = EntryDocument(
        content=entry.content,
        entry_type=entry.entry_type,
        title=entry.title,
        projectId=ObjectId(entry.project_id),
        authorId=ObjectId(current_user.id),
        author=author,
        tags=entry.tags or [],
        summary=entry.summary or "",
        created_at=now,
        week=week,
        vector_status=VectorStatus.pending,
    )

    saved = await entry_repository.create_entry(entry_document)
    return entry_mapper.doc_to_response(saved)


async def update_entry(entry_id: str, update: EntryUpdate, current_user: UserResponse) -> EntryResponse | None:
    # Verifica membership
    entry = await entry_repository.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found.",
        )
    role = await project_repository.get_user_role_in_project(str(entry.projectId), current_user.id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non sei membro di questo progetto.",
        )

    existing = await entry_repository.get_entry_by_id(entry_id)
    if not existing:
        return None

    fields = update.model_dump(exclude_unset=True)    
    if fields:
        fields["vector_status"] = VectorStatus.outdated

    updated = await entry_repository.update_entry(entry_id, fields)
    return entry_mapper.doc_to_response(updated) if updated else None


async def index_entry(entry_id: str, current_user: UserResponse) -> EntryResponse | None:
    # Verifica membership
    entry = await entry_repository.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found.",
        )
    role = await project_repository.get_user_role_in_project(str(entry.projectId), current_user.id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non sei membro di questo progetto.",
        )

    logger.info(f"[index] START entry_id={entry_id}")

    existing = await entry_repository.get_entry_by_id(entry_id)
    if not existing:
        logger.warning(f"[index] Entry {entry_id} not found")
        return None
    logger.info(f"[index] Loaded entry — title: {existing.title!r}, content: {len(existing.content)} chars")

    # Step 1 — Persist vector_status=indexed (enrichment via classifier rimosso dalla pipeline)
    logger.info("[index] Step 1/3 — Persisting vector_status=indexed to MongoDB")
    fields = {"vector_status": VectorStatus.indexed}
    updated = await entry_repository.update_entry(entry_id, fields)
    logger.info("[index] Metadata persisted.")

    # Step 2 — Chunk HTML
    logger.info("[index] Step 2/3 — Chunking HTML content")
    await chunks_repository.delete_chunks_by_entry_id(entry_id)
    raw_chunks = chunker.chunk_html(
        content=existing.content,
        entry_id=ObjectId(entry_id),
        project_id=str(existing.projectId),
        entry_type=existing.entry_type,
        entry_title=existing.title,
        created_at=existing.created_at,
    )
    logger.info(f"[index] Chunking done — {len(raw_chunks)} chunk(s) produced")

    # Step 3 — Embed each chunk
    logger.info(f"[index] Step 3/3 — Embedding {len(raw_chunks)} chunk(s)")
    for i, chunk in enumerate(raw_chunks):
        logger.info(f"[index] Embedding chunk {i+1}/{len(raw_chunks)} — {len(chunk.text)} chars")
        vector = await embedder.generate_embedding(chunk.text)
        chunk.embedding = vector
    logger.info("[index] All chunks embedded.")

    await chunks_repository.insert_chunks(raw_chunks)
    logger.info(f"[index] DONE entry_id={entry_id} — {len(raw_chunks)} chunk(s) stored.")

    return entry_mapper.doc_to_response(updated) if updated else None


async def delete_entry(entry_id: str, current_user: UserResponse) -> bool:
    # Verifica membership
    entry = await entry_repository.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found.",
        )
    role = await project_repository.get_user_role_in_project(str(entry.projectId), current_user.id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non sei membro di questo progetto.",
        )

    await chunks_repository.delete_chunks_by_entry_id(entry_id)
    return await entry_repository.delete_entry_by_id(entry_id)