import logging
import os
from typing import Optional

from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)

_active: bool = False
_llamaindex_instrumentor_active: bool = False
_langchain_handler: Optional[CallbackHandler] = None

# ---------------------------------------------------------------------------
# API pubblica
# ---------------------------------------------------------------------------

def setup(host: str, public_key: str, secret_key: str) -> None:
    """Attiva il tracing Langfuse via OpenTelemetry.
    """
    global _active, _llamaindex_instrumentor_active, _langchain_handler

    os.environ["LANGFUSE_BASE_URL"] = host
    os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
    os.environ["LANGFUSE_SECRET_KEY"] = secret_key
    os.environ["LANGFUSE_OTEL_HOST"] = host

    from langfuse import get_client
    get_client()

    from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
    if _llamaindex_instrumentor_active:
        LlamaIndexInstrumentor().uninstrument()
    LlamaIndexInstrumentor().instrument()
    _llamaindex_instrumentor_active = True

    logging.getLogger(
        "openinference.instrumentation.llama_index._handler"
    ).setLevel(logging.ERROR)

    # Aggiunge il CallbackHandler per LangChain/LangGraph
    _langchain_handler = CallbackHandler()

    _active = True
    logger.info(f"[observability] langfuse attivo — host: {host}")


def teardown() -> None:
    """Disattiva il tracing Langfuse e rimuove le credenziali dall'ambiente.
    """
    global _active, _llamaindex_instrumentor_active, _langchain_handler

    if not _active:
        logger.debug("[observability] teardown chiamato ma langfuse non era attivo, skip")
        return

    if _llamaindex_instrumentor_active:
        from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
        LlamaIndexInstrumentor().uninstrument()
        _llamaindex_instrumentor_active = False

    # Rimuove le variabili d'ambiente — evita che una config successiva
    # erediti credenziali vecchie se i campi vengono lasciati vuoti.
    for var in ("LANGFUSE_BASE_URL", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
        os.environ.pop(var, None)

    _langchain_handler = None
    _active = False
    logger.info("[observability] langfuse disattivato")


async def flush() -> None:
    """Svuota la coda di trace pendenti prima dello shutdown.
    """
    if not _active:
        return

    try:
        from langfuse import get_client
        get_client().flush()
        logger.info("[observability] flush completato")
    except Exception:
        # Il flush non deve mai bloccare lo shutdown dell'applicazione.
        logger.warning("[observability] flush fallito — alcuni trace potrebbero essere persi", exc_info=True)


def is_active() -> bool:
    """Restituisce True se il tracing è attualmente attivo.
    """
    return _active

def get_langchain_handler():
    """Restituisce un CallbackHandler"""
    if not _langchain_handler:
        return None
    return _langchain_handler