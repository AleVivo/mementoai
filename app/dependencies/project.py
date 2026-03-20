from typing import Tuple

from fastapi import Depends, HTTPException, status

from app.db.repositories import project_repository
from app.dependencies.auth import get_current_user
from app.models.user import UserResponse


async def require_project_member(
        project_id: str,
        current_user: UserResponse = Depends(get_current_user)
    ) -> Tuple[str, str]:
    role = await project_repository.get_user_role_in_project(project_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso negato.")
    return project_id, role

async def require_project_owner(
        project_id: str,
        current_user: UserResponse = Depends(get_current_user)
    ) -> tuple[str, str]:
    role = await project_repository.get_user_role_in_project(project_id, current_user.id)
    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo il proprietario può eseguire questa operazione.",
        )
    return project_id, role