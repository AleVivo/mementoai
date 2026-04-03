from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from app.models.types import PyObjectId

class EntryType(str, Enum):
    adr = "adr"
    postmortem = "postmortem"
    update = "update"

class VectorStatus(str, Enum):
    pending = "pending"
    indexed = "indexed"
    outdated = "outdated"
    error = "error"

class EntryCreate(BaseModel):
    content: str
    entry_type: EntryType
    title: str
    project_id: str
    folder_id: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None

class EntryUpdate(BaseModel):
    content: Optional[str] = None
    entry_type: Optional[EntryType] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None
    folder_id: Optional[str] = None

class EntryResponse(BaseModel):
    id: str
    content: str
    entry_type: EntryType
    title: str
    summary: str
    projectId: str
    authorId: str
    author: str
    tags: list[str]
    created_at: datetime
    week: str
    vector_status: VectorStatus
    folder_id: Optional[str] = None

class EntryDocument(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    content: str
    entry_type: EntryType
    title: str
    summary: str = ""
    projectId: ObjectId
    authorId: ObjectId
    author: str
    tags: list[str] = []
    created_at: datetime
    week: str
    vector_status: VectorStatus = VectorStatus.pending
    folderId: Optional[ObjectId] = None

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}