from fastapi import FastAPI
from app.routers import entries, search, chat

app = FastAPI(title = "MementoAI")

app.include_router(entries.router, prefix="/entries", tags=["entries"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])