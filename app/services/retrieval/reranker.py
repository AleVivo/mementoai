"""
- get_reranker()     → SentenceTransformerRerank — cross-encoder locale per riordinare
                        i chunk per rilevanza dopo il retrieval vettoriale.
                        Usato da: rag_service.py, agent/tools.py dopo aretrieve()
"""

import logging

from llama_index.postprocessor.sbert_rerank import SentenceTransformerRerank


logger = logging.getLogger(__name__)

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RERANKER_TOP_N = 3

_reranker: SentenceTransformerRerank | None = None

def get_reranker() -> SentenceTransformerRerank:
    """
    Ritorna il singleton SentenceTransformerRerank.

    Il cross-encoder riordina i chunk per rilevanza semantica precisa
    rispetto alla query — migliora la precision senza aumentare top_k.

    Modello: cross-encoder/ms-marco-MiniLM-L-6-v2 (~80MB, locale, no API calls)
    top_n=3: i 3 chunk più rilevanti dopo il re-ranking vengono passati all'LLM.

    Uso:
        nodes = await retriever.aretrieve(query)
        nodes = get_reranker().postprocess_nodes(nodes, query_str=query)
    """
    global _reranker
    if _reranker is None:
        logger.info("[reranker] Caricamento modello cross-encoder...")
        _reranker = SentenceTransformerRerank(
            model=RERANKER_MODEL,
            top_n=RERANKER_TOP_N,
        )
        logger.info("[reranker] Modello caricato")
    return _reranker
