from fastapi import APIRouter, Query, HTTPException, status, Depends

from app.db.repositories.users_repository import get_user_by_email
from app.dependencies.auth import get_current_user
from app.models.user import UserResponse, user_to_response

router = APIRouter()


@router.get("/search", response_model=UserResponse)
async def search_user_by_email(
    email: str = Query(..., description="Email dell'utente da cercare"),
    _current_user: UserResponse = Depends(get_current_user),
):
    """Cerca un utente per email. Usato per aggiungere membri a un progetto."""
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato.")
    return user_to_response(user)
