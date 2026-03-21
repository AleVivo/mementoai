"""
Factory per i provider LLM.
 
Questo file è l'unico punto dove viene letta la configurazione del provider.
Il resto del codice chiama get_embedding_provider() o get_chat_provider()
e riceve un oggetto che rispetta il contratto ABC — senza sapere quale provider è.
 
Pattern usato: Factory Function (non Factory Class — più semplice in Python).
 
Come si usa:
    from app.services.llm.factory import get_embedding_provider, get_chat_provider
 
    provider = get_embedding_provider()
    vector = await provider.embed("testo da vettorizzare")
 
Configurazione in .env:
    LLM_PROVIDER=ollama          # oppure: openai, groq
    EMBEDDING_PROVIDER=ollama    # può essere diverso da LLM_PROVIDER
    OPENAI_API_KEY=sk-...
    GROQ_API_KEY=gsk_...
    OLLAMA_URL=http://localhost:11434
"""

import logging
from functools import lru_cache
 
from app.config import settings
from app.services.llm.base import EmbeddingProvider, ToolChatProvider
 
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    from app.services.llm.litellm_provider import LiteLLMEmbeddingProvider
    return LiteLLMEmbeddingProvider()
 
 
# ---------------------------------------------------------------------------
# Chat / completion provider
# ---------------------------------------------------------------------------
 
@lru_cache(maxsize=1)
def get_chat_provider() -> ToolChatProvider:
    from app.services.llm.litellm_provider import LiteLLMChatProvider
    return LiteLLMChatProvider()