from fastapi import APIRouter, Depends
from app.services import chat_service
from app.models.chat import ChatRequest
from app.models.user import UserResponse
from fastapi.responses import StreamingResponse
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("")
async def chat_endpoint(request: ChatRequest, current_user: UserResponse = Depends(get_current_user)):
    return StreamingResponse(
        chat_service.stream_chat(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
