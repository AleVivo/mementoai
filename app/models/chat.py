from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    project_id: Optional[str] = None
    top_k: int = 5