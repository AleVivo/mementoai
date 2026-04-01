# MementoAI — Claude Code

Architettura completa: @docs/architecture.md | Frontend spec: @docs/frontend-spec.md

## Comandi essenziali

```bash
# Backend (dalla root)
uv run uvicorn app.main:app --reload        # avvia API su http://localhost:8000
uv run pytest                               # test (se presenti)
uv run pyright app/                         # type check Python

# Seed dati
uv run python scripts/seed.py              # popola MongoDB con dati di esempio

# Frontend (da ui/)
npm run dev                                 # browser dev server
npm run tauri                              # desktop app Tauri
npx tsc --noEmit --skipLibCheck            # type check TypeScript
```

Prerequisiti: Python 3.13+, `uv`, MongoDB in esecuzione, Node.js 20+.
LLM default: Ollama con `qwen2.5:7b` e `nomic-embed-text`.

## Struttura del monorepo

```
app/                  FastAPI backend
  routers/            endpoint HTTP (1 file per dominio)
  services/
    ai/               RAG, agent LangGraph, SSE streaming
    domain/           logica di business (entry, project, auth, config)
    ingestion/        pipeline chunking + embedding
    retrieval/        vector search, reranker, llama_store
    llm/              factory + provider_cache (LiteLLM)
  db/repositories/    accesso MongoDB (1 repo per collection)
  models/             schemi Pydantic
  dependencies/       FastAPI deps (auth, project, entry access)
  utils/              encryption.py, ecc.
ui/src/               React + Tauri frontend
  api/                client fetch per ogni dominio
  store/              5 Zustand store (auth, projects, entries, ui, chat)
  components/         organizzati per dominio (editor, chat, admin, …)
  hooks/              logica con stato (useEntries, useChat, …)
docs/                 architettura e spec frontend
```

## Decisioni architetturali critiche

**1. AsyncMongoClient — NON Motor**
`from pymongo import AsyncMongoClient`. Motor è deprecato dal 14/05/2025.

**2. No LLM on save**
`PUT /entries/:id` è un puro DB write. Il pipeline AI gira SOLO su `POST /entries/:id/index`.
Non aggiungere mai chiamate LLM nei service di salvataggio.

**3. `vector_status` lifecycle**
Dopo ogni `PUT /entries/:id` → impostare `vector_status = "outdated"`.
Ciclo completo: `pending` → (click "Indicizza") → `indexed`.
Il campo vive sull'Entry document in MongoDB.

**4. Provider cache obbligatoria**
Mai istanziare LLM o embed model direttamente. Sempre:
`get_llm()` / `get_embed_model()` da @app/services/llm/provider_cache.py
Il provider è configurabile a runtime dall'admin console senza riavvio.

**5. Fernet encryption sui secret**
`config_values` in MongoDB contiene secret cifrati con Fernet.
Usare sempre @app/utils/encryption.py per leggere/scrivere — mai accedere raw.

**6. SSE separation pattern**
`@observe` di Langfuse non supporta `AsyncGenerator`.
Pattern obbligatorio: `_execute_rag()` (logica AI, decorata) → `stream_rag()` (wrappa come SSE).
Vedi @app/services/ai/sse.py e @app/services/ai/rag_service.py.

**7. LlamaIndex chunking gerarchico**
`HierarchicalNodeParser`: 2048 → 512 → 128 token.
Solo i leaf node (128 token) vengono embeddati.
`AutoMergingRetriever` promuove cluster di leaf al parent a query time.
Non modificare queste soglie senza verificare il recall.

**8. `InjectedState` per project_ids negli agent tool**
Gli agent tool ricevono `project_ids` via `InjectedState`, non come argomento LLM.
Vedi @app/services/ai/agent_state.py e @app/services/ai/agent_tools.py.

## Come verificare il tuo lavoro

```bash
# Frontend
cd ui && npx tsc --noEmit --skipLibCheck

# Backend
uv run pyright app/

# Test
uv run pytest

# Config MongoDB vector index (se hai modificato ingestion)
mongosh --eval "db.chunks.getIndexes()"
```

## Cosa non toccare

- **Motor**: non importare mai `motor` — rimosso, usa `pymongo.AsyncMongoClient`
- **LLM nel save**: nessuna chiamata AI in `PUT /entries/:id` o autosave
- **LiteLLM diretto**: non istanziare provider fuori da `provider_cache.py`
- **Secret raw**: non leggere `config_values` senza decrypt via `encryption.py`
- **`.env` diretto**: modificare le variabili d'ambiente manualmente, non via script
