"""
Contratto che ogni reader deve rispettare.

Aggiungere un nuovo formato:
1. Creare un nuovo file, es. readers/pdf_reader.py
2. Implementare la funzione read() con questa stessa firma
3. Registrare l'estensione in pipeline.py → _READERS

Nessun'altra modifica necessaria.
"""

from datetime import datetime
from typing import Protocol

from llama_index.core import Document


class ReaderFn(Protocol):
    def __call__(
        self,
        content: str | bytes,
        entry_id: str,
        project_id: str,
        entry_type: str,
        entry_title: str,
        created_at: datetime,
        **kwargs: object,
    ) -> list[Document]: ...