"""
Responsabilità: accesso al VectorStore e all'indice LlamaIndex.

Analogia con services/llm/provider_cache.py:
  provider_cache  tiene in memoria i provider LLM attivi (singleton)
  store           tiene in memoria il vector store e costruisce l'indice

Espone:
- get_vector_store()       → MongoDBAtlasVectorSearch (singleton, lru_cache)
- get_vector_store_index() → VectorStoreIndex pronto per query (leggero, no cache)

Non contiene logica di business — solo costruzione e accesso agli oggetti
LlamaIndex che wrappano MongoDB. Chi vuole fare retrieval importa da retriever.py,
chi vuole scrivere nodi importa get_vector_store() direttamente in pipeline.py.
"""

import logging
from functools import lru_cache
from urllib.parse import quote_plus

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch

from app.config import settings as app_settings
from app.db import client

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_vector_store() -> MongoDBAtlasVectorSearch:
    """
    Singleton MongoDBAtlasVectorSearch.

    lru_cache(maxsize=1) garantisce una sola istanza per tutta la vita dell'app.
    Non dipende dal provider embedding — non serve ricrearlo se l'admin
    aggiorna la configurazione LLM.

    Richiede sia mongodb_client (sync) che async_mongodb_client:
    - sync  → operazioni di setup interno LlamaIndex
    - async → add/query a runtime (async_add, aquery)
    Entrambi vengono da db/client.py.

    Configurazione campi MongoDB (devono corrispondere all'indice mongot):
    - embedding_key="embedding"  → path del vettore
    - text_key="text"            → campo testo del chunk
    - metadata_key="metadata"    → oggetto nested con i campi custom

    Indice mongot atteso sulla collection chunks:
      {
        "fields": [
          { "type": "vector", "path": "embedding",
            "numDimensions": 768, "similarity": "cosine" },
          { "type": "filter", "path": "metadata.project_id" }
        ]
      }
    """
    logger.info("[retrieval/store] inizializzazione MongoDBAtlasVectorSearch")
    return MongoDBAtlasVectorSearch(
        mongodb_client=client.get_sync_client(),
        async_mongodb_client=client.get_async_client(),
        db_name=app_settings.mongodb_db,
        collection_name="chunks",
        vector_index_name="chunks_vector_index",
        embedding_key="embedding",
        text_key="text",
        metadata_key="metadata",
    )


@lru_cache(maxsize=1)
def get_docstore() -> MongoDocumentStore:
    """
    Singleton MongoDocumentStore su MongoDB.

    Conserva i nodi padre (root ~2048t, intermedi ~512t) prodotti da
    HierarchicalNodeParser — non embeddati, usati da AutoMergingRetriever
    per espandere il contesto dei leaf node recuperati da $vectorSearch.

    Usa from_uri() che crea internamente sia un client sync (pymongo) che
    async (Motor) — necessario perché IngestionPipeline.arun() chiama
    metodi async del docstore (aget, aput).
    La collection creata da LlamaIndex è "node_docstore/data".
    Nessun Atlas Vector Search index necessario su questa collection.
    """
    logger.info("[retrieval/store] inizializzazione MongoDocumentStore")

    mongodb_uri = ""

    user = quote_plus(app_settings.mongodb_user)
    pw = quote_plus(app_settings.mongodb_password)
    dc = "?directConnection=true"
    url = app_settings.mongodb_url
    scheme, rest = url.split("://", 1)
    mongodb_uri = f"{scheme}://{user}:{pw}@{rest}{dc}"

    return MongoDocumentStore.from_uri(
        uri=mongodb_uri,
        db_name=app_settings.mongodb_db,
        namespace="node_docstore",
    )


def get_vector_store_index() -> VectorStoreIndex:
    """
    VectorStoreIndex collegato a MongoDBAtlasVectorSearch + MongoDocumentStore.

    from_vector_store() non re-indicizza nulla — costruisce l'interfaccia di query
    sull'indice MongoDB esistente. È leggero (nessuna chiamata a MongoDB o LLM)
    e può essere chiamato a ogni request senza overhead significativo.

    Non usa lru_cache perché VectorStoreIndex legge Settings.embed_model
    al momento della query — se l'embed_model cambia a runtime (admin console),
    il prossimo indice creato usa automaticamente il nuovo provider senza
    dover invalidare cache.

    Il docstore viene incluso nel StorageContext per abilitare
    AutoMergingRetriever (che legge i nodi padre da node_docstore).

    Chiamato da retriever.py ogni volta che serve un QueryEngine o un Retriever.
    """
    vector_store = get_vector_store()
    return VectorStoreIndex.from_vector_store(
        vector_store
    )