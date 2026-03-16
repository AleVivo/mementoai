from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.models.agent import AgentRequest
from app.models.user import UserResponse
from app.services.agent import run_agent_stream
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("")
async def ask_agent_stream(request: AgentRequest, current_user: UserResponse = Depends(get_current_user)):
    return StreamingResponse(
        run_agent_stream(
            question=request.question,
            project=request.project,
            max_steps=request.max_steps,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
