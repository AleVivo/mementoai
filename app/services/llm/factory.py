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
    """
    Restituisce il provider di embedding configurato.
 
    @lru_cache(maxsize=1) significa che la funzione viene eseguita UNA sola volta
    e il risultato viene memorizzato. Ogni chiamata successiva restituisce
    lo stesso oggetto senza ricreare nulla.
 
    Perché lru_cache e non una variabile globale?
    - Una variabile globale viene inizializzata all'import del modulo,
      prima che settings sia caricato correttamente.
    - lru_cache ritarda l'inizializzazione alla prima chiamata,
      quando settings è già disponibile.
    """
    provider = settings.embedding_provider.lower()
    logger.info(f"[factory] Initializing embedding provider: {provider}")
 
    if provider == "ollama":
        from app.services.llm.ollama_provider import OllamaEmbeddingProvider
        return OllamaEmbeddingProvider()
 
    if provider == "openai":
        from app.services.llm.openai_provider import OpenAIEmbeddingProvider
        _require_key("OPENAI_API_KEY", settings.openai_api_key)
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embed_model)
 
    raise ValueError(
        f"EMBEDDING_PROVIDER='{provider}' non riconosciuto. "
        f"Valori supportati: ollama, openai"
    )
 
 
# ---------------------------------------------------------------------------
# Chat / completion provider
# ---------------------------------------------------------------------------
 
@lru_cache(maxsize=1)
def get_chat_provider() -> ToolChatProvider:
    """
    Restituisce il provider di chat configurato.
 
    Restituisce sempre un ToolChatProvider (che estende ChatProvider),
    così può essere usato sia dove serve solo stream_chat (rag.py)
    sia dove serve stream_chat_with_tools (agent.py).
    """
    provider = settings.llm_provider.lower()
    logger.info(f"[factory] Initializing chat provider: {provider}")
 
    if provider == "ollama":
        from app.services.llm.ollama_provider import OllamaChatProvider
        return OllamaChatProvider()
 
    if provider == "openai":
        from app.services.llm.openai_provider import OpenAIChatProvider
        _require_key("OPENAI_API_KEY", settings.openai_api_key)
        return OpenAIChatProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_chat_model)
 
    if provider == "groq":
        from app.services.llm.openai_provider import GroqChatProvider
        _require_key("GROQ_API_KEY", settings.groq_api_key)
        return GroqChatProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_chat_model)
 
    raise ValueError(
        f"LLM_PROVIDER='{provider}' non riconosciuto. "
        f"Valori supportati: ollama, openai, groq"
    )
 
 
# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
 
def _require_key(name: str, value: str | None) -> None:
    """Lancia un errore chiaro se una API key richiesta è mancante."""
    if not value:
        raise ValueError(
            f"{name} non configurata nel .env. "
            f"Aggiungila prima di usare questo provider."
        )