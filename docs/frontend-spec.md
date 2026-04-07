---
generated_by: GitHub Copilot (Claude Sonnet 4.6)
last_updated: 2026-04-07
---

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
| Drag and drop | **@dnd-kit/core** | latest | Drag-and-drop accessibile per entry/cartelle nella sidebar |
| HTTP client | **fetch** (native) | — | Native browser fetch via Tauri WebView |
| Icons | **Lucide React** | latest | Clean minimal icon set |

Il sistema visuale usa token semantici centralizzati in `App.css` (entry type colors, status colors, destructive hover) con varianti light/dark. Vedi `docs/theming.md`.

## Project Structure (frontend)

```
ui/                          ← Tauri frontend root
├── src/
│   ├── main.tsx             ← React entry point
│   ├── App.tsx              ← Root layout (sidebar + main panel) + auth gate
│   ├── api/
│   │   ├── client.ts        ← Base fetch wrapper (baseURL = localhost:8000, JWT inject, refresh silenzioso)
│   │   ├── entries.ts       ← /entries API calls
│   │   ├── folders.ts       ← /projects/{project_id}/folders API calls
│   │   ├── projects.ts      ← /projects API calls (CRUD + member management)
│   │   ├── users.ts         ← /users/search API call (lookup per email)
│   │   ├── search.ts        ← /search API calls
│   │   ├── chat.ts          ← /chat e /agent API calls
│   │   └── admin.ts         ← /admin/config API calls (getAllConfig, getConfigSection, updateConfigSection)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx         ← Left nav: projects + entries list + admin button (admin only)
│   │   │   └── MainPanel.tsx       ← Right area: editor or search results
│   │   ├── admin/
│   │   │   ├── AdminConsole.tsx    ← Pagina scrollabile che sostituisce MainPanel quando isAdminConsoleOpen
│   │   │   ├── AdminSection.tsx    ← Card per singola sezione config (form + save button)
│   │   │   └── AdminField.tsx      ← Field dinamico (text, secret, select, toggle)
│   │   ├── editor/
│   │   │   ├── EntryEditor.tsx     ← TipTap editor (autosave 1.5s; espone onEditorMount)
│   │   │   ├── EditorToolbar.tsx   ← Toolbar full-width fuori dallo scroll + StatusChip + pulsante indicizza/reindicizza/riprova
│   │   │   └── EntryMeta.tsx       ← Meta compatte (title/type/author/project) + tags/summary espandibili + stato salvataggio
│   │   ├── entries/
│   │   │   ├── EntryList.tsx       ← Sidebar entries list
│   │   │   ├── EntryListItem.tsx   ← Riga compatta con type dot colorato + context menu move
│   │   │   ├── EntryTypeBadge.tsx  ← ADR / Postmortem / Update badge
│   │   │   └── NewEntryDialog.tsx  ← Dialog nuova entry con folder selector pre-selezionato da activeFolder
│   │   ├── folders/
│   │   │   ├── FolderTree.tsx      ← Albero cartelle + root drop zone + creazione cartella root
│   │   │   ├── FolderNode.tsx      ← Nodo ricorsivo, expand/collapse, drag/drop, context menu
│   │   │   ├── FolderPicker.tsx    ← Dialog "move to" con esclusione discendenti
│   │   │   └── ContextMenu.tsx     ← Menu contestuale custom (rename/move/new subfolder/delete)
│   │   ├── projects/
│   │   │   ├── NewProjectDialog.tsx     ← Crea nuovo progetto (controlled)
│   │   │   └── ProjectSettingsDialog.tsx ← Rinomina, descrizione, gestione membri
│   │   ├── search/
│   │   │   ├── SearchBar.tsx       ← Semantic search input (debounced 300ms, Ctrl+K)
│   │   │   └── SearchResults.tsx   ← Results list with score, type, summary
│   │   ├── chat/
│   │   │   ├── ChatDrawer.tsx      ← vaul Drawer from right; header con select RAG/Agent; titolo mostra progetto attivo o "Tutto"
│   │   │   ├── ChatInput.tsx       ← Textarea, Enter sends, Shift+Enter newline
│   │   │   ├── ChatMessage.tsx     ← User bubble (right) + AI bubble (left, markdown rendered)
│   │   │   └── ChatHistory.tsx     ← ScrollArea with auto-scroll to bottom
│   │   └── ui/                     ← shadcn/ui components (auto-generated)
│   ├── store/
│   │   ├── folders.store.ts        ← Zustand: folder tree + isLoading + error
│   │   ├── entries.store.ts        ← Zustand: entries + isLoading + error (string|null); setError propagato da useEntries su fetch fallito
│   │   ├── projects.store.ts       ← Zustand: lista progetti + isLoading + error (string|null); setError propagato da useProjects su fetch fallito
│   │   ├── ui.store.ts             ← Zustand: sidebar/chat/admin, active project/entry/folder, dirty/saving/indexing state
│   │   ├── auth.store.ts           ← Zustand: token, refreshToken, user; persistiti in localStorage
│   │   └── chat.store.ts           ← Zustand: messages per projectId (chiave "__all__" per scope globale); actions: addPendingStep (tool_start) / addStep (sostituisce pending con risultato)
│   ├── hooks/
│   │   ├── useEntries.ts           ← Fetch entries on project change, popola store; propaga errori a entries.store.error; espone refetch() come funzione di retry
│   │   ├── useFolders.ts           ← Fetch tree cartelle sul progetto attivo + create/rename/move/delete con refetch
│   │   ├── useProjects.ts          ← Fetch progetti dell'utente, popola store; propaga errori a projects.store.error; espone refetch() come funzione di retry
│   │   ├── useSearch.ts            ← Debounced semantic search (300ms)
│   │   ├── useChat.ts              ← send(question) → POST /chat o POST /agent in base a chatMode
│   │   └── useKeyboardShortcuts.ts ← Registra Ctrl+N/K/J a livello window
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

export type VectorStatus = 'pending' | 'indexed' | 'outdated' | 'error';

export interface Entry {
  id: string;
  title: string;
  content: string;
  entry_type: EntryType;
  author: string;       // nome display (read-only, copiato al momento della creazione)
  authorId: string;     // ObjectId dell'utente autore
  projectId: string;    // ObjectId del progetto
  tags: string[];
  summary: string;
  vector_status: VectorStatus;
  created_at: string;   // ISO datetime
  week: string;         // e.g. "2026-W10"
  folder_id: string | null;
}

export interface EntryCreate {
  title: string;
  content: string;
  entry_type: EntryType;
  project_id: string;   // ObjectId del progetto
  folder_id?: string | null;
  summary?: string;
  tags?: string[];
}

export interface EntryUpdate {
  title?: string;
  content?: string;
  entry_type?: EntryType;
  summary?: string;
  tags?: string[];
  folder_id?: string | null;
}

export interface FolderResponse {
  id: string;
  name: string;
  parent_id: string | null;
  path: string;
  created_at: string;
}

export interface FolderTree extends FolderResponse {
  children: FolderTree[];
}

export interface FolderCreate {
  name: string;
  parent_id?: string | null;
}

export interface FolderUpdate {
  name: string;
}

export interface FolderMove {
  new_parent_id: string | null;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  ownerId: string;
  createdAt: string;
  currentUserRole: string; // 'owner' | 'member'
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectMember {
  userId: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  addedAt: string;
}

export interface SearchRequest {
  query: string;
  project_id?: string;  // ObjectId del progetto (opzionale)
  top_k?: number;
}

export interface SearchResult {
  entry_id: string;
  entry_type: EntryType;
  entry_title: string;
  project_id: string;
  heading: string | null;
  text: string;
  score: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  reasoning?: string;       // agent reasoning (collapsible)
  steps?: AgentStep[];      // agent tool calls (collapsible)
  sources?: ChatSource[];   // present on assistant messages after sources event
  isStreaming: boolean;
}

export interface ChatRequest {
  question: string;
  project_id?: string;   // ObjectId del progetto (omesso = scope globale)
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
  project_id?: string;   // ObjectId del progetto (omesso = scope globale)
  conversation_id?: string;
}

export interface AgentStep {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
  pending?: boolean;  // true mentre il tool è in esecuzione (rimosso al completamento)
}

export type AgentSSEEvent =
  | { type: 'session';    conversation_id: string }   // primo evento — ID conversazione (nuovo o esistente)
  | { type: 'token';      content: string }
  | { type: 'reasoning';  content: string }            // solo su modelli con thinking nativo
  | { type: 'tool_start'; tool: string }               // emesso non appena il modello decide di usare un tool
  | { type: 'step';       tool: string; args: Record<string, unknown>; result: unknown }  // dopo esecuzione
  | { type: 'done';       steps: AgentStep[]; model: string }
  | { type: 'error';      message: string };

// #### AUTH TYPES ####

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  company: string;
  role: 'user' | 'admin';  // ruolo a livello di sistema
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// #### ADMIN TYPES ####

export type FieldType = 'text' | 'secret' | 'select' | 'toggle';
export type SectionType = 'integration' | 'settings';
export type ConfigStatus = 'unknown' | 'active' | 'error';

export interface SelectOption {
  value: string;
  label: string;
}

export interface DependsOn {
  field: string;
  options: Record<string, SelectOption[]>;
}

export interface RequiredIf {
  field: string;
  in?: string[];
  not_in?: string[];
}

export interface SchemaField {
  key: string;
  label: string;
  type: FieldType;
  required?: boolean;
  required_if?: RequiredIf;
  placeholder?: string;
  options?: SelectOption[];
  depends_on?: DependsOn;
  value: string | boolean | null;
}

export interface ConfigSection {
  id: string;
  type: SectionType;
  label: string;
  description?: string;
  fields: SchemaField[];
  status?: ConfigStatus;
  status_message?: string;
  last_tested_at?: string;
  updated_at?: string;
  updated_by?: string;
}

export interface ConfigUpdateRequest {
  values: Record<string, string | boolean | null>;
}
```

