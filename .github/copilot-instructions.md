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
│   ├── models/                 ← Pydantic models (entry.py, chat.py, search.py, agent.py, chunk.py)
│   ├── routers/                ← FastAPI routers (entries, search, chat, agent)
│   ├── services/               ← Business logic (entry_service, chat_service, rag, embedding, chunker, agent, agent_registry, agent_tools, ollama)
│   └── mappers/                ← MongoDB doc ↔ Pydantic model conversion
├── ui/                         ← Tauri v2 + React 19 frontend
│   └── src/
│       ├── App.tsx             ← Root layout: Sidebar + MainPanel + ChatDrawer
│       ├── api/                ← Fetch wrappers (client.ts, entries.ts, search.ts, chat.ts)
│       ├── components/
│       │   ├── layout/         ← Sidebar.tsx, MainPanel.tsx, ThemeToggle.tsx
│       │   ├── editor/         ← EntryEditor.tsx, EditorToolbar.tsx, EntryMeta.tsx
│       │   ├── entries/        ← EntryList.tsx, EntryListItem.tsx, EntryTypeBadge.tsx, NewEntryDialog.tsx
│       │   ├── chat/           ← ChatDrawer.tsx, ChatHistory.tsx, ChatInput.tsx, ChatMessage.tsx
│       │   ├── search/         ← SearchBar.tsx, SearchResults.tsx
│       │   ├── loader.tsx      ← MementoLoader SVG animation (shown during streaming)
│       │   └── ui/             ← shadcn/ui components (auto-generated)
│       ├── store/              ← Zustand: ui.store.ts, entries.store.ts, chat.store.ts
│       ├── hooks/              ← useEntries.ts, useSearch.ts, useChat.ts, useKeyboardShortcuts.ts
│       ├── types/index.ts      ← TypeScript types (source of truth for frontend)
│       └── lib/utils.ts        ← cn() helper
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
| `POST` | `/entries/{id}/index` | Vectorize entry | Slow — chunker + embedding (nomic-embed-text). No LLM classifier. |
| `DELETE` | `/entries/{id}` | Delete entry | — |
| `POST` | `/search` | Semantic vector search | `SearchRequest` body |
| `POST` | `/chat` | RAG chat (SSE stream) | `ChatRequest` body — streams `sources`, `token`, `done` events |
| `POST` | `/agent` | ReAct agent (SSE stream) | `AgentRequest` body — streams `reasoning`, `step`, `token`, `done` events |

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
    content: str
    entry_type: EntryType
    title: str
    summary: str
    project: str
    author: str
    tags: list[str]
    created_at: datetime
    week: str               # ISO week e.g. "2026-W10"
    vector_status: VectorStatus

class ChatRequest(BaseModel):
    question: str
    project: Optional[str] = None
    top_k: int = 5

class AgentRequest(BaseModel):
    question: str
    project: Optional[str] = None
    max_steps: int = 5  # range 1-10
```
---

## Frontend TypeScript Types (`ui/src/types/index.ts`)

> Frontend and backend field names are aligned — no mapping needed in the API layer.

```typescript
export type EntryType = "adr" | "postmortem" | "update" | "other";
export type VectorStatus = "pending" | "indexed" | "outdated";

export interface Entry {
  id: string;
  title: string;
  content: string;
  entry_type: EntryType;
  author: string;
  project: string;
  tags: string[];
  summary: string;
  vector_status: VectorStatus;
  created_at: string;
  week: string;             // ISO week e.g. "2026-W10"
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
  top_k?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  summary: string;
  author: string;
  project: string;
  entry_type: EntryType;
  tags: string[];
  score: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  reasoning?: string;       // agent reasoning (collapsible)
  steps?: AgentStep[];      // agent tool calls (collapsible)
  sources?: ChatSource[];   // present on assistant messages after sources event
  isStreaming: boolean;
}

export interface ChatRequest {
  question: string;         // ← field name used by backend
  project?: string;
}

export interface ChatSource {
  entry_id: string;
  title: string;
  entry_type: EntryType;
  section: string | null;
}

export type SSEEvent =
  | { type: 'sources'; sources: ChatSource[] }
  | { type: 'token';   content: string }
  | { type: 'done' }
  | { type: 'error';   message: string };

export interface AgentRequest {
  question: string;
  project?: string;
}

export interface AgentStep {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
}

export type AgentSSEEvent =
  | { type: 'token';     content: string }
  | { type: 'reasoning'; content: string }
  | { type: 'step';      tool: string; args: Record<string, unknown>; result: unknown }
  | { type: 'done';      steps: AgentStep[]; model: string }
  | { type: 'error';     message: string };
```

---

## Zustand Stores

```typescript
// ui.store.ts
interface UIState {
  activeEntryId: string | null;
  isDirty: boolean;         // unsaved changes
  isSaving: boolean;        // PUT in progress
  isIndexing: boolean;      // POST /index in progress
  isChatOpen: boolean;
  isSidebarOpen: boolean;
  activeProject: string | null;
  isNewEntryOpen: boolean;  // new entry dialog open
  chatMode: "rag" | "agent";
}

// entries.store.ts
interface EntriesState {
  entries: Entry[];
  isLoading: boolean;
  setEntries / setLoading / upsertEntry / removeEntry
}

// chat.store.ts  (keyed by project name, "__all__" for global scope)
interface ChatState {
  messages: Record<string, ChatMessage[]>;
  addMessage / appendToken / appendReasoning / addStep / setSources / setStreamingDone / clearMessages
}
// Note: isWaiting is derived in useChat hook, not stored in the Zustand store
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
- **Models**: Pydantic v2. `EntryDocument` = MongoDB internal model (`content`, `entry_type`, includes `embedding`). `EntryResponse` / `EntryCreate` / `EntryUpdate` = API-facing DTOs (`content`, `entry_type`). The mapper translates between the two. Never expose `EntryDocument` directly.
- **Errors**: Raise `HTTPException` in routers. Services return `None` for not-found

---

## Key UX Patterns

- **Autosave**: debounce 1.5s after last keystroke → `PUT /entries/:id` (no LLM, fast)
- **Index**: triggered on editor blur or manual button → `POST /entries/:id/index` (slow, LLM)
- **Vector status indicator**: `pending/outdated` → amber warning, `indexed` → green checkmark (disappears after 3s)
- **Search**: semantic via `POST /search`, debounce 300ms — not text filter
- **Chat**: scoped to `activeProject`; only indexed entries participate in RAG
