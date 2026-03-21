---
generated_by: GitHub Copilot (Claude Sonnet 4.6)
last_updated: 2026-03-21
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
│  │  ┌─────────────┬────────────────────┐    │   │
│  │  │  Sidebar    │  Main Panel        │    │   │
│  │  │  - Projects │  ┌──────────────┐  │    │   │
│  │  │  - Entries  │  │ TipTap Block │  │    │   │
│  │  │  - Search   │  │ Editor       │  │    │   │
│  │  │             │  └──────────────┘  │    │   │
│  │  │             │  ┌──────────────┐  │    │   │
│  │  │             │  │ RAG Chat     │  │    │   │
│  │  │             │  │ Panel        │  │    │   │
│  │  │             │  └──────────────┘  │    │   │
│  │  └─────────────┴────────────────────┘    │   │
│  └──────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────┘
                   │ HTTP localhost:8000
┌──────────────────▼────────────────────────────────────────────┐
│  Backend (FastAPI — Python)                                   │
│  POST /auth/register     ← registrazione utente               │  
|  POST /auth/login        ← login → JWT access                 |
|  POST /auth/refresh      ← rinnovo token (token rotation)     |
│  GET  /projects          ← lista progetti dell'utente          │
│  POST /projects          ← crea progetto                       │
│  GET  /projects/:id      ← dettaglio progetto                  │
│  PUT  /projects/:id      ← aggiorna progetto                   │
│  DELETE /projects/:id    ← elimina progetto                    │
│  GET  /projects/:id/members    ← lista membri                  │
│  POST /projects/:id/members    ← aggiungi membro               │
│  DELETE /projects/:id/members/:userId ← rimuovi membro        │
│  GET  /users/search      ← ricerca utente per email (lookup)   │
│  POST /entries          ← create entry                        │
│  GET  /entries          ← list entries (filter)               │
│  GET  /entries/:id      ← get single entry                    │
│  PUT  /entries/:id      ← save entry (no LLM)                 │
│  POST /entries/:id/index← vectorize entry                     │
│  DEL  /entries/:id      ← delete entry                        │
│  POST /search           ← semantic vector search              │
│  POST /chat             ← RAG chat (SSE stream)               │
│  POST /agent            ← ReAct agent (SSE stream)            │
└──────────────────┬────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────┐   ┌──────────────────────┐
│  MongoDB     │   │  LLM Provider        │
│  (documents  │   │  LiteLLM             │
│  + vectors)  │   │  (ollama/openai/groq)│
└──────────────┘   └──────────────────────┘
```

## Backend

**Stack:** Python 3.11+, FastAPI, uvicorn, pymongo, httpx, pydantic-settings, PyJWT, pwdlib[argon2], litellm

### Domain Model

**User** — l'identità autenticata:
| Field | Type | Description |
|---|---|---|
| `id` | `str` | MongoDB ObjectId |
| `email` | `str` | Email univoca (indice unique) |
| `hashed_password` | `str` | Hash argon2 (non esposto nelle API) |
| `first_name` | `str` | Nome |
| `last_name` | `str` | Cognome |
| `company` | `str` | Azienda (opzionale) |
| `created_at` | `datetime` | Timestamp di registrazione |

**Entry** — the core document unit:
| Field | Type | Description |
|---|---|---|
| `id` | `str` | MongoDB ObjectId |
| `entry_type` | `EntryType` | `adr` \| `postmortem` \| `update` |
| `title` | `str` | Document title |
| `projectId` | `ObjectId` | Riferimento al progetto (collection `projects`) |
| `authorId` | `ObjectId` | Riferimento all'utente autore (collection `users`) |
| `author` | `str` | Nome visualizzato dell'autore (copiato al momento della creazione) |
| `content` | `str` | Full HTML content (TipTap) |
| `summary` | `str` | Summary manuale |
| `tags` | `list[str]` | Classification tags |
| `created_at` | `datetime` | Creation timestamp |
| `week` | `str` | ISO week string (e.g. `2026-W10`) |
| `vector_status` | `VectorStatus` | `pending` \| `indexed` \| `outdated` |

**Project** — namespace organizzativo:
| Field | Type | Description |
|---|---|---|
| `id` | `str` | MongoDB ObjectId |
| `name` | `str` | Nome univoco del progetto |
| `description` | `str` | Descrizione opzionale |
| `ownerId` | `ObjectId` | Utente che ha creato il progetto |
| `createdAt` | `datetime` | Timestamp di creazione |

**ProjectMember** — appartenenza utente–progetto:
| Field | Type | Description |
|---|---|---|
| `id` | `str` | MongoDB ObjectId |
| `projectId` | `ObjectId` | Riferimento al progetto |
| `userId` | `ObjectId` | Riferimento all'utente membro |
| `role` | `str` | `owner` \| `member` |
| `addedAt` | `datetime` | Timestamp di aggiunta |

### Services

Il package `services/` è organizzato in quattro sotto-package per responsabilità:

**`services/ai/`** — logica AI
- `rag_service` — ricerca chunk + costruzione prompt + streaming SSE; ingloba il vecchio `chat_service`
- `search_service` — embedding della query + vector search via `chunks_repository`
- `agent` — loop ReAct: il modello ragiona iterativamente, sceglie un tool dal registry, esegue, osserva il risultato e itera fino alla risposta finale (max `max_steps` iterazioni)
- `agent_registry` — catalogo dei tool disponibili all'agente: ricerca semantica, filtri per progetto/tipo, conteggi
- `agent_tools` — implementazione Python dei tool: `search_semantic`, `filter_entries`, `get_entry`, `count_entries`

**`services/domain/`** — business logic di dominio
- `entry_service` — CRUD entry + pipeline di indicizzazione (`index_entry`)
- `auth_service` — `hash_password`, `verify_password` (argon2), `create_access_token`, `create_refresh_token`, `decode_*` (PyJWT HS256), `build_token_response`

**`services/processing/`** — servizi di trasformazione dati
- `chunker` — parsing HTML TipTap → chunk per heading, max 300 token (cl100k_base / tiktoken)
- `embedder` — thin wrapper: delega a `llm.factory.get_embedding_provider().embed()`

**`services/llm/`** — provider LLM (pattern Strategy)
- `base` — ABC: `EmbeddingProvider`, `ChatProvider`, `ToolChatProvider`
- `factory` — `get_embedding_provider()` / `get_chat_provider()` con `lru_cache`; espone provider concreti LiteLLM
- `litellm_provider` — `LiteLLMEmbeddingProvider` e `LiteLLMChatProvider` (streaming chat, tool-calling, embedding)

### Modelli LLM

Il backend usa due variabili nel `.env`:
- `LLM_MODEL` per chat/RAG/agent
- `EMBEDDING_MODEL` per la vettorializzazione

Entrambe seguono il formato `provider/modello` gestito da LiteLLM.

| Modello | Provider | Uso |
|---|---|---|
| `ollama/qwen2.5:7b` | Ollama | Chat RAG e agente ReAct |
| `ollama/nomic-embed-text` | Ollama | Embedding dei chunk (768 dim) |
| `openai/gpt-4o-mini` | OpenAI | Chat RAG e agente (alternativa cloud) |
| `openai/text-embedding-3-small` | OpenAI | Embedding (1536 dim — richiede re-indicizzazione se si cambia da Ollama) |
| `groq/llama-3.3-70b-versatile` | Groq | Chat RAG e agente (alternativa cloud) |

### LLM Provider Abstraction

Il layer `app/services/llm/` disaccoppia il resto del codice dal provider LLM concreto:

```
settings.llm_model / settings.embedding_model (.env)
  └─ factory.py  (get_chat_provider / get_embedding_provider — lru_cache)
    └─ LiteLLMChatProvider / LiteLLMEmbeddingProvider
      └─ litellm (routing per prefisso modello: ollama/openai/groq)
