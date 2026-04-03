from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.types import PyObjectId


class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[str] = None


class FolderUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class FolderMove(BaseModel):
    new_parent_id: Optional[str] = None


class FolderDocument(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    project_id: ObjectId
    parent_id: Optional[ObjectId] = None
    path: str
    is_root: bool = False
    created_at: datetime
    created_by: ObjectId

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}


class FolderResponse(BaseModel):
    id: str
    name: str
    parent_id: Optional[str]
    path: str
    created_at: datetime


class FolderTree(FolderResponse):
    children: List["FolderTree"] = []
