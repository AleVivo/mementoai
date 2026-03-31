import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.client import close_client, get_async_client
from app.handlers import config_handlers
from app.observability import langfuse_integration
from app.routers import admin, entries, search, chat, agent, auth, project, users
from app.config import settings
from app.services.llm import provider_cache

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MementoAI starting up...")
    get_async_client()
    
    await config_handlers.run_all_handlers()

    if not provider_cache.is_initialized():
        logger.warning(
            "⚠ Uno o più provider non inizializzati. "
            "Configura LLM ed embedding dalla admin console."
        )

    yield

    logger.info("MementoAI shutting down...")
    await langfuse_integration.flush()  # ← flush trace pendenti prima di chiudere
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
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