```

`LLM_MODEL` e `EMBEDDING_MODEL` possono essere configurati **indipendentemente** (es. Ollama per embedding e Groq per chat). Il resto del codice (`rag_service.py`, `agent.py`, `embedder.py`) non sa quale provider è attivo.

## Frontend

**Stack:** Tauri v2, React 19, Vite, TypeScript, TailwindCSS, shadcn/ui, TipTap ^3, Zustand, react-markdown

See [frontend-spec.md](./frontend-spec.md) for full detail.

## Authentication & Authorization

### Strategia

Autenticazione **stateless JWT** con token rotation. Accesso alle entry e alle funzioni AI è **project-scoped**: un utente può accedere solo ai progetti di cui è membro (come `owner` o `member`). I ruoli sono gestiti dalla collection `project_members`.

L'owner di un progetto può invitare altri utenti (ricerca per email via `GET /users/search`) e rimuoverli. L'owner non può essere rimosso finché è l'unico membro.

### Token

| Token | Durata default | Contenuto claims |
|---|---|---|
| Access token | 30 min | `sub` (userId), `email`, `type: "access"`, `exp` |
| Refresh token | 7 giorni | `sub`, `type: "refresh"`, `exp` |

Entrambi firmati HS256 con `JWT_SECRET_KEY` dal `.env`.

### Flusso di autenticazione

```
User → POST /auth/register { email, password, first_name?, last_name?, company? }
  → password hashata con argon2 (pwdlib)
  → UserDocument salvato in MongoDB (collection `users`, indice unique su `email`)
  → Response: UserResponse (senza password)

