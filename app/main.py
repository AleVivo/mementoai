import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import entries, search, chat, agent, auth
from app.services import ollama
from app.config import settings
from app.db.users_mongo import users_collection

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MementoAI starting up...")
    await users_collection.create_index("email", unique=True)
    try:
        await ollama.preload_models()
    except Exception as e:
        logger.warning(f"Could not preload Ollama models (is Ollama running?): {e}")
    yield
    logger.info("MementoAI shutting down...")
    try:
        await ollama.unload_models()
    except Exception:
        pass


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