import logging
import time

from fastapi import HTTPException, status
from langfuse import get_client, observe

from app.models.search import SearchRequest
from app.models.chunk import ChunkSearchResult
from app.models.user import UserResponse
from app.services.processing import embedder
from app.db.repositories import chunks_repository, project_repository

logger = logging.getLogger(__name__)

async def resolve_project_ids(project_id: str | None, user_id: str) -> list[str]:
    """
    Risolve i project_ids accessibili all'utente.
    Se project_id specificato: verifica membership e ritorna [project_id].
    Se assente: ritorna tutti i project_ids accessibili.
    """
    if project_id:
        role = await project_repository.get_user_role_in_project(project_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accesso negato al progetto specificato.",
            )
        return [project_id]
    return await project_repository.get_project_ids_for_user(user_id)

async def vector_search_chunks(request: SearchRequest, current_user: UserResponse) -> list[ChunkSearchResult]:
    project_ids = await resolve_project_ids(request.project_id, current_user.id)

    logger.info(f"[search] Generating embedding for query: {request.query!r}")
    t0 = time.perf_counter()
    embedded_query = await embedder.generate_embedding(request.query)
    logger.info(f"[search] Embedding done ({time.perf_counter()-t0:.2f}s) — running vector search (top_k={request.top_k}, project={project_ids!r})")

    t1 = time.perf_counter()
    results = await chunks_repository.vector_search_chunks(
        embedded_query,
        project_ids,
        request.top_k,
    )
    logger.info(f"[search] Vector search done ({time.perf_counter()-t1:.2f}s) — {len(results)} chunk(s) found")
    return results