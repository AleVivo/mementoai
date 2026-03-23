import logging
import os
from typing import Optional

import litellm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stato modulo-level — privato, non importare dall'esterno
# ---------------------------------------------------------------------------
_active: bool = False


# ---------------------------------------------------------------------------
# API pubblica
# ---------------------------------------------------------------------------

def setup(host: str, public_key: str, secret_key: str) -> None:
    """Attiva il tracing Langfuse via OpenTelemetry.

    Idempotente: può essere chiamata più volte (es. aggiornamento config
    a runtime dall'admin console) senza effetti collaterali.
    Se era già attiva, aggiorna le credenziali e lascia il callback invariato.
    """
    global _active

    # Imposta le variabili d'ambiente richieste dall'integrazione OTEL.
    # Nota: il metodo OTEL usa LANGFUSE_OTEL_HOST, non LANGFUSE_HOST.
    os.environ["LANGFUSE_OTEL_HOST"] = host
    os.environ["LANGFUSE_HOST"] = host
    os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
    os.environ["LANGFUSE_SECRET_KEY"] = secret_key

    print(host, public_key, secret_key)

    # Aggiunge il callback solo se non è già presente — evita duplicati
    # che causerebbero trace doppi per ogni chiamata LiteLLM.
    if "langfuse_otel" not in litellm.callbacks:
        litellm.callbacks.append("langfuse_otel")

    _active = True
    logger.info(f"[observability] langfuse attivo — host: {host}")


def teardown() -> None:
    """Disattiva il tracing Langfuse e rimuove le credenziali dall'ambiente.

    Idempotente: non fa nulla se Langfuse non era attivo.
    Chiamata da config_handlers quando il provider viene impostato su 'none'.
    """
    global _active

    if not _active:
        logger.debug("[observability] teardown chiamato ma langfuse non era attivo, skip")
        return

    # Rimuove il callback da LiteLLM
    if "langfuse_otel" in litellm.callbacks:
        litellm.callbacks.remove("langfuse_otel")

    # Rimuove le variabili d'ambiente — evita che una config successiva
    # erediti credenziali vecchie se i campi vengono lasciati vuoti.
    for var in ("LANGFUSE_OTEL_HOST", "LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
        os.environ.pop(var, None)

    _active = False
    logger.info("[observability] langfuse disattivato")


async def flush() -> None:
    """Svuota la coda di trace pendenti prima dello shutdown.

    Langfuse invia i trace in background in modo asincrono. Senza questo
    flush, i trace generati poco prima della chiusura del processo vengono
    persi. Va chiamato nel lifespan FastAPI durante lo shutdown.

    Idempotente: non fa nulla se Langfuse non era attivo.
    """
    if not _active:
        return

    try:
        # get_client() restituisce il singleton Langfuse già inizializzato
        # dall'integrazione OTEL — non crea una nuova connessione.
        from langfuse import get_client
        langfuse = get_client()
        langfuse.flush()
        logger.info("[observability] flush completato")
    except Exception:
        # Il flush non deve mai bloccare lo shutdown dell'applicazione.
        logger.warning("[observability] flush fallito — alcuni trace potrebbero essere persi", exc_info=True)


def is_active() -> bool:
    """Restituisce True se il tracing è attualmente attivo.

    Utile per logging condizionale nei servizi AI: evita di costruire
    metadata di trace se Langfuse non è configurato.
    """
    return _active