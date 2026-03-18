from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
from app.models.user import UserDocument
from app.db.client import get_db

async def create_user(user_doc: UserDocument) -> UserDocument:
    document = user_doc.model_dump(by_alias=True, exclude_none=True)
    result = await get_db().users.insert_one(document)
    user_doc.id = result.inserted_id
    return user_doc


async def get_user_by_email(email: str) -> Optional[UserDocument]:
    doc = await get_db().users.find_one({"email": email})
    return UserDocument.model_validate(doc) if doc else None


async def get_user_by_id(user_id: str) -> Optional[UserDocument]:
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        return None
    doc = await get_db().users.find_one({"_id": oid})
    return UserDocument.model_validate(doc) if doc else None
