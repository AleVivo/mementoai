"""
Handler di reload per le sezioni di configurazione.

Ogni handler:
1. Legge i values decifrati da MongoDB tramite config_service
2. Istanzia il provider corretto
3. Aggiorna la cache in provider_cache

La dispatch table SECTION_HANDLERS mappa section_id → handler.
Non tutte le sezioni hanno un handler — sezioni type "settings" non
devono ricaricare nulla.

run_handler() è l'unico punto di ingresso pubblico —
il router chiama questo senza sapere cosa c'è dentro.
"""

import logging
import os
from typing import Any, Callable, Coroutine, Optional

from app.observability import langfuse_integration
from app.services.llm import litellm_provider
from app.services.llm import provider_cache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_model_string(provider: str, model: str) -> str:
    """
    Costruisce la stringa modello nel formato LiteLLM: "provider/model".
    Esempi: "ollama/qwen2.5:7b", "openai/gpt-4o-mini", "groq/llama-3.3-70b-versatile"
    """
    return f"{provider}/{model}"

async def _handle_llm(values: dict[str, Any]) -> None:
    provider = values.get("provider")
    model = values.get("model")

    if not provider or not model:
        logger.warning("[config_handlers] llm — provider o model mancante, skip")
        return

    model_string = _build_model_string(provider, model)

    api_base: Optional[str] = values.get("host") if provider == "ollama_chat" else None
    api_key: Optional[str] = values.get("api_key") if provider != "ollama_chat" else None

    provider_cache.set_chat_provider(litellm_provider.LiteLLMChatProvider(
        model=model_string, 
        api_base=api_base, 
        api_key=api_key
    ))
    logger.info(f"[config_handlers] llm — provider aggiornato: {model_string}")


async def _handle_embedding(values: dict[str, Any]) -> None:
    provider = values.get("provider")
    model = values.get("model")

    if not provider or not model:
        logger.warning("[config_handlers] embedding — provider o model mancante, skip")
        return

    model_string = _build_model_string(provider, model)

    api_base: Optional[str] = values.get("host") if provider == "ollama" else None
    api_key: Optional[str] = values.get("api_key") if provider != "ollama" else None
    
    provider_cache.set_embedding_provider(litellm_provider.LiteLLMEmbeddingProvider(
        model=model_string,
        api_base=api_base,
        api_key=api_key
    ))
    logger.info(f"[config_handlers] embedding — provider aggiornato: {model_string}")


async def _handle_observability(values: dict[str, Any]) -> None:
    obs_provider = values.get("provider", "none")

    if obs_provider == "none":
        logger.info("[config_handlers] observability — disabilitata")
        langfuse_integration.teardown()
        return

    if obs_provider == "langfuse":
        host = values.get("host")
        public_key = values.get("public_key")
        secret_key = values.get("secret_key")

        if not all([host, public_key, secret_key]):
            logger.warning("[config_handlers] observability — langfuse config incompleta, skip")
            return

        assert isinstance(host, str)
        assert isinstance(public_key, str)  
        assert isinstance(secret_key, str)
        langfuse_integration.setup(
            host=host,
            public_key=public_key,
            secret_key=secret_key
        )
        return

    logger.warning(f"[config_handlers] observability — provider sconosciuto: '{obs_provider}', skip")


# ---------------------------------------------------------------------------
# Dispatch table e punto di ingresso pubblico
# ---------------------------------------------------------------------------

# Tipo dell'handler: funzione async che riceve i values decifrati
HandlerType = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]

SECTION_HANDLERS: dict[str, HandlerType] = {
    "llm":           _handle_llm,
    "embedding":     _handle_embedding,
    "observability": _handle_observability,
}


async def run_handler(section_id: str) -> None:
    """
    Punto di ingresso pubblico — chiamato dal router dopo ogni PUT.
    Chiamato anche dal lifespan all'avvio per tutte le sezioni.

    Se la sezione non ha un handler registrato non fa nulla —
    sezioni type "settings" non hanno provider da ricaricare.

    Se config_values non esiste per la sezione logga un warning
    e non fa nulla — il sistema parte senza provider per quella sezione.
    """
    handler = SECTION_HANDLERS.get(section_id)
    if handler is None:
        logger.debug(f"[config_handlers] nessun handler per sezione '{section_id}' — skip")
        return

    # Import qui per evitare circular import —
    # config_handlers → config_service → config_repository
    # config_service non importa config_handlers
    from app.services.domain.config_service import get_decrypted_values

    values = await get_decrypted_values(section_id)
    if values is None:
        logger.warning(
            f"[config_handlers] nessun config_values per '{section_id}' — "
            f"provider non inizializzato"
        )
        return

    await handler(values)


async def run_all_handlers() -> None:
    """
    Esegue tutti gli handler registrati in sequenza.
    Chiamato dal lifespan all'avvio.

    Un errore su un handler non blocca gli altri —
    ogni handler è isolato nel suo try/except.
    """
    for section_id in SECTION_HANDLERS:
        try:
            await run_handler(section_id)
        except Exception as e:
            logger.error(
                f"[config_handlers] errore durante reload '{section_id}': {e}",
                exc_info=True
            )