# MementoAI — Copilot Instructions

MementoAI is a local-first desktop knowledge base for dev teams. Users write structured documents (ADRs, postmortems, updates), search them semantically, and query them via RAG chat.

---

## Repository Structure

```
MementoAI/
├── app/                        ← Python FastAPI backend
│   ├── main.py                 ← FastAPI app + CORSMiddleware
│   ├── config.py               ← Pydantic settings (.env)
│   ├── db/mongo.py             ← Motor (async pymongo) client
│   ├── models/                 ← Pydantic models (entry.py, chat.py, search.py)
│   ├── routers/                ← FastAPI routers (entries, search, chat)
│   ├── services/               ← Business logic (entry_service, chat_service, rag, embedding, classifier)
│   └── mappers/                ← MongoDB doc ↔ Pydantic model conversion
├── ui/                         ← Tauri v2 + React 19 frontend
│   └── src/
│       ├── App.tsx             ← Root layout: Sidebar + MainPanel + ChatPanel
│       ├── api/                ← Fetch wrappers (client.ts, entries.ts, search.ts, chat.ts)
│       ├── components/
│       │   ├── layout/         ← Sidebar.tsx, MainPanel.tsx, ChatPanel.tsx
│       │   ├── editor/         ← EntryEditor.tsx, EditorToolbar.tsx, EntryMeta.tsx (to implement)
│       │   ├── entries/        ← EntryList.tsx, EntryListItem.tsx, EntryTypeBadge.tsx
│       │   ├── search/         ← SearchBar.tsx, SearchResults.tsx (to implement)
│       │   └── ui/             ← shadcn/ui components (auto-generated)
│       ├── store/              ← Zustand: ui.store.ts, entries.store.ts, chat.store.ts
│       ├── hooks/              ← Custom hooks (to implement)
│       ├── types/index.ts      ← TypeScript types (source of truth for frontend)
│       └── lib/utils.ts        ← cn(), formatDate(), formatWeek()
└── .github/
    ├── copilot-instructions.md ← This file (auto-loaded by Copilot)
    └── prompts/                ← Reusable Copilot prompts
```

---

## Backend API Reference

Base URL: `http://localhost:8000`  
CORS: enabled for all origins (CORSMiddleware configured in `main.py`)

| Method | Path | Description | Notes |
|---|---|---|---|
| `GET` | `/entries` | List entries | `?project=&type=&week=&limit=20&skip=0` |
| `GET` | `/entries/{id}` | Get single entry | — |
| `POST` | `/entries` | Create entry | No LLM — fast. `vector_status = pending` |
| `PUT` | `/entries/{id}` | Save entry | No LLM — fast. Sets `vector_status = outdated` |
| `POST` | `/entries/{id}/index` | Vectorize entry | Slow — runs classifier + embedding via Ollama |
| `DELETE` | `/entries/{id}` | Delete entry | — |
| `POST` | `/search` | Semantic vector search | `SearchRequest` body |
| `POST` | `/chat` | RAG chat | `ChatRequest` body |

---

## Backend Python Models (`app/models/entry.py`)

```python
class EntryType(str, Enum):
    adr = "adr"
    postmortem = "postmortem"
    update = "update"

class VectorStatus(str, Enum):
    pending = "pending"
    indexed = "indexed"
    outdated = "outdated"

class EntryResponse(BaseModel):
    id: str
    raw_text: str
    type: EntryType         # ← "type", not "entry_type"
    title: str
    summary: str
    project: str
    author: str
    tags: list[str]
    created_at: datetime
    week: str               # ISO week e.g. "2026-W10"
    vector_status: VectorStatus
```

---

## Frontend TypeScript Types (`ui/src/types/index.ts`)

> ⚠️ **Field name mismatch with backend** — the frontend uses different names than the backend `EntryResponse`. 
> When consuming API responses, map: `raw_text → content`, `type → entry_type`. This mapping must be done in the API layer (`api/entries.ts`).

