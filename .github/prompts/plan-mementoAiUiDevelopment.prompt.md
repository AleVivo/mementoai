# MementoAI — Piano di Sviluppo UI

**Decisioni:** Backend first → UI. Sempre backend reale. Tauri sidecar escluso (backend avviato separatamente).

---

## Fase 1 — Backend: Modifiche per separazione Save/Index

### 1.1 `app/models/entry.py`
- Aggiungi enum `VectorStatus` con valori `pending | indexed | outdated`
- Aggiungi campo `vector_status: VectorStatus` a `EntryDocument` (default `"pending"`)
- Aggiungi campo `vector_status: VectorStatus` a `EntryResponse`
- Rimuovi `summary: str` obbligatorio da `EntryResponse` (ora prodotto dall'index) — o mantieni con default `""`

### 1.2 `app/mappers/entry_mapper.py`
- `doc_to_response()`: aggiungi `vector_status=doc.vector_status`

### 1.3 `app/services/entry_service.py`
- `create_entry()`: rimuovi chiamate a `classifier.enrich_entry()` e `embedding.generate_embedding()`. Crea con `summary=""`, `tags=[]`, `embedding=[]`, `vector_status="pending"`
- `update_entry()`: rimuovi generazione embedding. Aggiungi `vector_status="outdated"` nei fields aggiornati
- Nuova funzione `index_entry(entry_id: str)`: legge entry, chiama `classifier.enrich_entry()` + `embedding.generate_embedding()`, aggiorna MongoDB con `summary`, `tags`, `embedding`, `vector_status="indexed"`, ritorna `EntryResponse`

### 1.4 `app/routers/entries.py`
- Aggiungi `POST /{entry_id}/index` → chiama `entry_service.index_entry()`, HTTP 404 se non trovata

### 1.5 `app/db/mongo.py`
- Nessuna modifica: `update_entry()` usa `$set` generico, funziona già

**Verifica Fase 1:** `uvicorn app.main:app --reload` → test con curl/httpx:
- `POST /entries` deve essere fast (no LLM)
- `PUT /entries/:id` deve essere fast (no LLM), `vector_status` diventa `outdated`
- `POST /entries/:id/index` deve triggerare LLM e restituire `vector_status: indexed`

---

## Fase 2 — Frontend: Scaffold Tauri + React

### 2.1 Init progetto
- `npm create tauri-app@latest ui -- --template react-ts` nella root del repo
- Configura Vite: porta `1420`, `clearScreen: false`
- Installa dipendenze: `tailwindcss@4`, `shadcn/ui`, `zustand`, `lucide-react`
- Installa TipTap: `@tiptap/react`, `@tiptap/starter-kit`, `@tiptap/extension-placeholder`, `@tiptap/extension-typography`, `@tiptap/extension-link`, `@tiptap/extension-task-list`, `@tiptap/extension-task-item`, `@tiptap/extension-highlight`, `@tiptap/extension-code-block-lowlight`
- Configura `tailwind.config.ts` con palette Notion (bg `#FAFAFA`, text `#1A1A1A`, border `#E5E5E5`)
- `tauri.conf.json`: window min `1024x600`, default `1280x800`, `csp: connect-src http://localhost:8000`
- Aggiungi shadcn: `npx shadcn@latest init` + add Button, Input, Badge, Dialog, Drawer, ScrollArea, Separator, Tooltip, Select

**Verifica:** `npm run tauri dev` → finestra vuota senza errori

---

## Fase 3 — Frontend: Foundation (tipi, API, store)

### 3.1 `src/types/index.ts`
- Tipi come da frontend-spec.md: `EntryType`, `VectorStatus`, `Entry`, `EntryCreate`, `EntryUpdate`, `SearchRequest`, `SearchResult` (con `raw_text`, `author`, `tags`, `score`), `ChatRequest`

### 3.2 `src/api/client.ts`
- `apiGet`, `apiPost`, `apiPut` come da spec

### 3.3 `src/api/entries.ts`
- `getEntries(params)`, `getEntryById(id)`, `createEntry(body)`, `updateEntry(id, body)`, `deleteEntry(id)`, `indexEntry(id)`

### 3.4 `src/api/search.ts`
- `searchEntries(body: SearchRequest)`

### 3.5 `src/api/chat.ts`
- `sendChat(body: ChatRequest)`

### 3.6 `src/store/ui.store.ts`
- `activeEntryId`, `isDirty`, `isSaving`, `isIndexing`, `isChatOpen`, `isSidebarOpen`, `activeProject` + setters

### 3.7 `src/store/entries.store.ts`
- `entries: Entry[]`, `isLoading`, `error` + `setEntries`, `upsertEntry`, `removeEntry`

### 3.8 `src/store/chat.store.ts`
- `messages: Record<project, ChatMessage[]>`, `isWaiting` + `addMessage`, `setWaiting`

### 3.9 `src/lib/utils.ts`
- `cn()` helper (clsx + tailwind-merge), `formatDate()`, `formatWeek()`

**Verifica:** `tsc --noEmit` senza errori

---

## Fase 4 — Frontend: Layout shell

### 4.1 `src/App.tsx`
- Layout a tre colonne: `<Sidebar>` (240px fisso) | `<MainPanel>` (flex-1) | `<ChatDrawer>` (overlay)
- Keyboard shortcuts globali via `useEffect`: Ctrl+K, Ctrl+J, Ctrl+N, Ctrl+S

### 4.2 `src/components/layout/Sidebar.tsx`
- Header "MementoAI", lista progetti raggruppata, `[+ New]` in fondo
- Usa `ScrollArea` shadcn per la lista entries

### 4.3 `src/components/layout/MainPanel.tsx`
- Mostra `EntryEditor` se `activeEntryId` != null, altrimenti placeholder "Select or create an entry"

### 4.4 `src/components/layout/ChatPanel.tsx`
- Wrapper del drawer, legge `isChatOpen` dallo store

**Verifica:** Layout visivo in browser senza dati reali

---

## Fase 5 — Frontend: Entry list e navigazione

### 5.1 `src/hooks/useEntries.ts`
- Fetch `GET /entries?project=...` all'init e al cambio progetto, popola `entries.store`
- Espone `refetch()`

### 5.2 `src/components/entries/EntryTypeBadge.tsx`
- Badge colorato: ADR → blue, Postmortem → amber, Update → green

### 5.3 `src/components/entries/EntryListItem.tsx`
- Titolo, `EntryTypeBadge`, data. Highlight se entry attiva.

### 5.4 `src/components/entries/EntryList.tsx`
- Lista `EntryListItem` per progetto attivo. Al click → `setActiveEntry(id)`

**Verifica:** Sidebar mostra entries dal backend reale, click apre entry nel panel

---

## Fase 6 — Frontend: Editor (core della app)

### 6.1 `src/components/editor/EntryMeta.tsx`
- Campi: titolo (input), tipo (Select shadcn), progetto (text), autore (text), tags (badge list + input)
- onChange → `setDirty(true)`

### 6.2 `src/components/editor/EditorToolbar.tsx`
- Bottoni bold/italic/h1/h2/list/code + indicatori stato:
  - `●` se dirty | `Saving...` se isSaving | `✓ Saved`
  - `⚠ Not indexed` se `vector_status != "indexed"` | `⟳ Indexing...` se isIndexing | `✓ Indexed` (3s poi scompare)
  - Bottone `[⟳ Index]` manuale

### 6.3 `src/components/editor/EntryEditor.tsx`
- `useEditor` TipTap con tutte le estensioni da spec
- `onUpdate`: debounce 1.5s → `PUT /entries/:id` → `upsertEntry` nello store
- `onBlur`: se `vector_status != "indexed"` → `POST /entries/:id/index`
- Salvataggio draft in `localStorage` (chiave `draft-{id}`)
- Ctrl+S: save immediato

**Verifica:** Apertura entry, scrittura, autosave, indexing automatico on blur

---

## Fase 7 — Frontend: New Entry

### 7.1 `src/components/entries/NewEntryDialog.tsx`
- Dialog shadcn: campi title, type (Select), project (input o select da progetti esistenti), author
- Submit → `POST /entries` → `upsertEntry` store → `setActiveEntry(newId)`

**Verifica:** Flusso completo creazione entry

---

## Fase 8 — Frontend: Search

### 8.1 `src/hooks/useSearch.ts`
- Stato `query`, `results`, `isSearching`. Debounce 300ms → `POST /search`

### 8.2 `src/components/search/SearchBar.tsx`
- Input controllato, mostra spinner durante ricerca. Ctrl+K focus automatico.

### 8.3 `src/components/search/SearchResults.tsx`
- Lista risultati con score, tipo, summary. Click → `setActiveEntry(id)`

**Verifica:** Search semantica funzionante con risultati cliccabili

---

## Fase 9 — Frontend: Chat

### 9.1 `src/hooks/useChat.ts`
- `send(question)` → `POST /chat` → aggiunge messaggi user + AI nello store

### 9.2 `src/components/chat/ChatMessage.tsx`
- Bubble per user (destra) e AI (sinistra). Markdown rendering per risposte AI (usa `marked` o `react-markdown`).

### 9.3 `src/components/chat/ChatHistory.tsx`
- `ScrollArea` con auto-scroll in fondo a ogni nuovo messaggio

### 9.4 `src/components/chat/ChatInput.tsx`
- Textarea + bottone Send. Enter invia, Shift+Enter va a capo. Disabilitato durante `isWaiting`.

### 9.5 `src/components/chat/ChatDrawer.tsx`
- Drawer shadcn dal lato destro. Header "Chat — {activeProject}". Contiene `ChatHistory` + `ChatInput`.

**Verifica:** Domanda → risposta RAG dal backend locale

---

## Aggiornamenti doc (paralleli a Fase 1)

- `docs/copilot-instructions.md`: aggiornare tabella API con endpoint index, aggiornare tipi TS con `VectorStatus` e `vector_status`, aggiornare `SearchResult` con campi mancanti (`raw_text`, `author`, `tags`)

---

## File modificati/creati — Riepilogo

**Backend (modifiche):**
- `app/models/entry.py`
- `app/mappers/entry_mapper.py`
- `app/services/entry_service.py`
- `app/routers/entries.py`

**Frontend (nuovo):**
- `ui/` — intero albero da scaffold

**Docs (aggiornamenti):**
- `docs/copilot-instructions.md`
