from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.models.types import PyObjectId

# ---------------------------------------------------------------------------
# Documento salvato su MongoDB da LlamaIndex
#
# LlamaIndex scrive documenti con questa struttura flat:
#   {
#     "id":        str   ← UUID generato da LlamaIndex (non ObjectId)
#     "embedding": list[float]
#     "text":      str
#     "metadata":  dict  ← tutti i nostri campi custom vanno qui
#   }
#
# Non esiste più un modello Pydantic per il documento grezzo perché
# LlamaIndex gestisce insert/read internamente tramite MongoDBAtlasVectorSearch.
# Questo file espone solo il modello di risposta verso i consumer (RAG, search,
# agent tools) e le costanti dei campi metadata.
# ---------------------------------------------------------------------------

class MetadataFields:
    """
    Costanti per i nomi dei campi dentro metadata{}.
    Usate da chunks_repository e retrieval/index.py per evitare stringhe
    sparse nel codice.
    """
    ENTRY_ID    = "entry_id"       # str (ObjectId serializzato come stringa)
    PROJECT_ID  = "project_id"     # str — campo indicizzato per pre-filter
    ENTRY_TYPE  = "entry_type"     # "adr" | "postmortem" | "update"
    ENTRY_TITLE = "entry_title"    # str
    HEADING     = "heading"        # str | None — heading TipTap del chunk
    CHUNK_INDEX = "chunk_index"    # int — posizione del chunk nell'entry
    CREATED_AT  = "created_at"     # str ISO 8601

class ChunkSearchResult(BaseModel):
    node_id:     str            # id LlamaIndex (UUID stringa)
    entry_id:    str            # ObjectId serializzato come stringa
    chunk_index: int
    heading:     Optional[str]
    text:        str
    score:       float
    entry_title: str
    project_id:  str
    entry_type:  str

    model_config = {"arbitrary_types_allowed": True}
        