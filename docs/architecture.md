---
generated_by: GitHub Copilot (Claude Sonnet 4.6)
last_updated: 2026-03-14
---

# MementoAI — Architecture

## Overview

MementoAI is a local-first knowledge base and AI chat application. It allows teams to document decisions (ADR), postmortems, and updates, then query the knowledge base via semantic search and RAG-powered chat.

## System Architecture

```
┌─────────────────────────────────────────────────┐
│  Desktop App (Tauri v2)                         │
│  ┌──────────────────────────────────────────┐   │
│  │  Frontend (React + Vite)                 │   │
│  │  ┌─────────────┬────────────────────┐   │   │
│  │  │  Sidebar    │  Main Panel        │   │   │
│  │  │  - Projects │  ┌──────────────┐  │   │   │
│  │  │  - Entries  │  │ TipTap Block │  │   │   │
│  │  │  - Search   │  │ Editor       │  │   │   │
│  │  │             │  └──────────────┘  │   │   │
│  │  │             │  ┌──────────────┐  │   │   │
│  │  │             │  │ RAG Chat     │  │   │   │
│  │  │             │  │ Panel        │  │   │   │
│  │  │             │  └──────────────┘  │   │   │
│  │  └─────────────┴────────────────────┘   │   │
│  └──────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────┘
                   │ HTTP localhost:8000
┌──────────────────▼──────────────────────────────┐
│  Backend (FastAPI — Python)                     │
│                                                 │
│  POST /entries          ← create entry          │
│  GET  /entries          ← list entries (filter) │
│  GET  /entries/:id      ← get single entry      │
│  PUT  /entries/:id      ← save entry (no LLM)   │
│  POST /entries/:id/index← vectorize entry       │
│  DEL  /entries/:id      ← delete entry          │
│  POST /search           ← semantic vector search│
│  POST /chat             ← RAG chat question     │
│  POST /agent            ← ReAct agent question  │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────┐   ┌──────────▼──────────┐
│  MongoDB     │   │  Ollama (local LLM)  │
│  (documents  │   │  - embeddings        │
│  + vectors)  │   │  - chat completion   │
└──────────────┘   └─────────────────────┘
```

## Backend (requires changes — see Data Flow section)

**Stack:** Python 3.11+, FastAPI, uvicorn, pymongo, httpx, pydantic-settings

### Domain Model

**Entry** — the core document unit:
| Field | Type | Description |
|---|---|---|
| `id` | `str` | MongoDB ObjectId |
| `entry_type` | `EntryType` | `adr` \| `postmortem` \| `update` |
| `title` | `str` | Document title |
| `project` | `str` | Project/team namespace |
| `author` | `str` | Author name |
| `content` | `str` | Full markdown content |
| `summary` | `str` | AI-generated summary |
| `tags` | `list[str]` | Classification tags |
| `embedding` | `list[float]` | Vector embedding (stored, not exposed) |
| `created_at` | `datetime` | Creation timestamp |
| `week` | `str` | ISO week string (e.g. `2026-W10`) |
| `vector_status` | `VectorStatus` | `pending` \| `indexed` \| `outdated` |

### Services
- `entry_service` — CRUD operations on entries
- `search_service` — semantic vector search via chunk embeddings
- `chat_service` — orchestrates search + RAG
- `agent` — loop ReAct: il modello ragiona iterativamente, sceglie un tool dal registry, esegue, osserva il risultato e itera fino alla risposta finale (max `max_steps` iterazioni)
- `agent_registry` — catalogo dei tool disponibili all'agente: ricerca semantica, filtri per progetto/tipo, conteggi
- `classifier` — ⚠️ **DEPRECATED** — `enrich_entry` (summary/tag LLM) rimosso dalla pipeline di indicizzazione, codice preservato
- `chunker` — parsing HTML TipTap → chunk per heading, max 300 token (cl100k_base / tiktoken)
- `embedding` — genera embedding vettoriale via Ollama (`nomic-embed-text`, 768 dim)
- `rag` — costruisce il prompt context e chiama Ollama per la risposta chat
- `ollama` — HTTP client per Ollama; gestisce preload/unload modelli al lifecycle dell'app

