from fastapi import Depends, HTTPException, status

from app.db.repositories import entry_repository, project_repository
from app.dependencies.auth import get_current_user
from app.models.entry import EntryDocument
from app.models.user import UserResponse


async def get_entry_and_verify_membership(
    entry_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> EntryDocument:
    """
    Recupera la entry per id e verifica che l'utente corrente
    sia membro del progetto a cui appartiene.
    Restituisce l'EntryDocument già validato.
    """
    entry = await entry_repository.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry non trovata.")

    role = await project_repository.get_user_role_in_project(
        str(entry.projectId), current_user.id
    )
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso negato.")

    return entry