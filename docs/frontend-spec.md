# MementoAI — Frontend Specification

## Technology Stack

| Layer | Technology | Version | Reason |
|---|---|---|---|
| Desktop shell | **Tauri v2** | ^2.0 | Lightweight native wrapper (~10MB binary), uses system WebView |
| Build tool | **Vite** | ^6.0 | Fast HMR, first-class Tauri integration |
| UI framework | **React** | ^19 | Mature ecosystem, best TipTap integration, strong Copilot support |
| Language | **TypeScript** | ^5.5 | Type safety, better DX |
| Styling | **TailwindCSS** | ^4.0 | Utility-first, Notion-like minimal design |
| Component library | **shadcn/ui** | latest | Unstyled accessible components, Tailwind-native |
| Rich text editor | **TipTap** | ^3.x | Block-based editor (Notion-like), React adapter |
| Markdown rendering | **react-markdown** | latest | AI chat response rendering |
| State management | **Zustand** | ^5.0 | Minimal, no boilerplate |
| HTTP client | **fetch** (native) | — | Native browser fetch via Tauri WebView |
| Icons | **Lucide React** | latest | Clean minimal icon set |

## Project Structure (frontend)

```
ui/                          ← Tauri frontend root
├── src/
│   ├── main.tsx             ← React entry point
│   ├── App.tsx              ← Root layout (sidebar + main panel)
│   ├── api/
│   │   ├── client.ts        ← Base fetch wrapper (baseURL = localhost:8000)
│   │   ├── entries.ts       ← /entries API calls
│   │   ├── search.ts        ← /search API calls
│   │   └── chat.ts          ← /chat API calls
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx         ← Left nav: projects + entries list
│   │   │   └── MainPanel.tsx       ← Right area: editor or search results
│   │   ├── editor/
│   │   │   ├── EntryEditor.tsx     ← TipTap-based block editor (autosave 1.5s, index on blur)
│   │   │   ├── EditorToolbar.tsx   ← Formatting toolbar + save/index status indicators
│   │   │   └── EntryMeta.tsx       ← Title, type, author, tags, vector status badge
│   │   ├── entries/
│   │   │   ├── EntryList.tsx       ← Sidebar entries list
│   │   │   ├── EntryListItem.tsx   ← Single entry row in sidebar
│   │   │   ├── EntryTypeBadge.tsx  ← ADR / Postmortem / Update badge
│   │   │   └── NewEntryDialog.tsx  ← shadcn Dialog for creating new entries
│   │   ├── search/
│   │   │   ├── SearchBar.tsx       ← Semantic search input (debounced 300ms, Ctrl+K)
│   │   │   └── SearchResults.tsx   ← Results list with score, type, summary
│   │   ├── chat/
│   │   │   ├── ChatDrawer.tsx      ← vaul Drawer from right, uses isChatOpen from store
│   │   │   ├── ChatInput.tsx       ← Textarea, Enter sends, Shift+Enter newline
│   │   │   ├── ChatMessage.tsx     ← User bubble (right) + AI bubble (left, markdown rendered)
│   │   │   └── ChatHistory.tsx     ← ScrollArea with auto-scroll to bottom
│   │   └── ui/                     ← shadcn/ui components (auto-generated)
│   ├── store/
│   │   ├── entries.store.ts        ← Zustand: entries state + actions
│   │   ├── ui.store.ts             ← Zustand: sidebar open, active entry, chat open, dirty/saving/indexing state
│   │   └── chat.store.ts           ← Zustand: messages per project, isWaiting
│   ├── hooks/
│   │   ├── useEntries.ts           ← Fetch entries on project change, popola store
│   │   ├── useSearch.ts            ← Debounced semantic search (300ms)
│   │   └── useChat.ts              ← send(question) → POST /chat → addMessage to store
│   ├── types/
│   │   └── index.ts                ← TypeScript types mirroring backend models
│   └── lib/
│       └── utils.ts                ← cn() helper, date formatting, etc.
├── src-tauri/                      ← Tauri Rust shell
│   ├── tauri.conf.json
│   └── src/
│       └── main.rs
├── index.html
├── vite.config.ts
├── tailwind.config.ts
└── package.json
```

## TypeScript Types

Mirror the backend Pydantic models exactly:

```typescript
// types/index.ts

export type EntryType = 'adr' | 'postmortem' | 'update' | 'other';

export type VectorStatus = 'pending' | 'indexed' | 'outdated';

export interface Entry {
  id: string;
  content: string;
  entry_type: EntryType;
  title: string;
  summary: string;
  project: string;
  author: string;
  tags: string[];
  created_at: string; // ISO datetime
  week: string;       // e.g. "2026-W10"
  vector_status: VectorStatus;
}

export interface EntryCreate {
  content: string;
  entry_type: EntryType;
  title: string;
  project: string;
  author: string;
  summary?: string;
  tags?: string[];
}

export interface EntryUpdate {
  content?: string;
  entry_type?: EntryType;
  title?: string;
  project?: string;
  author?: string;
  summary?: string;
  tags?: string[];
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
  created_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  question: string;
  project: string;       // obbligatorio — la chat è sempre scoped a un progetto
}

export interface ChatSource {
  ref: number;
  id: string;
  title: string;
  type: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}
```

