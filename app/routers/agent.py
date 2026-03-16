from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.agent import AgentRequest
from app.services.agent import run_agent_stream

router = APIRouter()

@router.post("")
async def ask_agent_stream(request: AgentRequest):
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