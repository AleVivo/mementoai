from typing import List

from fastapi import APIRouter, Depends
from starlette import status

from app.dependencies.auth import get_current_user
from app.models.folder import FolderCreate, FolderMove, FolderResponse, FolderTree, FolderUpdate
from app.models.user import UserResponse
from app.services.domain import folder_service

router = APIRouter()


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    project_id: str,
    data: FolderCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    return await folder_service.create_folder(project_id, data, current_user)


@router.get("", response_model=List[FolderTree])
async def get_folder_tree(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    return await folder_service.get_folder_tree(project_id, current_user)


@router.put("/{folder_id}", response_model=FolderResponse)
async def rename_folder(
    project_id: str,
    folder_id: str,
    data: FolderUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    return await folder_service.rename_folder(project_id, folder_id, data, current_user)


@router.put("/{folder_id}/move", response_model=FolderResponse)
async def move_folder(
    project_id: str,
    folder_id: str,
    data: FolderMove,
    current_user: UserResponse = Depends(get_current_user),
):
    return await folder_service.move_folder(project_id, folder_id, data, current_user)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    project_id: str,
    folder_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    await folder_service.delete_folder(project_id, folder_id, current_user)
