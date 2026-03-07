from app.services import search_service, rag
from app.models.chat import ChatRequest
from app.models.search import SearchRequest

async def chat(request: ChatRequest):
    search_request = SearchRequest(
        query=request.question,
        project=request.project or None,
        top_k=request.top_k
    )
    results = await search_service.search_entries(search_request)
    response = await rag.return_chat_response(request.question, results)
    return response