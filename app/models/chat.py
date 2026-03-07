from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    project: str
    top_k: int = 5