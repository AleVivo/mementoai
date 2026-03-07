from fastapi import APIRouter
from app.services import chat_service
from app.models.chat import ChatRequest

router = APIRouter()

@router.post("")
async def chat_endpoint(request: ChatRequest):
    return await chat_service.chat(request)