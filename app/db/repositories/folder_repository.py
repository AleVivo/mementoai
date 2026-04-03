import re
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.db.client import get_db
from app.models.folder import FolderDocument


# ─── Read ─────────────────────────────────────────────────────────────────────

async def get_folder_by_id(folder_id: str) -> Optional[FolderDocument]:
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return None
    doc = await get_db().folders.find_one({"_id": oid})
    return FolderDocument.model_validate(doc) if doc else None


async def get_folder_by_id_and_project(folder_id: str, project_id: str) -> Optional[FolderDocument]:
    try:
        f_oid = ObjectId(folder_id)
        p_oid = ObjectId(project_id)
    except InvalidId:
        return None
    doc = await get_db().folders.find_one({"_id": f_oid, "project_id": p_oid})
    return FolderDocument.model_validate(doc) if doc else None


async def get_root_folder(project_id: str) -> Optional[FolderDocument]:
    try:
        p_oid = ObjectId(project_id)
    except InvalidId:
        return None
    doc = await get_db().folders.find_one({"project_id": p_oid, "is_root": True})
    return FolderDocument.model_validate(doc) if doc else None


async def get_folders_by_project(project_id: str) -> list[FolderDocument]:
    """Returns all non-root folders for a project (used for tree building)."""
    try:
        p_oid = ObjectId(project_id)
    except InvalidId:
        return []
    cursor = get_db().folders.find({"project_id": p_oid, "is_root": {"$ne": True}})
    docs = await cursor.to_list(length=None)
    return [FolderDocument.model_validate(doc) for doc in docs]


async def get_descendants(folder_path: str) -> list[FolderDocument]:
    """Returns all folders whose path starts with folder_path + '/'."""
    prefix = re.escape(folder_path) + "/"
    cursor = get_db().folders.find({"path": {"$regex": f"^{prefix}"}})
    docs = await cursor.to_list(length=None)
    return [FolderDocument.model_validate(doc) for doc in docs]


async def get_descendant_ids(folder_path: str) -> list[ObjectId]:
    """Returns ObjectIds of all descendant folders (excludes the folder itself)."""
    prefix = re.escape(folder_path) + "/"
    cursor = get_db().folders.find(
        {"path": {"$regex": f"^{prefix}"}},
        {"_id": 1},
    )
    docs = await cursor.to_list(length=None)
    return [doc["_id"] for doc in docs]


async def find_duplicate_name(project_id: str, parent_id: Optional[str], name: str) -> bool:
    """Returns True if a folder with the same name already exists at this parent level."""
    try:
        p_oid = ObjectId(project_id)
    except InvalidId:
        return False

    query: dict = {
        "project_id": p_oid,
        "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"},
        "is_root": {"$ne": True},
    }
    if parent_id is None:
        query["parent_id"] = None
    else:
        try:
            query["parent_id"] = ObjectId(parent_id)
        except InvalidId:
            return False

    doc = await get_db().folders.find_one(query)
    return doc is not None


# ─── Write ────────────────────────────────────────────────────────────────────

async def create_root_folder(project_id: ObjectId, user_id: ObjectId) -> FolderDocument:
    folder_id = ObjectId()
    doc = {
        "_id": folder_id,
        "name": "",
        "project_id": project_id,
        "parent_id": None,
        "path": f"/{project_id}",
        "is_root": True,
        "created_at": datetime.now(timezone.utc),
        "created_by": user_id,
    }
    await get_db().folders.insert_one(doc)
    saved = await get_db().folders.find_one({"_id": folder_id})
    return FolderDocument.model_validate(saved)


async def create_folder(
    name: str,
    project_id: ObjectId,
    parent_id: Optional[ObjectId],
    path: str,
    user_id: ObjectId,
    folder_id: Optional[ObjectId] = None,
) -> FolderDocument:
    folder_id = folder_id or ObjectId()
    doc = {
        "_id": folder_id,
        "name": name,
        "project_id": project_id,
        "parent_id": parent_id,
        "path": path,
        "is_root": False,
        "created_at": datetime.now(timezone.utc),
        "created_by": user_id,
    }
    await get_db().folders.insert_one(doc)
    saved = await get_db().folders.find_one({"_id": folder_id})
    return FolderDocument.model_validate(saved)


async def rename_folder(folder_id: str, name: str) -> Optional[FolderDocument]:
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return None
    doc = await get_db().folders.find_one_and_update(
        {"_id": oid},
        {"$set": {"name": name}},
        return_document=True,
    )
    return FolderDocument.model_validate(doc) if doc else None


async def move_folder_and_descendants(old_path: str, new_path: str, folder_id: str, new_parent_id: Optional[ObjectId]) -> None:
    """
    Atomically updates the path of the folder and all its descendants.
    Uses MongoDB $replaceAll (available from MongoDB 4.4+).
    Also updates parent_id on the moved folder itself.
    """
    try:
        f_oid = ObjectId(folder_id)
    except InvalidId:
        return

    escaped = re.escape(old_path)

    # Update the folder itself (path + parent_id)
    await get_db().folders.update_one(
        {"_id": f_oid},
        {"$set": {"path": new_path, "parent_id": new_parent_id}},
    )

    # Update all descendants (path prefix replacement)
    await get_db().folders.update_many(
        {"path": {"$regex": f"^{escaped}/"}},
        [{"$set": {"path": {
            "$replaceAll": {
                "input": "$path",
                "find": old_path,
                "replacement": new_path,
            }
        }}}],
    )


async def delete_folder(folder_id: str) -> bool:
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return False
    result = await get_db().folders.delete_one({"_id": oid})
    return result.deleted_count == 1


async def delete_folders_by_project_id(project_id: str) -> int:
    try:
        p_oid = ObjectId(project_id)
    except InvalidId:
        return 0
    result = await get_db().folders.delete_many({"project_id": p_oid})
    return result.deleted_count


# ─── Guards ───────────────────────────────────────────────────────────────────

async def has_children(folder_id: str) -> bool:
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return False
    count = await get_db().folders.count_documents({"parent_id": oid})
    return count > 0


async def has_entries(folder_id: str) -> bool:
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return False
    count = await get_db().entries.count_documents({"folderId": oid})
    return count > 0
