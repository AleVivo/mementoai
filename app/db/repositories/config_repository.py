"""
Repository per le collection config_schema e config_values.

config_schema  — read-only, scritto direttamente su MongoDB dallo sviluppatore
config_values  — scritto tramite PUT /admin/config/{section_id}

Entrambe le collection usano _id stringa semantica ("llm", "embedding", ...)
invece di ObjectId — è una scelta deliberata perché questi documenti hanno
un'identità naturale nota a design time.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.db.client import get_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# config_schema — solo lettura
# ---------------------------------------------------------------------------

async def get_all_schemas() -> list[dict]:
    """
    Restituisce tutti i documenti config_schema ordinati per _id.
    """
    cursor = get_db().config_schema.find({}).sort("_id", 1)
    return await cursor.to_list(length=None)


async def get_schema(section_id: str) -> Optional[dict]:
    """
    Restituisce il documento config_schema per la sezione richiesta.
    Restituisce None se la sezione non esiste.
    """
    return await get_db().config_schema.find_one({"_id": section_id})


# ---------------------------------------------------------------------------
# config_values — lettura e scrittura
# ---------------------------------------------------------------------------

async def get_all_values() -> list[dict]:
    """
    Restituisce tutti i documenti config_values.
    """
    cursor = get_db().config_values.find({})
    return await cursor.to_list(length=None)


async def get_values(section_id: str) -> Optional[dict]:
    """
    Restituisce il documento config_values per la sezione richiesta.
    Restituisce None se non esiste ancora — il service gestisce questo caso
    restituendo una sezione senza valori nel merge.
    """
    return await get_db().config_values.find_one({"_id": section_id})


async def upsert_values(
    section_id: str,
    values: dict,
    updated_by: str,
) -> dict:
    """
    Inserisce o aggiorna i values per una sezione.

    Perché upsert=True:
    - Se il documento esiste → aggiorna solo i campi in $set
    - Se non esiste → crea il documento con $set + $setOnInsert

    Perché $setOnInsert per status e last_tested_at:
    - Questi campi vengono gestiti separatamente quando implementeremo
      il test delle integration
    - Non vogliamo resettarli ad ogni salvataggio dei values
    - $setOnInsert viene eseguito SOLO alla creazione del documento,
      mai negli aggiornamenti successivi

    Restituisce il documento completo aggiornato.
    """
    now = datetime.now(timezone.utc)

    await get_db().config_values.update_one(
        {"_id": section_id},
        {
            "$set": {
                "values": values,
                "updated_at": now,
                "updated_by": updated_by,
            },
            "$setOnInsert": {
                "_id": section_id,
                "status": "unknown",
                "status_message": None,
                "last_tested_at": None,
            },
        },
        upsert=True,
    )

    doc = await get_db().config_values.find_one({"_id": section_id})
    if doc is None:
        raise RuntimeError(f"upsert_values: documento non trovato dopo upsert per _id={section_id}")
    return doc