## Layout Design

```
┌──────────────────────────────────────────────────────────┐
│ ●  MementoAI                                    [Chat ▶] │  ← Titlebar
├────────────┬─────────────────────────────────────────────┤
│  Projects  │  [🔍 Search entries...]                     │  ← Search bar
│  ────────  │  ───────────────────────────────────────────│
│  ▼ backend │                                             │
│    ADR-001 │   Title: Service Mesh ADR               ... │  ← Active entry
│    PM-003  │   Project: backend  Type: [ADR]   Author:.. │
│    UP-012  │   Tags: [mesh] [infra] [aws]                │
│  ▶ mobile  │   ────────────────────────────────────      │
│  ▶ data    │                                             │
│            │   [Block editor content here — TipTap]      │
│  ────────  │                                             │
│  [+ New]   │                                             │
│            │                             [Save  Cmd+S]   │
└────────────┴─────────────────────────────────────────────┘
```

**Admin console** sostituisce MainPanel quando `isAdminConsoleOpen = true`:
```
┌────────────┬────────────────────────────────────────────┐
│  Projects  │  ⚙ Admin Console                           │
│  ────────  │  ──────────────────────────────────────────│
│  ...       │                                            │
│            │  ┌──────────────────────────────────────┐  │
│            │  │ LLM Provider              [● Attivo] │  │
│            │  │ Configurazione modello...            │  │
│            │  │ Provider  [Ollama ▾]                 │  │
│            │  │ Host      [http://localhost:11434]   │  │
│            │  │ Modello   [Qwen 2.5 7B ▾]            │  │
│            │  │                           [ Salva ]  │  │
│            │  └──────────────────────────────────────┘  │
│            │  ┌─────────────────────────────────────┐   │
│            │  │ Embedding Provider                  │   │
│            │  │ ...                                 │   │
│            │  └─────────────────────────────────────┘   │
│  ────────  │                                            │
│  [⚙️ Admin]│                                            │
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
- **Trigger esclusivamente manuale**: pulsante `[Indicizza]` nella toolbar dell'editor → `POST /entries/:id/index`
  - Il backend esegue: chunking HTML → embedding chunk → salvataggio in collection `chunks`, `vector_status = "indexed"`
  - Summary e tag **non** vengono generati automaticamente — sono inseriti manualmente dall'utente
- L'indicizzazione **non scatta al blur** dell'editor

| Stato `vector_status` | Indicatore |
|---|---|
| `pending` | `Da indicizzare` (muted) |
| `outdated` | `Modificata` (warning) |
| `error` | `Errore` (error) + CTA `Riprova` |
| indexing in corso | `Indicizzazione...` (spinner, pulsante disabilitato) |
| `indexed` | `Indicizzata` (success) |

### Admin Console
- Accessibile solo agli utenti con `role: "admin"` — il pulsante `ShieldCheck` nel footer della sidebar non viene renderizzato per gli altri utenti
- `isAdminConsoleOpen` nello store UI — quando `true` sostituisce `MainPanel` con `AdminConsole`
- Selezionare una entry dalla sidebar chiude automaticamente la console (`setActiveEntryId` resetta `isAdminConsoleOpen`)
- Le sezioni sono renderizzate dinamicamente dal backend (`GET /admin/config`) — aggiungere una nuova sezione su MongoDB non richiede modifiche al frontend
- Ogni sezione è una card indipendente con il proprio stato locale — il salvataggio avviene per sezione, non globalmente
- I campi `secret` mostrano `***` se già impostati, `null` se mai configurati — il valore reale non viene mai esposto
- Cambiare il valore di un campo resetta automaticamente tutti i campi che dipendono da esso (`depends_on` e `required_if`) — logica generica, non specifica per provider
- Il bottone Salva è disabilitato se ci sono campi obbligatori vuoti (validazione `required` e `required_if`)
- Il badge di stato (`unknown` / `active` / `error`) viene aggiornato dopo ogni salvataggio dalla response del backend

### Zustand UI Store
```typescript
interface UIStore {
  activeEntryId: string | null;
  activeProjectId: string | null;  // ObjectId del progetto selezionato
  activeFolderId: string | null;   // cartella selezionata nella sidebar
  isDirty: boolean;      // modifiche non ancora salvate su DB
  isSaving: boolean;     // PUT /entries/:id in corso
  isIndexing: boolean;   // POST /entries/:id/index in corso
  isChatOpen: boolean;
  isSidebarOpen: boolean;
  isNewEntryOpen: boolean;   // new entry dialog open
  isAdminConsoleOpen: boolean; // admin console aperta — sostituisce MainPanel
  chatMode: 'rag' | 'agent';
}
```

### Layout toolbar editor
```
┌────────────────────────────────────────────────────────────┐
│ [B][I][H1][H2][List] ...      [Modificata] [Reindicizza] │
└────────────────────────────────────────────────────────────┘
```

La toolbar è renderizzata da `MainPanel` sopra l'area scrollabile dell'editor (non dentro `EntryEditor`) per rimanere sempre visibile durante lo scroll.

### Folder management (sidebar)
- Albero cartelle sopra la lista entry root (`folder_id = null`)
- Empty state contestuale:
  - nessun progetto: CTA `Nuovo progetto`
  - progetti presenti ma nessun progetto attivo: hint direzionale `Seleziona un progetto`
- Drag-and-drop:
  - entry → cartella o root drop zone (update `folder_id`)
  - cartella → cartella/root, con blocco drop su discendenti
- Context menu su cartelle e entry: move, rename, new subfolder, delete
- Delete cartella disabilitato se contiene subfolder o entry

### New entry
Fill metadata modal (title, type — il progetto è automaticamente quello selezionato nella sidebar, l'autore viene ricavato dall'utente autenticato) → `POST /entries` → open in editor.
Il backend crea con `vector_status = "pending"`, l'entry è subito modificabile.
Il campo cartella è preselezionato dalla cartella attiva (`activeFolderId`), con fallback su radice progetto.

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