User → POST /auth/login { email, password }
  → lookup per email + verify argon2 (costante nel tempo — anti timing attack)
  → Response: TokenResponse { access_token, refresh_token, user: UserResponse }
  → Frontend: token salvati in localStorage, profilo in Zustand store

Request autenticata → header Authorization: Bearer <access_token>
  → dependency get_current_user() in app/dependencies/auth.py
  → decodifica JWT, lookup utente per sub (ObjectId _id)
  → 401 se token invalido/scaduto/utente non trovato

Access token scaduto → POST /auth/refresh { refresh_token }
  → nuovi access_token + refresh_token (token rotation)
  → Response: TokenResponse
  → Frontend: refresh silenzioso — la request originale viene ripetuta
```

### Endpoint pubblici vs protetti

| Endpoint | Autenticazione richiesta |
|---|---|
| `POST /auth/register` | ❌ pubblico |
| `POST /auth/login` | ❌ pubblico |
| `POST /auth/refresh` | ❌ pubblico |
| `GET /users/search` | ✅ Bearer token |
| `GET/POST/PUT/DELETE /projects` e `/projects/:id/*` | ✅ Bearer token + membership check |
| Tutti gli altri (`/entries`, `/search`, `/chat`, `/agent`) | ✅ Bearer token + membership check |

### Frontend

- `ui/src/store/auth.store.ts` — Zustand store: `token`, `refreshToken`, `user`; persistiti in `localStorage`
- `ui/src/api/client.ts` — injetta `Authorization: Bearer` header su ogni request; su 401 tenta refresh silenzioso (singleton promise — evita thundering herd); se il refresh fallisce chiama `logout()`
- `ui/src/api/chat.ts` — idem per le SSE stream di `/chat` e `/agent` (fetch dirette non passano per `client.ts`)
- `ui/src/components/auth/` — `LoginPage`, `RegisterPage`, `AuthBrandingPanel`; il toggle tema è disponibile prima del login
- `ui/src/App.tsx` — auth gate: se `token === null` → pagine auth, altrimenti layout principale

## Data Flow

### Register / Login
```
POST /auth/register { email, password, first_name?, last_name?, company? }
  → Valida email univoca → hasha password → salva UserDocument
  → Response: UserResponse (201)

POST /auth/login { email, password }
  → Verifica credenziali (costante nel tempo)
  → Response: TokenResponse { access_token, refresh_token, user }
  → UI: token in localStorage, layout principale sbloccato
```

### Create Entry
```
POST /entries { content, entry_type, title, project_id }
  → project_id: ObjectId del progetto (membership verificata)
  → author ricavato dal token JWT (authorId + nome display)
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
  → Backend: loop ReAct — max max_steps iterazioni con stream=True
       1. LLM ragiona sull'input (streaming tokens come 'reasoning')
       2. Sceglie un tool dal registry (tool_calls nel chunk intermedio)
       3. Esegue il tool e manda subito l'evento 'step' al client
       4. Ripete finché ha abbastanza informazioni o raggiunge max_steps
       5. Genera la risposta finale come token in streaming
  → SSE stream:
       data: {"type":"reasoning","content":"..."}   ← ragionamento del modello
       data: {"type":"step","tool":"...","args":{},"result":{}}  ← tool eseguito
       data: {"type":"token","content":"..."}         ← risposta finale token-by-token
       data: {"type":"done","steps":[...],"model":"..."}
  → Answer rendered as markdown in chat bubble
  → Steps shown as collapsible list above the answer
```

## Deployment

The application runs fully locally:
- Tauri bundles the frontend as a native desktop binary
- FastAPI starts on `localhost:8000` (launched by Tauri sidecar or separately)
- MongoDB runs locally or via connection string in `.env`
- LLM calls pass through LiteLLM (local via Ollama or cloud via OpenAI/Groq, depending on model prefix)

Cloud dependencies are optional and depend on the configured model providers.
