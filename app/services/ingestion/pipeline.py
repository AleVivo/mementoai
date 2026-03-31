"""
services/ingestion/pipeline.py

Orchestratore della pipeline di indicizzazione.

Punto di ingresso chiamato da entry_service.index_entry().
Seleziona il reader giusto, produce i Document e li indicizza tramite
LlamaIndex IngestionPipeline con HierarchicalNodeParser.

Architettura a 3 livelli di chunk (HierarchicalNodeParser):
  - root   ~2048 token  → nodi padre, conservati in node_docstore (MongoDocumentStore)
  - medio  ~512  token  → nodi intermedi, conservati in node_docstore
  - leaf   ~128  token  → nodi foglia embeddati, conservati in chunks (MongoDBAtlasVectorSearch)

AutoMergingRetriever in retriever.py usa node_docstore per espandere
il contesto dei leaf node quando più fratelli vengono recuperati insieme.

Aggiungere un nuovo formato:
1. Creare services/ingestion/readers/<formato>_reader.py
   implementando la firma definita in readers/base.py
2. Importarlo e aggiungerlo a _READERS qui sotto
"""

import logging
from datetime import datetime

from llama_index.core import Document, Settings
from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy

from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes

from app.services.ingestion.readers import html_reader
from app.services.ingestion.readers.base_reader import ReaderFn
from app.services.retrieval import llama_store


logger = logging.getLogger(__name__)

# Il reader fa **due cose soltanto**:

# 1. **Trasforma il contenuto grezzo** in testo pulito — nel caso HTML, stripping dei tag, estrazione del testo leggibile
# 2. **Costruisce il `Document` LlamaIndex** con i metadati corretti — `doc_id`, `project_id`, `entry_type`, ecc.

_READERS: dict[str, ReaderFn] = {
    "html": html_reader.read,
}

# HierarchicalNodeParser: produce 3 livelli di nodi dalla stessa entry.
# chunk_sizes=[2048, 512, 128]:
#   2048 → root (una o poche sezioni, contesto ampio)
#   512  → intermedi (paragrafi)
#   128  → leaf (frasi, embeddati su Atlas)
_node_parser = HierarchicalNodeParser.from_defaults(
    chunk_sizes=[2048, 512, 128],
)


async def run(
    content: str | bytes,
    content_type: str,
    entry_id: str,
    project_id: str,
    entry_type: str,
    entry_title: str,
    created_at: datetime,
    **kwargs: object,
) -> int:
    """
    Esegue la pipeline completa: reader → HierarchicalNodeParser → embedding → MongoDB.

    Punto di ingresso pubblico chiamato da entry_service.index_entry().

    Scrive:
    - leaf nodes (128t) + embedding → collection chunks  (vector store)
    - tutti i nodi                  → collection node_docstore/data (docstore)

    Args:
        content:      contenuto del documento (str per HTML, bytes per binari)
        content_type: formato — oggi solo "html", in futuro "pdf" | "docx" | "md"
        entry_id:     ObjectId serializzato come stringa
        project_id:   ID del progetto
        entry_type:   "adr" | "postmortem" | "update"
        entry_title:  titolo dell'entry
        created_at:   timestamp di creazione
        **kwargs:     argomenti extra passati al reader (es. filename per i binari)

    Returns:
        Numero di Document processati. 0 se il contenuto non produce output valido
        o il content_type non è supportato.
    """
    documents = _build_documents(
        content=content,
        content_type=content_type,
        entry_id=entry_id,
        project_id=project_id,
        entry_type=entry_type,
        entry_title=entry_title,
        created_at=created_at,
        **kwargs,
    )

    if not documents:
        logger.warning(
            f"[pipeline] nessun documento prodotto per entry {entry_id!r} "
            f"(content_type={content_type!r})"
        )
        return 0

    await _index_documents(documents)
    logger.info(
        f"[pipeline] entry {entry_id!r} — "
        f"{len(documents)} document(s) indicizzati (content_type={content_type!r})"
    )
    return len(documents)


# ---------------------------------------------------------------------------
# Privati
# ---------------------------------------------------------------------------

def _build_documents(
    content: str | bytes,
    content_type: str,
    entry_id: str,
    project_id: str,
    entry_type: str,
    entry_title: str,
    created_at: datetime,
    **kwargs: object,
) -> list[Document]:
    """
    Seleziona il reader corretto e produce i Document.
    Non scrive su MongoDB.
    """
    reader = _READERS.get(content_type)

    if reader is None:
        logger.error(
            f"[pipeline] content_type non supportato: {content_type!r} "
            f"(entry_id={entry_id}). "
            f"Tipi disponibili: {list(_READERS.keys())}"
        )
        return []

    return reader(
        content=content,
        entry_id=entry_id,
        project_id=project_id,
        entry_type=entry_type,
        entry_title=entry_title,
        created_at=created_at,
        **kwargs,
    )


async def _index_documents(documents: list[Document]) -> None:
    """
    Esegue HierarchicalNodeParser + embedding + scrittura su MongoDB.

    IngestionPipeline gestisce automaticamente:
    - Parsing gerarchico (3 livelli di chunk)
    - Generazione embedding per i soli leaf node (Settings.embed_model)
    - Scrittura leaf+embedding su vector_store (chunks)
    - Scrittura tutti i nodi su docstore (node_docstore/data)
    """
    docstore = llama_store.get_docstore()
    vector_store = llama_store.get_vector_store()

    for doc in documents:
        entry_id = doc.doc_id
        await docstore.adelete_ref_doc(entry_id, raise_error=False)
        await vector_store.adelete(entry_id)

    all_nodes = _node_parser.get_nodes_from_documents(documents)
    leaf_nodes = get_leaf_nodes(all_nodes)

    if not all_nodes:
        logger.warning("[pipeline] nessun nodo prodotto dal parser")
        return
    
    await docstore.async_add_documents(all_nodes)


    pipeline = IngestionPipeline(
        transformations=[
            Settings.embed_model,
        ],
        vector_store=llama_store.get_vector_store(),
    )
    await pipeline.arun(nodes=leaf_nodes, show_progress=False)

    logger.info(
        f"[pipeline] {len(all_nodes)} nodi totali → docstore, "
        f"{len(leaf_nodes)} leaf → vector store"
    )
