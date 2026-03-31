import logging
from bson import ObjectId
from fastapi import HTTPException, status

from app.models.entry import EntryDocument, EntryResponse, EntryCreate, EntryUpdate, VectorStatus
from app.db.repositories import entry_repository, chunks_repository, project_repository
from app.mappers import entry_mapper
from datetime import datetime, timezone

from app.models.user import UserResponse
from app.services.ingestion import pipeline as ingestion_pipeline

from langfuse import observe


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


@observe(name="entry_indexing")
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
    logger.info(f"[index] Loaded entry — title: {entry.title!r}, content: {len(entry.content)} chars")

    try:
        await ingestion_pipeline.run(
            content=entry.content,
            content_type="html",
            entry_id=entry_id,
            project_id=str(entry.projectId),
            entry_type=entry.entry_type,
            entry_title=entry.title,
            created_at=entry.created_at,
        )
        # vector_status=indexed settato DOPO il successo della pipeline
        updated = await entry_repository.update_entry(entry_id, {"vector_status": VectorStatus.indexed})
        logger.info(f"[index] DONE entry_id={entry_id}")
    except Exception as exc:
        logger.error(f"[index] FAILED entry_id={entry_id}: {exc}", exc_info=True)
        await entry_repository.update_entry(entry_id, {"vector_status": VectorStatus.error})
        raise HTTPException(status_code=500, detail="Indicizzazione fallita. Riprova.")

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
    await chunks_repository.delete_docstore_nodes_by_entry_id(entry_id)
    return await entry_repository.delete_entry_by_id(entry_id)