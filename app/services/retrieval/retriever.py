"""
Responsabilità: interfaccia pubblica del retriever verso i consumer.

Espone:
- get_retriever()    → AutoMergingRetriever — retrieval gerarchico con merge automatico
                        dei chunk fratelli nel nodo padre.
                        Usato da: search_service.py, agent/tools.py, rag_service.py
"""

import logging
from typing import Optional

from llama_index.core import StorageContext
from llama_index.core.indices.vector_store import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.vector_stores.types import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)

from app.services.retrieval.llama_store import get_vector_store_index, get_docstore, get_vector_store

logger = logging.getLogger(__name__)


def get_retriever(
    project_ids: Optional[list[str]] = None,
    top_k: int = 10,
) -> AutoMergingRetriever:
    """
    Ritorna un AutoMergingRetriever configurato.

    Il retriever esegue:
    1. Embedding della query (via Settings.embed_model → ProviderEmbeddingAdapter)
    2. $vectorSearch su MongoDB (collection chunks, leaf nodes ~128 token)
       con pre-filter per project_id se fornito
    3. AutoMerging: se ≥ soglia di leaf fratelli vengono recuperati,
       li sostituisce con il nodo padre (512t o 2048t) da node_docstore
    4. Ritorna i NodeWithScore — da passare poi a get_reranker() per il re-ranking

    Non genera testo — restituisce solo i chunk con i loro score.

    Args:
        project_ids: lista di project_id per filtrare i chunk.
                     None = ricerca su tutta la knowledge base.
        top_k:       numero iniziale di leaf chunk da recuperare prima del merge.
                     Valore più alto = più candidati per il reranker.
                     Default 10 (poi SentenceTransformerRerank porta a top_n=3).

    Usato da:
    - rag_service.py    → POST /chat
    - search_service.py → POST /search
    - agent/tools.py    → tool search_semantic
    """
    index = get_vector_store_index()
    filters = _build_project_filters(project_ids)

    storage_context = StorageContext.from_defaults(
        vector_store=get_vector_store(),
        docstore=get_docstore(),
    )

    base_retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=top_k,
        filters=filters,
    )

    return AutoMergingRetriever(
        vector_retriever=base_retriever,
        storage_context=storage_context,
        verbose=False,
    )


# ---------------------------------------------------------------------------
# Helper privato
# ---------------------------------------------------------------------------

def _build_project_filters(
    project_ids: Optional[list[str]],
) -> Optional[MetadataFilters]:
    """
    Costruisce il filtro MetadataFilters di LlamaIndex per project_id.

    LlamaIndex traduce MetadataFilters in un pre-filter MongoDB compatibile
    con $vectorSearch. Il campo filtrato è metadata.project_id (path nested)
    che deve essere indicizzato come "filter" nell'indice mongot.

    Con un solo project_id usa EQ (più efficiente).
    Con più project_id usa IN.
    Con None ritorna None — nessun filtro, ricerca globale.
    """
    if not project_ids:
        return None

    if len(project_ids) == 1:
        return MetadataFilters(
            filters=[
                MetadataFilter(
                    key="metadata.project_id",
                    value=project_ids[0],
                    operator=FilterOperator.EQ,
                )
            ]
        )

    return MetadataFilters(
        filters=[
            MetadataFilter(
                key="metadata.project_id",
                value=project_ids,
                operator=FilterOperator.IN,
            )
        ]
    )
