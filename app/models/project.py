from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.types import PyObjectId


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectDocument(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    description: Optional[str] = None
    ownerId: ObjectId
    createdAt: datetime

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class ProjectResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    ownerId: PyObjectId = Field(default_factory=PyObjectId)
    createdAt: datetime
    currentUserRole: str

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class MemberResponse(BaseModel):
    userId: PyObjectId = Field(default_factory=PyObjectId)
    email: str
    firstName: str
    lastName: str
    role: str
    addedAt: datetime

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class ProjectMemberDocument(BaseModel):
    id: PyObjectId = Field(alias="_id")
    projectId: ObjectId
    userId: ObjectId
    role: str
    addedAt: datetime

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class AddMemberRequest(BaseModel):
    projectId: str
    userId: str
    role: str = "member"