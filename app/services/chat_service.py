import logging
import time
from app.services import search_service, rag
from app.models.chat import ChatRequest
from app.models.search import SearchRequest

logger = logging.getLogger(__name__)


async def chat(request: ChatRequest):
    t0 = time.perf_counter()
    logger.info(f"[chat] START — question: {request.question!r}, project: {request.project!r}")

    search_request = SearchRequest(
        query=request.question,
        project=request.project or None,
        top_k=request.top_k,
    )

    results = await search_service.search_entries(search_request)
    logger.info(f"[chat] Vector search done — {len(results)} chunk(s) retrieved ({time.perf_counter()-t0:.2f}s)")

    response = await rag.return_chat_response(request.question, results)
    logger.info(f"[chat] DONE — total time: {time.perf_counter()-t0:.2f}s")
    return response