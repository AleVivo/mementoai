from typing import Optional
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    top_k: int = 5

class SearchResult(BaseModel):
    entry_id: str
    entry_type: str
    entry_title: str
    project_id: str
    heading: Optional[str] = None
    text: str
    score: float