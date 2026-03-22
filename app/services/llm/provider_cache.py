"""
Singleton in memoria per i provider LLM attivi.

Questo modulo è l'unico punto dove vivono i provider istanziati.
Viene scritto dagli handler in config_handlers.py — mai dal codice applicativo.
Viene letto dal codice AI (rag_service, search_service, agent) tramite
get_chat_provider() e get_embedding_provider().

Perché un modulo singleton invece di app.state:
- Gli handler di reload non hanno accesso alla request o all'istanza app
- Il modulo Python è un singleton naturale — caricato una volta dal runtime
- L'assegnazione di variabile in Python è atomica grazie al GIL —
  safe in contesto async con aggiornamenti rari come questo
"""
import logging
from typing import Optional

from app.services.llm.base import EmbeddingProvider, ToolChatProvider

logger = logging.getLogger(__name__)

_chat_provider: Optional[ToolChatProvider] = None
_embedding_provider: Optional[EmbeddingProvider] = None

def get_chat_provider() -> ToolChatProvider:
    if _chat_provider is None:
        raise RuntimeError(
            "Chat provider non inizializzato. "
            "Configura il provider LLM dalla admin console."
        )
    return _chat_provider

def get_embedding_provider() -> EmbeddingProvider:
    if _embedding_provider is None:
        raise RuntimeError(
            "Embedding provider non inizializzato. "
            "Configura il provider embedding dalla admin console."
        )
    return _embedding_provider

def set_chat_provider(provider: ToolChatProvider) -> None:
    global _chat_provider
    logger.info(f"[provider_cache] chat provider aggiornato: {type(provider).__name__}")
    _chat_provider = provider

def set_embedding_provider(provider: EmbeddingProvider) -> None:
    global _embedding_provider
    logger.info(f"[provider_cache] embedding provider aggiornato: {type(provider).__name__}")
    _embedding_provider = provider

def is_initialized() -> bool:
    return _chat_provider is not None and _embedding_provider is not None