from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from app.db.client import get_db
from app.models.project import ProjectDocument


# ─── Projects ────────────────────────────────────────────────────────────────

async def create_project(doc: ProjectDocument) -> ProjectDocument:
    document = doc.model_dump(by_alias=True, exclude_none=True, exclude={"id"})
    result = await get_db().projects.insert_one(document)
    saved = await get_db().projects.find_one({"_id": result.inserted_id})
    return ProjectDocument.model_validate(saved)


async def get_project_by_id(project_id: str) -> Optional[ProjectDocument]:
    try:
        oid = ObjectId(project_id)
    except InvalidId:
        return None
    doc = await get_db().projects.find_one({"_id": oid})
    return ProjectDocument.model_validate(doc) if doc else None


async def get_projects_with_role_for_user(user_id: str) -> list[dict]:
    """Aggregates project_members → projects and returns dicts with `currentUserRole`."""
    try:
        u_oid = ObjectId(user_id)
    except InvalidId:
        return []

    pipeline = [
        {"$match": {"userId": u_oid}},
        {
            "$lookup": {
                "from": "projects",
                "localField": "projectId",
                "foreignField": "_id",
                "as": "project",
            }
        },
        {"$unwind": "$project"},
        {
            "$replaceRoot": {
                "newRoot": {
                    "$mergeObjects": ["$project", {"currentUserRole": "$role"}]
                }
            }
        },
    ]
    cursor = await get_db().project_members.aggregate(pipeline)
    return await cursor.to_list(length=None)


async def get_user_role_in_project(project_id: str, user_id: str) -> Optional[str]:
    try:
        p_oid = ObjectId(project_id)
        u_oid = ObjectId(user_id)
    except InvalidId:
        return None
    print(p_oid, u_oid)
    doc = await get_db().project_members.find_one({"projectId": p_oid, "userId": u_oid})
    return doc["role"] if doc else None


async def update_project(project_id: str, fields: dict) -> Optional[ProjectDocument]:
    try:
        oid = ObjectId(project_id)
    except InvalidId:
        return None
    doc = await get_db().projects.find_one_and_update(
        {"_id": oid},
        {"$set": fields},
        return_document=True,
    )
    return ProjectDocument.model_validate(doc) if doc else None


async def delete_project(project_id: str) -> bool:
    try:
        oid = ObjectId(project_id)
    except InvalidId:
        return False
    result = await get_db().projects.delete_one({"_id": oid})
    return result.deleted_count == 1


# ─── Project Members ─────────────────────────────────────────────────────────

async def add_project_member(project_id: str, user_id: str, role: str) -> None:
    p_oid = ObjectId(project_id)
    u_oid = ObjectId(user_id)
    await get_db().project_members.insert_one({
        "projectId": p_oid,
        "userId": u_oid,
        "role": role,
        "addedAt": datetime.now(timezone.utc),
    })


async def get_project_members(project_id: str) -> list[dict]:
    try:
        p_oid = ObjectId(project_id)
    except InvalidId:
        return []

    pipeline = [
        {"$match": {"projectId": p_oid}},
        {
            "$lookup": {
                "from": "users",
                "localField": "userId",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": "$user"},
        {
            "$project": {
                "_id": 0,
                "userId": {"$toString": "$user._id"},
                "email": "$user.email",
                "firstName": "$user.first_name",
                "lastName": "$user.last_name",
                "role": "$role",
                "addedAt": "$addedAt",
            }
        },
    ]
    cursor = await get_db().project_members.aggregate(pipeline)
    return await cursor.to_list(length=None)


async def get_project_member(project_id: str, user_id: str) -> Optional[dict]:
    try:
        p_oid = ObjectId(project_id)
        u_oid = ObjectId(user_id)
    except InvalidId:
        return None
    return await get_db().project_members.find_one({"projectId": p_oid, "userId": u_oid})


async def remove_project_member(project_id: str, user_id: str) -> bool:
    try:
        p_oid = ObjectId(project_id)
        u_oid = ObjectId(user_id)
    except InvalidId:
        return False
    result = await get_db().project_members.delete_one({"projectId": p_oid, "userId": u_oid})
    return result.deleted_count == 1


async def delete_all_project_members(project_id: str) -> int:
    try:
        p_oid = ObjectId(project_id)
    except InvalidId:
        return 0
    result = await get_db().project_members.delete_many({"projectId": p_oid})
    return result.deleted_count

async def get_project_ids_for_user(user_id: str) -> list[str]:
    """Restituisce gli id stringa di tutti i progetti a cui l'utente appartiene."""
    try:
        u_oid = ObjectId(user_id)
    except InvalidId:
        return []
    cursor = get_db().project_members.find({"userId": u_oid}, {"projectId": 1, "_id": 0})
    docs = await cursor.to_list(length=None)
    return [str(doc["projectId"]) for doc in docs]