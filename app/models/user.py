from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

UserRole = Literal["user", "admin"]

class UserDocument(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    email: str
    hashed_password: str
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    role: UserRole = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = ""
    last_name: str = ""
    company: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    company: str
    role: UserRole
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


def user_to_response(user: "UserDocument") -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        company=user.company,
        role=user.role,
        created_at=user.created_at,
    )
