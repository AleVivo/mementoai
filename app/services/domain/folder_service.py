import logging
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, status

from app.db.repositories import folder_repository, project_repository
from app.models.folder import FolderCreate, FolderDocument, FolderMove, FolderResponse, FolderTree, FolderUpdate
from app.models.user import UserResponse

logger = logging.getLogger(__name__)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _doc_to_response(doc: FolderDocument) -> FolderResponse:
    assert doc.id is not None
    return FolderResponse(
        id=str(doc.id),
        name=doc.name,
        parent_id=str(doc.parent_id) if doc.parent_id else None,
        path=doc.path,
        created_at=doc.created_at,
    )


def _build_tree(folders: list[FolderDocument]) -> list[FolderTree]:
    """In-memory O(n) tree build — single DB fetch, no N+1 queries."""
    by_id: dict[str, FolderTree] = {}
    for f in folders:
        assert f.id is not None
        by_id[str(f.id)] = FolderTree(
            id=str(f.id),
            name=f.name,
            parent_id=str(f.parent_id) if f.parent_id else None,
            path=f.path,
            created_at=f.created_at,
            children=[],
        )

    roots: list[FolderTree] = []
    for node in by_id.values():
        if node.parent_id is None or node.parent_id not in by_id:
            roots.append(node)
        else:
            by_id[node.parent_id].children.append(node)
    return roots


async def _require_member(project_id: str, user_id: str) -> None:
    role = await project_repository.get_user_role_in_project(project_id, user_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso negato.")


async def _get_folder_in_project(folder_id: str, project_id: str) -> FolderDocument:
    folder = await folder_repository.get_folder_by_id_and_project(folder_id, project_id)
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartella non trovata.")
    return folder


# ─── CREATE ───────────────────────────────────────────────────────────────────

async def create_folder(project_id: str, data: FolderCreate, current_user: UserResponse) -> FolderResponse:
    await _require_member(project_id, current_user.id)

    parent_path: str
    parent_oid: Optional[ObjectId] = None

    if data.parent_id is not None:
        parent = await _get_folder_in_project(data.parent_id, project_id)
        if parent.is_root:
            # Treat root as "no parent" for response purposes, but use its path
            parent_path = parent.path
            parent_oid = None
        else:
            parent_path = parent.path
            parent_oid = parent.id

    else:
        # Create under project root — lazy-create root if missing (projects created before
        # folder feature was introduced won't have a root folder document yet).
        root = await folder_repository.get_root_folder(project_id)
        if root is None:
            root = await folder_repository.create_root_folder(
                project_id=ObjectId(project_id),
                user_id=ObjectId(current_user.id),
            )
        parent_path = root.path
        parent_oid = None

    # Duplicate name check
    effective_parent_id = str(parent_oid) if parent_oid else None
    duplicate = await folder_repository.find_duplicate_name(project_id, effective_parent_id, data.name)
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A folder named '{data.name}' already exists at this level",
        )

    p_oid = ObjectId(project_id)
    # Pre-generate the ID so we can compute the path before inserting
    new_id = ObjectId()
    final_path = f"{parent_path}/{new_id}"

    folder = await folder_repository.create_folder(
        name=data.name,
        project_id=p_oid,
        parent_id=parent_oid,
        path=final_path,
        user_id=ObjectId(current_user.id),
        folder_id=new_id,
    )
    return _doc_to_response(folder)


# ─── READ ─────────────────────────────────────────────────────────────────────

async def get_folder_tree(project_id: str, current_user: UserResponse) -> list[FolderTree]:
    await _require_member(project_id, current_user.id)
    folders = await folder_repository.get_folders_by_project(project_id)
    return _build_tree(folders)


# ─── RENAME ───────────────────────────────────────────────────────────────────

async def rename_folder(project_id: str, folder_id: str, data: FolderUpdate, current_user: UserResponse) -> FolderResponse:
    await _require_member(project_id, current_user.id)
    folder = await _get_folder_in_project(folder_id, project_id)

    # Duplicate name check at same parent level (excluding itself)
    effective_parent_id = str(folder.parent_id) if folder.parent_id else None
    existing = await folder_repository.find_duplicate_name(project_id, effective_parent_id, data.name)
    if existing and data.name.lower() != folder.name.lower():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A folder named '{data.name}' already exists at this level",
        )

    updated = await folder_repository.rename_folder(folder_id, data.name)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartella non trovata.")
    return _doc_to_response(updated)


# ─── MOVE ─────────────────────────────────────────────────────────────────────

async def move_folder(project_id: str, folder_id: str, data: FolderMove, current_user: UserResponse) -> FolderResponse:
    await _require_member(project_id, current_user.id)
    folder = await _get_folder_in_project(folder_id, project_id)

    # Resolve new parent
    new_parent_oid: Optional[ObjectId] = None
    new_parent_path: str

    if data.new_parent_id is not None:
        new_parent = await folder_repository.get_folder_by_id(data.new_parent_id)
        if new_parent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartella di destinazione non trovata.")

        # Cross-project check
        if str(new_parent.project_id) != project_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot move a folder to a parent in a different project",
            )

        # Circular move check: new_parent must not be a descendant of folder
        assert folder.id is not None
        if new_parent.path.startswith(folder.path + "/"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot move a folder into its own descendant",
            )

        new_parent_path = new_parent.path if new_parent.is_root else new_parent.path
        new_parent_oid = new_parent.id if not new_parent.is_root else None
    else:
        # Move to project root — lazy-create root if missing
        root = await folder_repository.get_root_folder(project_id)
        if root is None:
            root = await folder_repository.create_root_folder(
                project_id=ObjectId(project_id),
                user_id=ObjectId(current_user.id),
            )
        new_parent_path = root.path
        new_parent_oid = None

    # Duplicate name check at destination
    effective_new_parent_id = str(new_parent_oid) if new_parent_oid else None
    duplicate = await folder_repository.find_duplicate_name(project_id, effective_new_parent_id, folder.name)
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A folder named '{folder.name}' already exists at the destination",
        )

    assert folder.id is not None
    old_path = folder.path
    new_path = f"{new_parent_path}/{folder.id}"

    await folder_repository.move_folder_and_descendants(old_path, new_path, folder_id, new_parent_oid)

    updated = await folder_repository.get_folder_by_id(folder_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Errore interno durante lo spostamento.")
    return _doc_to_response(updated)


# ─── DELETE ───────────────────────────────────────────────────────────────────

async def delete_folder(project_id: str, folder_id: str, current_user: UserResponse) -> None:
    await _require_member(project_id, current_user.id)
    folder = await _get_folder_in_project(folder_id, project_id)

    if folder.is_root:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non puoi eliminare il root folder.")

    if await folder_repository.has_children(folder_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a folder that contains subfolders",
        )

    if await folder_repository.has_entries(folder_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a folder that contains entries",
        )

    deleted = await folder_repository.delete_folder(folder_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartella non trovata.")
