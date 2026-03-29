"""
Responsabilità: adattamento delle interfacce interne all'app verso LlamaIndex.

Contiene:
- ProviderEmbeddingAdapter — traduce EmbeddingProvider → BaseEmbedding LlamaIndex
- configure_llamaindex_settings() — configura Settings LlamaIndex con i provider attivi

Analogia con services/llm/:
  base.py          definisce i contratti interni (EmbeddingProvider, ChatProvider)
  adapters.py      traduce quei contratti verso LlamaIndex (BaseEmbedding)
  store.py         usa l'adapter per costruire il vector store

configure_llamaindex_settings() viene chiamata da handlers/config_handlers.py
al momento dell'avvio e ogni volta che l'admin aggiorna il provider embedding —
stesso pattern degli altri handler che chiamano provider_cache.set_*_provider().
"""

import asyncio
import concurrent.futures
import logging
from typing import Any, List

from llama_index.core import Settings
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.embeddings import BaseEmbedding

from app.services.llm.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class ProviderEmbeddingAdapter(BaseEmbedding):
    """
    Adatta EmbeddingProvider all'interfaccia BaseEmbedding di LlamaIndex.

    BaseEmbedding richiede sia metodi sync (_get_*) che async (_aget_*).
    Il nostro EmbeddingProvider è solo async.

    Strategia:
    - _aget_* → delegano direttamente al provider (percorso normale in FastAPI)
    - _get_*  → usano asyncio.run() come fallback per contesti sync interni
                 a LlamaIndex (es. operazioni di setup). NON chiamare da
                 dentro una coroutine attiva — causerebbe RuntimeError.

    PrivateAttr: LlamaIndex usa Pydantic internamente. Gli attributi non-campo
    vanno dichiarati PrivateAttr() altrimenti Pydantic li rifiuta.
    """

    _provider: EmbeddingProvider = PrivateAttr()

    def __init__(self, provider: EmbeddingProvider, **kwargs: Any) -> None:
        super().__init__(model_name="provider-embedding-adapter", **kwargs)
        self._provider = provider

    @classmethod
    def class_name(cls) -> str:
        return "ProviderEmbeddingAdapter"

    # ------------------------------------------------------------------
    # Async — percorso principale (FastAPI, event loop attivo)
    # ------------------------------------------------------------------

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return await self._provider.embed(text)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return await self._provider.embed(query)

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return await asyncio.gather(*[self._provider.embed(t) for t in texts])

    # ------------------------------------------------------------------
    # Sync — fallback richiesto dall'interfaccia, non usato in FastAPI.
    # Usa un thread separato per evitare RuntimeError "event loop already
    # running" quando chiamato dall'interno di uvicorn/FastAPI.
    # ------------------------------------------------------------------

    def _get_text_embedding(self, text: str) -> List[float]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, self._provider.embed(text)).result()

    def _get_query_embedding(self, query: str) -> List[float]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, self._provider.embed(query)).result()

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._get_text_embedding(t) for t in texts]


def configure_llamaindex_settings() -> None:
    """
    Configura LlamaIndex Settings con i provider attivi da provider_cache.

    Chiamata da handlers/config_handlers.py:
    1. All'avvio, dopo run_all_handlers()
    2. Ogni volta che l'admin aggiorna il provider embedding dalla admin console

    Settings.llm = None — il nostro ChatProvider non implementa l'interfaccia
    LlamaIndex LLM. La sintesi RAG rimane in rag_service.py che chiama
    stream_chat direttamente, mantenendo il controllo su prompt e streaming SSE.

    Import locale per evitare circular import al caricamento del modulo.
    """
    from app.services.llm.provider_cache import get_embedding_provider

    embedding_provider = get_embedding_provider()
    Settings.embed_model = ProviderEmbeddingAdapter(provider=embedding_provider)
    Settings.llm = None

    logger.info(
        "[retrieval/adapters] LlamaIndex Settings configurati — "
        f"embed_model: ProviderEmbeddingAdapter({type(embedding_provider).__name__})"
    )