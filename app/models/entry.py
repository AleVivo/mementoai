from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from bson import ObjectId

class EntryType(str, Enum):
    adr = "adr"
    postmortem = "postmortem"
    update = "update"

class VectorStatus(str, Enum):
    pending = "pending"
    indexed = "indexed"
    outdated = "outdated"

class EntryCreate(BaseModel):
    raw_text: str
    type: EntryType
    title: str
    project: str
    author: str
    summary: Optional[str] = None
    tags: Optional[list[str]] = None

class EntryUpdate(BaseModel):
    raw_text: Optional[str] = None
    type: Optional[EntryType] = None
    title: Optional[str] = None
    project: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None

class EntryResponse(BaseModel):
    id: str
    raw_text: str
    type: EntryType
    title: str
    summary: str
    project: str
    author: str
    tags: list[str]
    created_at: datetime
    week: str
    vector_status: VectorStatus

class EntryDocument(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    raw_text: str
    type: EntryType
    title: str
    summary: str = ""
    project: str
    author: str
    tags: list[str] = []
    embedding: list[float] = []
    created_at: datetime
    week: str
    vector_status: VectorStatus = VectorStatus.pending

    model_config = {"arbitrary_types_allowed": True}