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
    raw_text: str
    type: str
    project: str
    author: str
    tags: list[str]
    score: float