from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from starlette import status

from app.dependencies.auth import get_current_user
from app.models.project import ProjectResponse, ProjectCreate, ProjectUpdate, AddMemberRequest, MemberResponse
from app.models.user import UserResponse
from app.services.domain import project_service

router = APIRouter()

@router.get("", response_model=List[ProjectResponse])
async def get_projects(current_user: UserResponse = Depends(get_current_user)):
    return await project_service.get_projects(current_user)

@router.post("", response_model=ProjectResponse)
async def add_project(project: ProjectCreate, current_user: UserResponse = Depends(get_current_user)):
    return await project_service.create_project(project,current_user)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(project_id: str, current_user: UserResponse = Depends(get_current_user)):
    return await project_service.get_project_by_id(project_id,current_user)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project_by_id(project_id: str, project: ProjectUpdate, current_user: UserResponse = Depends(get_current_user)):
    return await project_service.update_project(project_id, project, current_user)

@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
async def delete_project_by_id(project_id: str, current_user: UserResponse = Depends(get_current_user)):
    return await project_service.delete_project(project_id, current_user)

@router.get("/{project_id}/members", response_model=List[MemberResponse])
async def get_project_members(project_id: str, current_user: UserResponse = Depends(get_current_user)):
    return await project_service.get_project_members(project_id, current_user)

@router.post("/{project_id}/members", status_code=status.HTTP_201_CREATED)
async def update_project_members(project_id: str, members_request: AddMemberRequest, current_user: UserResponse = Depends(get_current_user)):
    return await project_service.add_member(project_id, members_request, current_user)

@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_200_OK)
async def delete_project_members(project_id: str, user_id: str, current_user: UserResponse = Depends(get_current_user)):
    return await project_service.remove_member(project_id, user_id, current_user)