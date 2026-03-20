from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from app.models.types import PyObjectId


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectDocument(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    description: Optional[str] = None
    ownerId: PyObjectId
    createdAt: datetime

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    ownerId: str
    createdAt: datetime
    currentUserRole: str

    model_config = {"arbitrary_types_allowed": True}

class MemberResponse(BaseModel):
    userId: str
    email: str
    firstName: str
    lastName: str
    role: str
    addedAt: datetime

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class ProjectMemberDocument(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    projectId: PyObjectId
    userId: PyObjectId
    role: str
    addedAt: datetime

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class AddMemberRequest(BaseModel):
    projectId: str
    userId: str
    role: str = "member"