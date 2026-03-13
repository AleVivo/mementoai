from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.models.types import PyObjectId

class ChunkDocument(BaseModel):
    """
    Documento salvato su MongoDB nella collection 'chunks'.
    Ogni entry genera N chunk, ciascuno con il proprio embedding.
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    entry_id: ObjectId
    chunk_index: int # indice del chunk all'interno dell'entry

    heading: Optional[str] = None
    text: str
    token_count: int = 0
    
    embedding: list[float] = []

    project: str
    entry_type: str
    entry_title: str
    created_at: datetime

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

class ChunkSearchResult(BaseModel):
    """
    Risultato di una ricerca vettoriale sui chunk.
    """
    chunk_id: PyObjectId
    entry_id: PyObjectId
    chunk_index: int
    heading: Optional[str]
    text: str
    score: float
    entry_title: str
    project: str
    entry_type: str

    model_config = {"arbitrary_types_allowed": True}
        