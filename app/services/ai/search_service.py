import logging
import time

from fastapi import HTTPException, status
from langfuse import get_client, observe

from app.models.search import SearchRequest
from app.models.chunk import ChunkSearchResult
from app.models.user import UserResponse
from app.db.repositories import chunks_repository
from app.services.domain import project_service

logger = logging.getLogger(__name__)