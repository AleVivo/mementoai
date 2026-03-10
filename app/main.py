from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import entries, search, chat

app = FastAPI(title = "MementoAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o specifica "tauri://localhost"
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entries.router, prefix="/entries", tags=["entries"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])