```typescript
export type EntryType = "adr" | "postmortem" | "update" | "other";
export type VectorStatus = "pending" | "indexed" | "outdated";

export interface Entry {
  id: string;
  title: string;
  content: string;          // ← backend sends "raw_text"
  entry_type: EntryType;    // ← backend sends "type"
  author: string;
  project: string;
  tags: string[];
  summary: string;
  vector_status: VectorStatus;
  created_at: string;
  updated_at: string;
}

export interface EntryCreate {
  title: string;
  content: string;
  entry_type: EntryType;
  author: string;
  project: string;
  tags?: string[];
  summary?: string;
}

export interface EntryUpdate {
  title?: string;
  content?: string;
  entry_type?: EntryType;
  author?: string;
  project?: string;
  tags?: string[];
  summary?: string;
}

export interface SearchRequest {
  query: string;
  project?: string;
  entry_type?: EntryType;
  top_k?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  raw_text: string;
  author: string;
  project: string;
  entry_type: EntryType;
  tags: string[];
  score: number;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  project?: string;
  history?: ChatMessage[];
}

export interface ChatResponse {
  answer: string;
  sources: SearchResult[];
}
```

---

## Zustand Stores

```typescript
// ui.store.ts
interface UIState {
  activeEntryId: string | null;
  isDirty: boolean;       // unsaved changes
  isSaving: boolean;      // PUT in progress
  isIndexing: boolean;    // POST /index in progress
  isChatOpen: boolean;
  isSidebarOpen: boolean;
  activeProject: string | null;
}

// entries.store.ts
interface EntriesState {
  entries: Entry[];
  isLoading: boolean;
  setEntries / setLoading / upsertEntry / removeEntry
}

// chat.store.ts
interface ChatState {
  messages: Record<string, ChatMessage[]>; // keyed by project
  isWaiting: boolean;
}
```

---

## Frontend Conventions

- **Styling**: TailwindCSS v4 utility classes only — no inline styles, no CSS modules
- **Palette**: bg `#FAFAFA`, text `#1A1A1A`, border `#E5E5E5`, muted `#6B7280`, accent `#0F172A`
- **Components**: Use shadcn/ui primitives where available (`Button`, `Dialog`, `Input`, `Badge`, `ScrollArea`, `Drawer`, `Separator`, `Tooltip`, `Select`)
- **State**: Zustand stores in `src/store/`. Keep component state local unless shared
- **API calls**: Always through `src/api/` wrappers — never call `fetch` directly in components
- **Editor**: TipTap v2 with `@tiptap/react`. Extensions installed: `StarterKit`, `Placeholder`, `Typography`, `Link`, `TaskList`, `TaskItem`, `Highlight`, `CodeBlockLowlight` + `lowlight`
- **No class components** — functional components + hooks only
- **File naming**: PascalCase for components, camelCase for hooks/utils/store
- **Icons**: `lucide-react` only

## Backend Conventions

- **Async**: All service functions are `async def` — always `await`
- **Save vs Index**: `PUT /entries/{id}` = persist only (no LLM). `POST /entries/{id}/index` = classifier + embedding (LLM). Never call embedding from `create_entry()` or `update_entry()`
- **Models**: Pydantic v2. `EntryDocument` = MongoDB model (includes `embedding`). `EntryResponse` = API response (no embedding exposed)
- **Errors**: Raise `HTTPException` in routers. Services return `None` for not-found

---

## Key UX Patterns

- **Autosave**: debounce 1.5s after last keystroke → `PUT /entries/:id` (no LLM, fast)
- **Index**: triggered on editor blur or manual button → `POST /entries/:id/index` (slow, LLM)
- **Vector status indicator**: `pending/outdated` → amber warning, `indexed` → green checkmark (disappears after 3s)
- **Search**: semantic via `POST /search`, debounce 300ms — not text filter
- **Chat**: scoped to `activeProject`; only indexed entries participate in RAG
