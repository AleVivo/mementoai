"""
Reader per contenuto HTML generato da TipTap.

Strategia: produce un singolo Document per entry con il testo strutturato
(headings preservati in stile markdown ## Heading).
Il chunking gerarchico è delegato a HierarchicalNodeParser in pipeline.py:
  - root   ~2048 token  → nodi padre, contesto ampio per AutoMergingRetriever
  - medio  ~512  token  → nodi intermedi
  - leaf   ~128  token  → nodi foglia embeddati su MongoDB (collection chunks)
"""

import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup, Tag
from llama_index.core import Document

from app.models.chunk import MetadataFields

logger = logging.getLogger(__name__)

_HEADING_TAGS = {"h1", "h2", "h3", "h4"}

_ALL_METADATA_KEYS = [
    v for k, v in vars(MetadataFields).items()
    if not k.startswith("_") and isinstance(v, str)
]


def read(
    content: str | bytes,
    entry_id: str,
    project_id: str,
    entry_type: str,
    entry_title: str,
    created_at: datetime,
    **kwargs: object,
) -> list[Document]:
    """
    Trasforma HTML TipTap in un singolo Document pronto per IngestionPipeline.

    Il testo risultante mantiene la struttura degli heading (## stile markdown)
    così HierarchicalNodeParser può produrre chunk semanticamente coerenti.

    Firma coerente con ReaderFn in base.py.
    """
    if not isinstance(content, str) or not content.strip():
        logger.warning(f"[html_reader] entry {entry_id} — contenuto non valido, skip")
        return []

    structured_text = _html_to_structured_text(content)
    if not structured_text.strip():
        logger.warning(f"[html_reader] entry {entry_id} — nessun testo estratto")
        return []

    logger.info(
        f"[html_reader] entry {entry_id!r} — "
        f"{len(structured_text)} chars estratti"
    )

    metadata: dict = {
        MetadataFields.ENTRY_ID:    entry_id,
        MetadataFields.PROJECT_ID:  project_id,
        MetadataFields.ENTRY_TYPE:  entry_type,
        MetadataFields.ENTRY_TITLE: entry_title,
        MetadataFields.CREATED_AT:  created_at.isoformat(),
        MetadataFields.FOLDER_ID:   kwargs.get("folder_id"),  # str | None
    }

    return [Document(
        id_=entry_id,       # doc_id = entry_id → usato da delete_ref_doc() per cleanup
        text=structured_text,
        metadata=metadata,
        excluded_embed_metadata_keys=_ALL_METADATA_KEYS,
        excluded_llm_metadata_keys=[
            MetadataFields.ENTRY_ID,
            MetadataFields.CREATED_AT,
        ],
    )]


# ---------------------------------------------------------------------------
# Helpers privati
# ---------------------------------------------------------------------------

def _html_to_structured_text(html: str) -> str:
    """
    Converte TipTap HTML in testo strutturato con headings stile markdown.

    Gli heading (h1-h4) diventano "## Titolo" in modo che
    HierarchicalNodeParser possa usarli come separatori semantici naturali.
    """
    sections = _extract_sections(html)
    parts: list[str] = []
    for heading, body in sections:
        if heading:
            parts.append(f"## {heading}\n{body}")
        else:
            parts.append(body)
    return "\n\n".join(parts)


def _extract_sections(html: str) -> list[tuple[str, str]]:
    """
    Divide l'HTML in sezioni (heading, testo_sezione).
    Sezione iniziale senza heading inclusa con heading vuoto "".
    """
    soup = BeautifulSoup(html, "html.parser")
    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_texts: list[str] = []

    for element in soup.descendants:
        if not isinstance(element, Tag):
            continue
        if element.parent and element.parent.name in _HEADING_TAGS:
            continue

        if element.name in _HEADING_TAGS:
            if current_texts:
                body = _clean_text(" ".join(current_texts))
                if body:
                    sections.append((current_heading, body))
            current_heading = _clean_text(element.get_text())
            current_texts = []

        elif element.name in {"p", "li", "td", "th", "blockquote", "pre", "code"}:
            if not _has_captured_ancestor(element):
                text = _clean_text(element.get_text())
                if text:
                    current_texts.append(text)

    if current_texts:
        body = _clean_text(" ".join(current_texts))
        if body:
            sections.append((current_heading, body))

    return sections


def _has_captured_ancestor(element: Tag) -> bool:
    """Evita duplicazione del testo per elementi annidati."""
    captured = {"p", "li", "td", "th", "blockquote", "pre", "code"}
    parent = element.parent
    while parent:
        if isinstance(parent, Tag) and parent.name in captured and parent != element:
            return True
        parent = parent.parent if isinstance(parent, Tag) else None
    return False


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
