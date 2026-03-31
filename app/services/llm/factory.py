"""
Factory per i provider LLM.
I provider sono gestiti da config_handlers.py e cachati in provider_cache.py.
Questo file esiste per backward compatibility — il codice esistente
che importa da factory.py continua a funzionare senza modifiche.
"""

from app.services.llm.provider_cache import (  # noqa: F401
    get_langchain_chat_provider,
    get_embedding_provider,
)