from typing import Optional
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    project: Optional[str] = None
    top_k: int = 5

class SearchResult(BaseModel):
    id: str
    title: str
    summary: str
    content: str
    entry_type: str
    project: str
    author: str
    tags: list[str]
    score: float