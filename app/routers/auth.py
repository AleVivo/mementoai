from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.models.user import UserCreate, UserResponse, TokenResponse, UserDocument, RefreshRequest, LoginRequest, user_to_response
from app.db.repositories.users_repository import create_user, get_user_by_email, get_user_by_id
from app.services.domain import auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_in: UserCreate):
    existing = await get_user_by_email(user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    doc = UserDocument(
        email=user_in.email,
        hashed_password=auth_service.hash_password(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        company=user_in.company,
        created_at=datetime.now(timezone.utc),
    )
    saved = await create_user(doc)
    return user_to_response(saved)


@router.post("/login", response_model=TokenResponse)
async def login(user_in: LoginRequest):
    user = await get_user_by_email(user_in.email)
    # Always run verify_password to prevent timing-based email enumeration
    dummy = "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy"
    hashed = user.hashed_password if user else dummy
    password_ok = auth_service.verify_password(user_in.password, hashed)
    if not user or not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return auth_service.build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    payload = auth_service.decode_refresh_token(body.refresh_token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await get_user_by_id(sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return auth_service.build_token_response(user)
