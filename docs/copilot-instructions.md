# MementoAI — Copilot Instructions

This file provides GitHub Copilot with context about the MementoAI project to improve code generation quality.

## Project Summary

MementoAI is a local-first desktop knowledge base application. Users write structured documents (ADRs, postmortems, updates), and can query them via semantic search and RAG-powered AI chat. The UI is a Notion-like desktop app built with Tauri v2.

## Repository Structure

```
MementoAI/
├── app/                  ← Python FastAPI backend
│   ├── main.py           ← FastAPI app entry point
│   ├── config.py         ← Pydantic settings (.env)
│   ├── db/mongo.py       ← MongoDB async client
│   ├── models/           ← Pydantic models (entry, chat, search)
│   ├── routers/          ← FastAPI routers (entries, search, chat)
│   ├── services/         ← Business logic (entry_service, chat_service, rag, embedding, classifier)
│   └── mappers/          ← MongoDB document ↔ Pydantic model conversion
├── ui/                   ← Tauri + React frontend (to be created)
│   ├── src/
│   │   ├── api/          ← Fetch wrappers for backend endpoints
│   │   ├── components/   ← React components
│   │   ├── store/        ← Zustand state stores
│   │   ├── hooks/        ← Custom React hooks
│   │   └── types/        ← TypeScript types
│   └── src-tauri/        ← Tauri Rust shell
└── docs/
    ├── architecture.md   ← System architecture overview
    ├── frontend-spec.md  ← Full frontend specification
    └── copilot-instructions.md  ← This file
```

## Backend API Reference

Base URL: `http://localhost:8000`

| Method | Path | Description | Body / Params |
|---|---|---|
|---|
| GET | `/entries` | List entries | `?project=&type=&week=&limit=20&skip=0` |
| GET | `/entries/{id}` | Get single entry | — |
| POST | `/entries` | Create entry (no LLM) | `EntryCreate` |
| PUT | `/entries/{id}` | Save entry (no LLM) | `EntryUpdate` |
| POST | `/entries/{id}/index` | Vectorize entry (LLM) | — |
| DELETE | `/entries/{id}` | Delete entry | — |
| POST | `/search` | Semantic search | `SearchRequest` |
| POST | `/chat` | RAG chat | `ChatRequest` |

## Core TypeScript Types

```typescript
type EntryType = 'adr' | 'postmortem' | 'update';
type VectorStatus = 'pending' | 'indexed' | 'outdated';

interface Entry {
  id: string;
  raw_text: string;
  type: EntryType;
  title: string;
  summary: string;
  project: string;
  author: string;
  tags: string[];
  created_at: string;
  week: string;
  vector_status: VectorStatus;
}

interface SearchResult {
  id: string;
  title: string;
  summary: string;
  raw_text: string;
  type: EntryType;
  project: string;
  author: string;
  tags: string[];
  score: float;
}

interface SearchRequest { query: string; project?: string; top_k?: number; }
interface ChatRequest   { question: string; project: string; top_k?: number; }
```

## Frontend Conventions

- **Framework**: React 19 + TypeScript + Vite inside Tauri v2
- **Styling**: TailwindCSS v4 utility classes only — no inline styles, no CSS modules
- **Components**: Use shadcn/ui primitives where available (Button, Dialog, Input, Badge, ScrollArea, Drawer, Separator, Tooltip)
- **State**: Zustand stores in `src/store/`. Keep component state local unless shared across routes
- **API calls**: Always go through `src/api/` wrappers, never call `fetch` directly in components
- **Editor**: TipTap v2 with `@tiptap/react`. The editor content is stored as Markdown (use `@tiptap/extension-markdown` for serialization)
- **No class components** — functional components and hooks only
- **File naming**: PascalCase for components (`EntryList.tsx`), camelCase for hooks/utils/store

## Backend Conventions

- **Language**: Python 3.11+
- **Async**: All service functions are `async def`. Always `await` async calls
- **Database**: Use motor (async pymongo). Collection name for entries: `entries`
- **Embeddings**: Generated via `services/embedding.py` (calls Ollama). Only called from `index_entry()`, never from `create_entry()` or `update_entry()`
- **Save vs Index**: `PUT /entries/{id}` persists data only (fast, no LLM). `POST /entries/{id}/index` runs classifier + embedding (slow, LLM). `vector_status` tracks indexing state: `pending` → `outdated` → `indexed`
- **Models**: Pydantic v2. `EntryDocument` is the MongoDB model (includes `embedding`). `EntryResponse` is the API response (no embedding exposed)
- **ObjectId**: Convert to `str` in mappers, never expose raw `ObjectId`
- **Error handling**: Raise `HTTPException` in routers. Services return `None` for not-found cases

## Design Language

- **Color palette**: Near-white background (`#FAFAFA`), dark text (`#1A1A1A`), subtle borders (`#E5E5E5`), accent (`#0F172A`)
- **Typography**: System font stack. Headings semi-bold, body regular
- **Spacing**: Generous padding, minimal visual weight — Notion aesthetic
- **Entry type badges**: ADR → blue, Postmortem → red/orange, Update → green
- **No heavy shadows** — use borders and background contrast instead

## Key UX Patterns

- Autosave on editor blur or after 1.5s debounce (PUT /entries/:id)
- Search is semantic (POST /search), not text filter — always debounce 300ms
- Chat panel is a right drawer, scoped to the currently active project
- Keyboard shortcuts: `Ctrl+K` search, `Ctrl+J` chat, `Ctrl+N` new entry, `Ctrl+S` save