### Modelli Ollama
| Modello | Uso |
|---|---|
| `qwen2.5:7b` | Generazione risposte RAG chat |
| `nomic-embed-text` | Embedding vettoriale dei chunk (768 dim) |

Entrambi vengono pre-caricati all'avvio dell'app (`keep_alive: -1`) e scaricati allo shutdown.

## Frontend

**Stack:** Tauri v2, React 19, Vite, TypeScript, TailwindCSS, shadcn/ui, TipTap ^3, Zustand, react-markdown

See [frontend-spec.md](./frontend-spec.md) for full detail.

## Data Flow

### Create Entry
```
POST /entries { content, entry_type, title, project, author }
  → Stored in MongoDB with vector_status = "pending"
  → Response: EntryResponse (fast, no LLM)
  → UI: entry aperta nell'editor, indicatore "⚠ Not indexed"
```

### Save Entry (autosave / Cmd+S)
```
PUT /entries/:id { content, title, ... }
  → MongoDB update (solo dati, no LLM)
  → vector_status = "outdated"
  → Response: EntryResponse aggiornata (fast)
```

### Index Entry
```
POST /entries/:id/index  (trigger: manuale tramite pulsante "Indicizza" nella toolbar)
  → Backend: legge content corrente
  → chunker   → divide HTML in chunk per heading (max 300 token)
  → embedding → vettore per ogni chunk (nomic-embed-text)
  → MongoDB:  - cancella chunk precedenti
              - inserisce nuovi chunk con embedding nella collection `chunks`
              - imposta vector_status = "indexed"
  → Response: EntryResponse con vector_status aggiornato
  → UI: indicatore "✓ Indexed" (scompare dopo 3s)

Nota: summary e tag NON vengono generati automaticamente.
Sono gestiti manualmente dall'utente nell'editor.
```

### Semantic Search
```
User types in search box
  → Debounced POST /search { query, project?, top_k }
  → Backend: query embedded → cosine similarity against DB
  → Returns ranked EntryResponse list
  → Results displayed in main panel
```

### RAG Chat
```
User types question in chat panel (modalità RAG)
  → POST /chat { question, project? }
     - project omesso = ricerca su tutta la knowledge base
     - project valorizzato = scopo limitato al progetto
  → Backend: query embedded (nomic-embed-text)
           → vector search sui chunk (collection `chunks`, indice `chunks_vector_index`)
           → top-k chunk recuperati
           → SSE stream aperto:
               data: {"type":"sources","sources":[{"entry_id","title","entry_type","section"},...]}
               data: {"type":"token","content":"..."}   ← uno per token
               data: {"type":"done"}
  → Frontend: SSEEvent parsed da streamChat() async generator
  → sources event → ChatMessage.sources popolato (accordion fonti)
  → token events  → content appendato token by token
  → done event    → isStreaming = false
  → Answer rendered as markdown in chat bubble
  → Sources shown as collapsible accordion above the text
```

### Agent Chat
```
User types question in chat panel (modalità Agent)
  → POST /agent { question, project?, max_steps }
     - project omesso = tool operano su tutta la knowledge base
  → Backend: loop ReAct — max max_steps iterazioni
       1. LLM ragiona sull'input (Thought)
       2. Sceglie un tool dal registry (Action)
             tool disponibili: search_semantic, filter_by_project,
                               filter_by_type, count_entries, get_entry
       3. Esegue il tool e osserva il risultato (Observation)
       4. Ripete finché ha abbastanza informazioni o raggiunge max_steps
       5. Genera la risposta finale
  → Response: { answer: string, steps: [{ tool, args, result }], model }
  → Answer rendered as markdown in chat bubble
```

## Deployment

The application runs fully locally:
- Tauri bundles the frontend as a native desktop binary
- FastAPI starts on `localhost:8000` (launched by Tauri sidecar or separately)
- MongoDB runs locally or via connection string in `.env`
- Ollama runs as a local service

No cloud dependencies. All data remains on-device.
