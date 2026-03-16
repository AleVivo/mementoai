from fastapi import APIRouter
from app.services import chat_service
from app.models.chat import ChatRequest
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        chat_service.stream_chat(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )