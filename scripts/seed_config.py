"""
seed_config.py — Inserisce config_schema e config_values di default.

config_schema: definisce la struttura della admin console.
               Viene sempre sovrascritto — è codice, non dati utente.

config_values: inserisce i valori di default per Ollama solo se non esistono.
               Con --reset vengono ricreati da zero.
"""

from datetime import datetime, timezone
from pymongo import AsyncMongoClient


CONFIG_SCHEMAS = [
    {
        "_id": "llm",
        "type": "integration",
        "label": "LLM Provider",
        "description": "Configurazione del modello linguistico per chat e agente",
        "fields": [
            {
                "key": "provider",
                "label": "Provider",
                "type": "select",
                "options": [
                    {"value": "ollama_chat", "label": "Ollama"},
                    {"value": "openai", "label": "OpenAI"},
                    {"value": "groq",   "label": "Groq"},
                ],
                "required": True,
            },
            {
                "key": "host",
                "label": "Host",
                "type": "text",
                "placeholder": "http://localhost:11434",
                "required_if": {"field": "provider", "in": ["ollama_chat"]},
            },
            {
                "key": "model",
                "label": "Modello",
                "type": "select",
                "depends_on": {
                    "field": "provider",
                    "options": {
                        "ollama_chat": [
                            {"value": "qwen2.5:7b",  "label": "Qwen 2.5 7B"},
                            {"value": "llama3.2:3b", "label": "Llama 3.2 3B"},
                            {"value": "qwen2.5:3b", "label": "Qwen 2.5 3B"},
                        ],
                        "openai": [
                            {"value": "gpt-4o-mini", "label": "GPT-4o Mini"},
                            {"value": "gpt-4o",      "label": "GPT-4o"},
                        ],
                        "groq": [
                            {"value": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B"},
                            {"value": "llama-3.1-8b-instant",      "label": "Llama 3.1 8B Instant"},
                        ],
                    },
                },
                "required": True,
            },
            {
                "key": "api_key",
                "label": "API Key",
                "type": "secret",
                "required_if": {"field": "provider", "not_in": ["ollama_chat"]},
            },
        ],
    },
    {
        "_id": "embedding",
        "type": "integration",
        "label": "Embedding Provider",
        "description": "Modello per la vettorializzazione dei contenuti",
        "fields": [
            {
                "key": "provider",
                "label": "Provider",
                "type": "select",
                "options": [
                    {"value": "ollama", "label": "Ollama"},
                    {"value": "openai", "label": "OpenAI"},
                ],
                "required": True,
            },
            {
                "key": "host",
                "label": "Host",
                "type": "text",
                "placeholder": "http://localhost:11434",
                "required_if": {"field": "provider", "in": ["ollama"]},
            },
            {
                "key": "model",
                "label": "Modello",
                "type": "select",
                "depends_on": {
                    "field": "provider",
                    "options": {
                        "ollama": [
                            {"value": "nomic-embed-text", "label": "Nomic Embed Text"},
                        ],
                        "openai": [
                            {"value": "text-embedding-3-small", "label": "Text Embedding 3 Small"},
                            {"value": "text-embedding-3-large", "label": "Text Embedding 3 Large"},
                        ],
                    },
                },
                "required": True,
            },
            {
                "key": "api_key",
                "label": "API Key",
                "type": "secret",
                "required_if": {"field": "provider", "not_in": ["ollama"]},
            },
        ],
    },
    {
        "_id": "observability",
        "type": "integration",
        "label": "Observability",
        "description": "Tracing e monitoring delle chiamate AI",
        "fields": [
            {
                "key": "provider",
                "label": "Provider",
                "type": "select",
                "options": [
                    {"value": "none",     "label": "Nessuno"},
                    {"value": "langfuse", "label": "Langfuse"},
                ],
                "required": True,
            },
            {
                "key": "host",
                "label": "Host",
                "type": "text",
                "placeholder": "http://localhost:3000",
                "required_if": {"field": "provider", "not_in": ["none"]},
            },
            {
                "key": "public_key",
                "label": "Public Key",
                "type": "text",
                "required_if": {"field": "provider", "not_in": ["none"]},
            },
            {
                "key": "secret_key",
                "label": "Secret Key",
                "type": "secret",
                "required_if": {"field": "provider", "not_in": ["none"]},
            },
        ],
    },
]


CONFIG_VALUES_DEFAULT = [
    {
        "_id": "llm",
        "values": {
            "provider": "ollama_chat",
            "host": "http://localhost:11434",
            "model": "qwen2.5:3b",
            "api_key": None,
        },
        "status": "unknown",
        "status_message": None,
        "last_tested_at": None,
        "updated_at": None,
        "updated_by": None,
    },
    {
        "_id": "embedding",
        "values": {
            "provider": "ollama",
            "host": "http://localhost:11434",
            "model": "nomic-embed-text",
            "api_key": None,
        },
        "status": "unknown",
        "status_message": None,
        "last_tested_at": None,
        "updated_at": None,
        "updated_by": None,
    },
    {
        "_id": "observability",
        "values": {
            "provider": "none",
            "host": None,
            "public_key": None,
            "secret_key": None,
        },
        "status": "unknown",
        "status_message": None,
        "last_tested_at": None,
        "updated_at": None,
        "updated_by": None,
    },
]


# ==============================================================================
# INDICE VETTORIALE
# ==============================================================================

VECTOR_INDEX_NAME = "chunks_vector_index"
EMBEDDING_DIMENSIONS = 768


async def drop_vector_index(db) -> None:
    existing_names: list[str] = []
    try:
        cursor = await db.chunks.list_search_indexes()
        async for idx in cursor:
            existing_names.append(idx.get("name", ""))
    except Exception:
        return  # collection non esiste ancora — nulla da eliminare

    if VECTOR_INDEX_NAME not in existing_names:
        return

    try:
        await db.command("dropSearchIndex", "chunks", name=VECTOR_INDEX_NAME)
        print(f"🗑  Indice vettoriale '{VECTOR_INDEX_NAME}' eliminato")
    except Exception as e:
        print(f"⚠️  Impossibile eliminare l'indice: {e}")


async def ensure_vector_index(db) -> None:
    try:
        await db.create_collection("chunks")
    except Exception:
        pass

    existing_names: list[str] = []
    cursor = await db.chunks.list_search_indexes()
    async for idx in cursor:
        existing_names.append(idx.get("name", ""))

    if VECTOR_INDEX_NAME in existing_names:
        print(f"ℹ️  Indice vettoriale '{VECTOR_INDEX_NAME}' già presente — skip")
        return

    index_definition = {
        "name": VECTOR_INDEX_NAME,
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": EMBEDDING_DIMENSIONS,
                    "similarity": "cosine",
                },
                # Filtro per project scope (ObjectId stringificato)
                {"type": "filter", "path": "project_id"},
                {"type": "filter", "path": "entry_type"},
            ]
        },
    }

    try:
        await db.command("createSearchIndexes", "chunks", indexes=[index_definition])
        print(f"✅ Indice vettoriale '{VECTOR_INDEX_NAME}' creato")
        print(f"   {EMBEDDING_DIMENSIONS} dimensioni — cosine — filtri: projectId, entry_type")
        print(f"   ⏳ Diventa READY dopo qualche secondo (mongot lo costruisce in background)\n")
    except Exception as e:
        err_msg = str(e)
        if "replica set" in err_msg.lower() or "replicaset" in err_msg.lower():
            print(f"⚠️  Indice vettoriale NON creato: MongoDB non è configurato come replica set.")
        else:
            print(f"⚠️  Indice vettoriale NON creato: {err_msg}")



async def run(db, reset: bool = False) -> None:
    # config_schema — sempre sovrascritto con upsert
    # È codice, non dati utente — deve sempre riflettere la versione corrente
    for schema in CONFIG_SCHEMAS:
        await db.config_schema.replace_one(
            {"_id": schema["_id"]},
            schema,
            upsert=True,
        )
    print(f"✅ config_schema: {len(CONFIG_SCHEMAS)} sezioni aggiornate")

    # config_values — reset pulisce e reinserisce, altrimenti skip se esistono
    if reset:
        await db.config_values.delete_many({})
        print("🗑  config_values: eliminati")

    inserted = 0
    skipped = 0
    for values in CONFIG_VALUES_DEFAULT:
        existing = await db.config_values.find_one({"_id": values["_id"]})
        if existing:
            skipped += 1
        else:
            await db.config_values.insert_one(values)
            inserted += 1

    if inserted:
        print(f"✅ config_values: {inserted} sezioni inserite con valori Ollama default")
    if skipped:
        print(f"ℹ️  config_values: {skipped} sezioni già presenti — skip")