import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.db.repositories import project_repository, entry_repository, chunks_repository
from app.models.project import ProjectResponse, ProjectUpdate, ProjectCreate, AddMemberRequest, ProjectDocument, \
    MemberResponse
from app.models.user import UserResponse

logger = logging.getLogger(__name__)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_response(doc: ProjectDocument, role: str) -> ProjectResponse:
    assert doc.id is not None, "ProjectDocument must have an id"
    return ProjectResponse(
        id=str(doc.id),
        name=doc.name,
        description=doc.description,
        ownerId=str(doc.ownerId),
        createdAt=doc.createdAt,
        currentUserRole=role,
    )

# ─── CRUD ────────────────────────────────────────────────────────────────────

async def get_projects(current_user: UserResponse) -> list[ProjectResponse]:
    docs = await project_repository.get_projects_with_role_for_user(current_user.id)
    return [
        ProjectResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            ownerId=str(doc["ownerId"]),
            createdAt=doc["createdAt"],
            currentUserRole=doc["currentUserRole"],
        )
        for doc in docs
    ]

async def create_project(data: ProjectCreate, current_user: UserResponse) -> ProjectResponse:
    doc = ProjectDocument(
        name=data.name,
        description=data.description,
        ownerId=ObjectId(current_user.id),
        createdAt=datetime.now(timezone.utc),
    )
    try:
        created = await project_repository.create_project(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un progetto con il nome '{data.name}' esiste già.",
        )

    try:
        await project_repository.add_project_member(str(created.id), current_user.id, "owner")
    except Exception as exc:
        logger.error("Inserimento project_member fallito per %s: %s — rollback in corso.", created.id, exc)
        await project_repository.delete_project(str(created.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossibile inizializzare la membership. Creazione del progetto annullata.",
        )

    return _build_response(created, "owner")

async def get_project_by_id(project_id: str, current_user: UserResponse) -> ProjectResponse:
    project = await project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progetto non trovato.")

    role = await project_repository.get_user_role_in_project(project_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso negato.")

    return _build_response(project, role)

async def update_project(project_id: str, update: ProjectUpdate, current_user: UserResponse) -> ProjectResponse:
    role = await project_repository.get_user_role_in_project(project_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progetto non trovato.")
    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo il proprietario può modificare il progetto.",
        )

    fields = update.model_dump(exclude_none=True)
    if not fields:
        return await get_project_by_id(project_id, current_user)

    try:
        updated = await project_repository.update_project(project_id, fields)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un progetto con il nome '{update.name}' esiste già.",
        )

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progetto non trovato.")

    return _build_response(updated, role)

async def delete_project(project_id: str, current_user: UserResponse) -> None:
    project = await project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progetto non trovato.")

    role = await project_repository.get_user_role_in_project(project_id, current_user.id)
    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo il proprietario può eliminare il progetto.",
        )

    # Cascata: entries → chunks → project_members → project
    await entry_repository.delete_entries_by_project_id(project_id)
    await chunks_repository.delete_chunks_by_project_id(project_id)
    await project_repository.delete_all_project_members(project_id)
    await project_repository.delete_project(project_id)

# ─── Members ─────────────────────────────────────────────────────────────────

async def add_member(project_id: str, request: AddMemberRequest, current_user: UserResponse) -> None:
    role = await project_repository.get_user_role_in_project(project_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progetto non trovato.")
    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo il proprietario può aggiungere membri.",
        )

    existing = await project_repository.get_project_member(project_id, request.userId)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="L'utente è già membro di questo progetto.",
        )

    await project_repository.add_project_member(project_id, request.userId, request.role)

async def get_project_members(project_id: str, current_user: UserResponse) -> list[MemberResponse]:
    role = await project_repository.get_user_role_in_project(project_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso negato.")

    docs = await project_repository.get_project_members(project_id)
    return [MemberResponse(**doc) for doc in docs]

async def remove_member(project_id: str, user_id: str, current_user: UserResponse) -> None:
    # Guard: non puoi rimuovere te stesso
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Non puoi rimuovere te stesso. "
                "Per dismettere il progetto usa la funzione di eliminazione."
            ),
        )

    current_role = await project_repository.get_user_role_in_project(project_id, current_user.id)
    if not current_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progetto non trovato.")
    if current_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo il proprietario può rimuovere membri.",
        )

    target = await project_repository.get_project_member(project_id, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro non trovato.")
    if target["role"] == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Non è possibile rimuovere il proprietario del progetto.",
        )

    await project_repository.remove_project_member(project_id, user_id)