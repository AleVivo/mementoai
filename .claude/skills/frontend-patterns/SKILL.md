---
name: frontend-patterns
description: Pattern React/Zustand per file in ui/src/ — store, API client, autosave, vector_status, keyboard shortcuts
type: project
---

# Frontend Patterns — MementoAI

Si attiva automaticamente quando lavori su file in `ui/src/`.

## 5 store Zustand

| Store | File | Responsabilità |
|---|---|---|
| `auth` | @ui/src/store/auth.store.ts | access token, refresh token, user corrente, stato login |
| `projects` | @ui/src/store/projects.store.ts | lista progetti, progetto selezionato |
| `entries` | @ui/src/store/entries.store.ts | lista entry, entry corrente, vector_status locale |
| `ui` | @ui/src/store/ui.store.ts | panels aperti, modali, tema, stato sidebar |
| `chat` | @ui/src/store/chat.store.ts | history messaggi, stato streaming, modalità (rag/agent) |

File canonico per pattern store: @ui/src/store/entries.store.ts

## API client — auth injection + silent refresh

Tutti i moduli API usano `apiClient` da @ui/src/api/client.ts, mai `fetch` direttamente.

Il client:
- Inietta automaticamente `Authorization: Bearer <token>` da `auth.store`
- Su risposta 401 → esegue silent refresh via `POST /auth/refresh`
- Se il refresh fallisce → logout e redirect a login
- Ritorna il JSON parsato o lancia un errore tipizzato

```typescript
// CORRETTO — usa il client centralizzato
import { apiClient } from './client'
const entry = await apiClient.get<EntryResponse>(`/entries/${id}`)

// SBAGLIATO — mai fetch diretto in api/
const res = await fetch(`/entries/${id}`)
```

## Autosave vs Indexing — distinzione critica

```
Autosave (debounce 1.5s)  →  PUT /entries/:id      ← puro DB write, NO LLM
Bottone "Indicizza"        →  POST /entries/:id/index ← avvia pipeline AI
```

**Dopo ogni autosave**: aggiornare `vector_status = "outdated"` nello store locale.
**Non chiamare mai `/index` nell'autosave** — è costoso e sbaglia il lifecycle.

```typescript
// Nel hook useEntries o store — dopo save riuscito:
set(state => ({
  entries: state.entries.map(e =>
    e.id === id ? { ...e, vector_status: 'outdated' } : e
  )
}))
```

## Keyboard shortcuts

Registrati in @ui/src/hooks/useKeyboardShortcuts.ts:

| Shortcut | Azione |
|---|---|
| `Cmd/Ctrl+S` | Salva entry corrente (forza save immediato, bypassa debounce) |
| `Cmd/Ctrl+K` | Apri ricerca |
| `Cmd/Ctrl+J` | Entry precedente nella lista |
| `Cmd/Ctrl+N` | Nuova entry |

Se aggiungi shortcuts, registrali in `useKeyboardShortcuts.ts` e documentali qui.

## TypeScript types

Tutti i tipi sono in @ui/src/types/index.ts — rispecchiano i modelli Pydantic del backend.
Non definire tipi locali nei componenti se esiste già il tipo globale.

## Struttura componenti

```
ui/src/components/<domain>/<ComponentName>.tsx
```

Domini esistenti: `admin/`, `auth/`, `chat/`, `editor/`, `entries/`, `layout/`, `projects/`, `search/`, `ui/`

File canonico per componente complesso: @ui/src/components/editor/EntryEditor.tsx
