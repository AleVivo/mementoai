from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.models.agent import AgentRequest
from app.models.user import UserResponse
from app.services.ai import agent_service
from app.services.domain import project_service
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("")
async def ask_agent_stream(req: Request, request: AgentRequest, current_user: UserResponse = Depends(get_current_user)):
    project_ids = await project_service.resolve_project_ids(request.project_id, current_user.id)
    graph = req.app.state.agent_graph
    return StreamingResponse(
        agent_service.run_agent_stream(
            question=request.question,
            project_ids=project_ids,
            graph=graph,
            conversation_id=request.conversation_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
