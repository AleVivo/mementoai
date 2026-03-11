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
- `search_service` — semantic vector search via embeddings
- `chat_service` — orchestrates search + RAG
- `classifier` — auto-tagging / classification
- `embedding` — generates vector embeddings via Ollama
- `rag` — builds prompt context and calls Ollama for chat response
- `ollama` — HTTP client wrapper for Ollama API

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
POST /entries/:id/index  (trigger: onBlur editor o manuale)
  → Backend: legge content corrente
  → classifier → summary + tags  (LLM call)
  → embedding  → vettore         (Ollama call)
  → MongoDB: aggiorna embedding, summary, tags, vector_status = "indexed"
  → Response: EntryResponse con vector_status aggiornato
  → UI: indicatore "✓ Indexed"
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
User types question in chat panel (requires active project)
  → POST /chat { question, project }
  → Backend: semantic search → retrieve top-k entries scoped to project
  → Backend: build prompt with context → Ollama completion
  → Response: { answer: string, sources: [{ ref, id, title, type, score }] }
  → Answer rendered as markdown in chat bubble
  → Sources shown as clickable references
```

## Deployment

The application runs fully locally:
- Tauri bundles the frontend as a native desktop binary
- FastAPI starts on `localhost:8000` (launched by Tauri sidecar or separately)
- MongoDB runs locally or via connection string in `.env`
- Ollama runs as a local service

No cloud dependencies. All data remains on-device.
