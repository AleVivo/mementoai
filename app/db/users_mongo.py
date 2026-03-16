from typing import Optional
from bson import ObjectId
from pymongo import AsyncMongoClient
from app.config import settings
from app.models.user import UserDocument

client = AsyncMongoClient(
    settings.mongodb_url,
    username=settings.mongodb_user,
    password=settings.mongodb_password,
    directConnection=True,
)

db = client[settings.mongodb_db]
users_collection = db["users"]


async def create_user(user_doc: UserDocument) -> UserDocument:
    document = user_doc.model_dump(by_alias=True, exclude_none=True)
    result = await users_collection.insert_one(document)
    user_doc.id = result.inserted_id
    return user_doc


async def get_user_by_email(email: str) -> Optional[UserDocument]:
    doc = await users_collection.find_one({"email": email})
    return UserDocument.model_validate(doc) if doc else None


async def get_user_by_id(user_id: str) -> Optional[UserDocument]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    doc = await users_collection.find_one({"_id": oid})
    return UserDocument.model_validate(doc) if doc else None
