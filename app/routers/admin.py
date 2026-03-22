from typing import List

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.dependencies.auth import require_admin
from app.handlers import config_handlers
from app.models.config import ConfigSectionResponse, ConfigUpdateRequest
from app.models.user import UserResponse
from app.services.domain import config_service

router = APIRouter()


@router.get("/config", response_model=List[ConfigSectionResponse])
async def get_all_config(
    current_user: UserResponse = Depends(require_admin),
):
    return await config_service.get_all_config()


@router.get("/config/{section_id}", response_model=ConfigSectionResponse)
async def get_config_section(
    section_id: str,
    current_user: UserResponse = Depends(require_admin),
):
    section = await config_service.get_config_section(section_id)
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sezione '{section_id}' non trovata.",
        )
    return section


@router.put("/config/{section_id}", response_model=ConfigSectionResponse)
async def update_config_section(
    section_id: str,
    body: ConfigUpdateRequest,
    current_user: UserResponse = Depends(require_admin),
):
    section = await config_service.get_config_section(section_id)
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sezione '{section_id}' non trovata.",
        )

    result, errors = await config_service.update_config_section(
        section_id=section_id,
        incoming=body.values,
        updated_by=current_user.id,
    )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors,
        )
    
    await config_handlers.run_handler(section_id)

    return result