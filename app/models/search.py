from typing import Optional
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    project: Optional[str] = None
    top_k: int = 5

class SearchResult(BaseModel):
    entry_id: str
    entry_type: str
    entry_title: str
    project: str
    heading: Optional[str] = None
    text: str
    score: float