## Layout Design

```
┌─────────────────────────────────────────────────────────┐
│ ●  MementoAI                                    [Chat ▶] │  ← Titlebar
├────────────┬────────────────────────────────────────────┤
│  Projects  │  [🔍 Search entries...]                    │  ← Search bar
│  ──────── │  ──────────────────────────────────────────│
│  ▼ backend │                                            │
│    ADR-001 │   Title: Service Mesh ADR              ... │  ← Active entry
│    PM-003  │   Project: backend  Type: [ADR]  Author:.. │
│    UP-012  │   Tags: [mesh] [infra] [aws]               │
│  ▶ mobile  │   ────────────────────────────────────     │
│  ▶ data    │                                            │
│            │   [Block editor content here — TipTap]    │
│  ──────── │                                            │
│  [+ New]   │                                            │
│            │                             [Save  Cmd+S] │
└────────────┴────────────────────────────────────────────┘
```

**Chat panel** slides in from the right as a drawer:
```
┌──────────────────────────────┐
│  Chat with backend KB    [✕] │
│  ──────────────────────────  │
│  [AI]: Based on ADR-001...   │
│                              │
│  [You]: What did we decide.. │
│                              │
│  ──────────────────────────  │
│  Ask a question...    [Send] │
└──────────────────────────────┘
```

## API Client

```typescript
// api/client.ts
const BASE_URL = 'http://localhost:8000';

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

## TipTap Editor Configuration

Extensions to enable for Notion-like experience:
- `StarterKit` — headings, bold, italic, lists, code blocks, blockquote, hr
- `Placeholder` — "Write something..."
- `Typography` — smart quotes, dashes
- `Link`
- `CodeBlockLowlight` — syntax highlighted code blocks
- `TaskList` + `TaskItem` — checkbox lists
- `Highlight` — text highlighting

## Key UX Behaviors

### Save (persistenza)
- **Autosave**: debounce 1.5s dopo l'ultimo keystroke → `PUT /entries/:id`
  - Salva solo i dati testuali, **nessuna chiamata LLM**
  - Il backend aggiorna `vector_status = "outdated"`
  - Indicatore: pallino `●` mentre dirty, `Saving...` durante il PUT
- `Cmd/Ctrl+S` forza il save immediato (cancella il debounce)
- Draft locale in `localStorage` come fallback anti-crash (chiave: `draft-{entryId}`)
- Se si naviga su un'altra entry con `isDirty = true` → dialog "Unsaved changes — Save or Discard?"

### Index (vettorializzazione)
- **Trigger automatico**: `onBlur` dell'editor → `POST /entries/:id/index`
  - Il backend esegue: classifier → summary + tags, embedding → vettore, `vector_status = "indexed"`
- **Trigger manuale**: pulsante `[⟳ Index]` nella toolbar dell'editor
- Indicatori visivi indipendenti dal save:

| Stato `vector_status` | Indicatore |
|---|---|
| `pending` | `⚠ Not indexed` (amber) |
| `outdated` | `⚠ Not indexed` (amber) |
| `indexed`, indexing in corso | `⟳ Indexing...` (spinner amber) |
| `indexed` | `✓ Indexed` (verde, scompare dopo 3s) |

### Zustand UI Store
```typescript
interface UIStore {
  activeEntryId: string | null;
  isDirty: boolean;      // modifiche non ancora salvate su DB
  isSaving: boolean;     // PUT /entries/:id in corso
  isIndexing: boolean;   // POST /entries/:id/index in corso
  isChatOpen: boolean;
  isSidebarOpen: boolean;
  activeProject: string | null;
}
```

### Layout toolbar editor
```
┌────────────────────────────────────────────────────────────┐
│  Service Mesh ADR   ●                                      │
│                              ⚠ Not indexed   [⟳ Index]   │
│                                               [Save Cmd+S] │
└────────────────────────────────────────────────────────────┘
```

### New entry
Fill metadata modal (title, type, project, author) → `POST /entries` → open in editor.
Il backend crea con `vector_status = "pending"`, l'entry è subito modificabile.

### Search
Debounce 300ms su input → `POST /search` → display results. Le entry `outdated`/`pending`
compaiono nei risultati con l'ultimo vettore disponibile (escluse se `pending`).

### Chat
Scoped al progetto attivo; `top_k = 5` default. Le entry non indicizzate non partecipano al RAG.

### Keyboard shortcuts
- `Cmd/Ctrl+S` → save immediato
- `Cmd/Ctrl+K` → open search
- `Cmd/Ctrl+J` → toggle chat panel
- `Cmd/Ctrl+N` → new entry

## Tauri Configuration Notes

- `allowlist.http` must be enabled to allow `fetch` to `localhost:8000`
- Window size: min `1024x600`, default `1280x800`
- Decorations: enabled (native titlebar)
- The FastAPI backend is run as a **sidecar** (Tauri spawns it on startup) or started separately during development
- `csp` must allow `connect-src http://localhost:8000`
