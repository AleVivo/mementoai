from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.models.agent import AgentRequest
from app.models.user import UserResponse
from app.services.ai import agent
from app.dependencies.auth import get_current_user
from app.services.ai.search_service import resolve_project_ids

router = APIRouter()

@router.post("")
async def ask_agent_stream(request: AgentRequest, current_user: UserResponse = Depends(get_current_user)):
    project_ids = await resolve_project_ids(request.project_id, current_user.id)
    return StreamingResponse(
        agent.run_agent_stream(
            question=request.question,
            project_ids=project_ids,
            max_steps=request.max_steps,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
