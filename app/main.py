import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.client import close_client, get_client
from app.routers import entries, search, chat, agent, auth, project
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

def _needs_ollama() -> bool:
    return (
        settings.llm_provider.lower() == "ollama"
        or settings.embedding_provider.lower() == "ollama"
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MementoAI starting up...")
    get_client()

    if _needs_ollama():
        from app.services.llm import ollama_provider
        try:
            await ollama_provider.preload_models()
        except Exception as e:
            logger.warning(f"Could not preload Ollama models (is Ollama running?): {e}")
    else:
        logger.info(f"LLM provider: {settings.llm_provider}, embedding: {settings.embedding_provider} — skipping Ollama preload")

    yield

    logger.info("MementoAI shutting down...")
    if _needs_ollama():
        from app.services.llm import ollama_provider
        try:
            await ollama_provider.unload_models()
        except Exception:
            pass
    await close_client()


app = FastAPI(title="MementoAI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o specifica "tauri://localhost"
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(entries.router, prefix="/entries", tags=["entries"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])
app.include_router(project.router, prefix="/project", tags=["project"])