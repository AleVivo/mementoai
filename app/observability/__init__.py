from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.callbacks import BaseCallbackHandler

def get_llm_callback_handler() -> "BaseCallbackHandler | None":
    """
    Restituisce il CallbackHandler di LangFuse se attivo, altrimenti None.
    Utile per strumenti che accettano un handler direttamente invece di un config.
    """
    from app.observability import langfuse_integration
    if not langfuse_integration.is_active():
        return None

    return langfuse_integration.get_langchain_handler()