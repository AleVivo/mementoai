from pymongo import AsyncMongoClient, MongoClient
from pymongo.asynchronous.database import AsyncDatabase
from app.config import settings

_client: AsyncMongoClient | None = None
_sync_client: MongoClient | None = None

def get_async_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        _client = AsyncMongoClient(
            settings.mongodb_url,
            username=settings.mongodb_user,
            password=settings.mongodb_password,
            directConnection=True,
        )
    return _client

def get_sync_client() -> MongoClient:
    global _sync_client
    if _sync_client is None:
        _sync_client = MongoClient(
            settings.mongodb_url,
            username=settings.mongodb_user,
            password=settings.mongodb_password,
            directConnection=True,
        )
    return _sync_client

def get_db() -> AsyncDatabase:
    return get_async_client()[settings.mongodb_db]


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None