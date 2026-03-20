from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.models.types import PyObjectId

class ChunkDocument(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    entry_id: ObjectId
    chunk_index: int # indice del chunk all'interno dell'entry
    heading: Optional[str] = None
    text: str
    token_count: int = 0
    embedding: list[float] = []
    project_id: str
    entry_type: str
    entry_title: str
    created_at: datetime

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

class ChunkSearchResult(BaseModel):
    chunk_id: PyObjectId
    entry_id: PyObjectId
    chunk_index: int
    heading: Optional[str]
    text: str
    score: float
    entry_title: str
    project_id: str
    entry_type: str

    model_config = {"arbitrary_types_allowed": True}
        