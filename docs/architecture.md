---
generated_by: GitHub Copilot (Claude Sonnet 4.6)
last_updated: 2026-03-23
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
┌──────────────────▼──────────────────────────────────────────────────────────┐
│  Backend (FastAPI — Python)                                                 │
│  POST /auth/register     ← registrazione utente                             │
|  POST /auth/login        ← login → JWT access                               |
|  POST /auth/refresh      ← rinnovo token (token rotation)                   |
│  GET  /projects          ← lista progetti dell'utente                       │
│  POST /projects          ← crea progetto                                    │
│  GET  /projects/:id      ← dettaglio progetto                               │
│  PUT  /projects/:id      ← aggiorna progetto                                │
│  DELETE /projects/:id    ← elimina progetto                                 │
│  GET  /projects/:id/members    ← lista membri                               │
│  POST /projects/:id/members    ← aggiungi membro                            │
│  DELETE /projects/:id/members/:userId ← rimuovi membro                      │
│  GET  /users/search      ← ricerca utente per email (lookup)                │
│  POST /entries          ← create entry                                      │
│  GET  /entries          ← list entries (filter)                             │
│  GET  /entries/:id      ← get single entry                                  │
│  PUT  /entries/:id      ← save entry (no LLM)                               │
│  POST /entries/:id/index← vectorize entry                                   │
│  DEL  /entries/:id      ← delete entry                                      │
│  POST /search           ← semantic vector search                            │
│  POST /chat             ← RAG chat (SSE stream)                             │
│  POST /agent            ← ReAct agent (SSE stream)                          │
│  GET  /admin/config      ← lista sezioni config (admin only)                │
│  GET  /admin/config/:id  ← singola sezione config (admin only)              │
│  PUT  /admin/config/:id  ← aggiorna config + reload provider (admin only)   │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────┐   ┌──────────────────────┐
│  MongoDB     │   │  LLM Provider        │
│  (documents  │   │  LiteLLM             │
│  + vectors   │   │  (ollama/openai/groq)│
│  + config)   │   │  configurato da DB   │
└──────────────┘   └──────────────────────┘
```

## Backend

**Stack:** Python 3.11+, FastAPI, uvicorn, pymongo, pydantic-settings, PyJWT, pwdlib[argon2], litellm, langfuse, cryptography

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
| `role` | `str` | `user` \| `admin` — ruolo a livello di sistema |
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

**ConfigSchema** — struttura della configurazione admin (read-only):
| Field | Type | Description |
|---|---|---|
| `_id` | `str` | Identificatore semantico: `llm` \| `embedding` \| `observability` |
| `type` | `str` | `integration` \| `settings` |
| `label` | `str` | Label visualizzata nella admin console |
| `description` | `str` | Descrizione opzionale |
| `fields` | `list` | Definizione dei campi (text, secret, select, toggle) |

**ConfigValues** — valori correnti della configurazione:
| Field | Type | Description |
|---|---|---|
| `_id` | `str` | Corrisponde all'`_id` del ConfigSchema |
| `values` | `dict` | Valori salvati dall'admin (secret cifrati con Fernet) |
| `status` | `str` | `unknown` \| `active` \| `error` — solo per `integration` |
| `status_message` | `str` | Messaggio di errore opzionale |
| `last_tested_at` | `datetime` | Ultimo test di connessione |
| `updated_at` | `datetime` | Timestamp ultimo aggiornamento |
| `updated_by` | `str` | ObjectId dell'admin che ha aggiornato |

### Services

Il package `services/` è organizzato per responsabilità:

**`services/ai/`** — logica AI
- `rag_service` — ricerca chunk + costruzione prompt + streaming SSE
- `search_service` — embedding della query + vector search via `chunks_repository`
- `agent` — loop ReAct: il modello ragiona iterativamente, sceglie un tool dal registry, esegue, osserva il risultato e itera fino alla risposta finale (max `max_steps` iterazioni)
- `agent_registry` — catalogo dei tool disponibili all'agente: ricerca semantica, filtri per progetto/tipo, conteggi
- `agent_tools` — implementazione Python dei tool: `search_semantic`, `filter_entries`, `get_entry`, `count_entries`

**`services/domain/`** — business logic di dominio
- `entry_service` — CRUD entry + pipeline di indicizzazione (`index_entry`)
- `project_service` — CRUD progetti + gestione membri
- `auth_service` — JWT, hashing argon2, `build_token_response`
- `config_service` — merge schema+values, validazione, cifratura/decifratura secret

**`services/processing/`** — servizi di trasformazione dati
- `chunker` — parsing HTML TipTap → chunk per heading, max 300 token (cl100k_base / tiktoken)
- `embedder` — `generate_embedding` (`@observe as_type="generation"`) — thin wrapper su provider embedding

**`services/llm/`** — provider LLM (pattern Strategy)
- `base` — ABC: `EmbeddingProvider`, `ChatProvider`, `ToolChatProvider`
- `factory` — re-export di `get_langchain_chat_provider` / `get_embedding_provider` da `provider_cache` (backward compatibility)
- `provider_cache` — singleton in memoria per i provider attivi; aggiornabile a runtime senza riavvio
- `litellm_provider` — `LiteLLMChatProvider(model, api_base, api_key)` e `LiteLLMEmbeddingProvider(model, api_base, api_key)`

**`handlers/`** — handler di reload configurazione
- `config_handlers` — dispatch table `SECTION_HANDLERS`: ogni sezione ha un handler che legge `config_values` da MongoDB e aggiorna `provider_cache` o `langfuse_integration`; `run_all_handlers()` chiamato dal lifespan all'avvio

**`observability/`** — tracing AI
- `langfuse_integration` — lifecycle Langfuse: `setup()`, `teardown()`, `flush()`, `is_active()`; gestito come singleton di modulo; attivato da `config_handlers` a runtime

**`utils/`** — utility trasversali
- `encryption` — cifratura simmetrica Fernet (AES-128) derivata da `JWT_SECRET_KEY` via SHA-256; `encrypt()`, `decrypt()`, `mask_secret()`

### Admin Console — Configurazione Dinamica

La configurazione dei provider LLM e dell'observability è gestita a runtime tramite la admin console. Non richiede modifiche al `.env` né riavvii del backend.

**Flusso di aggiornamento:**
```
Admin → PUT /admin/config/{section_id} { values: {...} }
  → config_service valida i values contro config_schema
  → secret cifrati con Fernet prima del salvataggio
  → upsert in config_values
  → config_handlers.run_handler(section_id)
      → get_decrypted_values(section_id)   ← legge da MongoDB con secret in chiaro
      → istanzia nuovo LiteLLMChatProvider(model, api_base, api_key)
      → provider_cache.set_langchain_chat_provider(provider)  ← aggiorna singleton in memoria
  → risponde 200 con schema + values merged (secret mascherati)
```

**Flusso all'avvio:**
```
lifespan
  → run_all_handlers()   ← esegue tutti gli handler registrati in sequenza
      → llm handler        ← inizializza chat provider
      → embedding handler  ← inizializza embedding provider
      → observability handler ← configura Langfuse se abilitato
  → se un provider non ha config_values → RuntimeError esplicito alla prima chiamata AI

shutdown
  → langfuse_integration.flush()  ← svuota la coda di trace pendenti prima di chiudere
  → close_client()                ← chiude la connessione MongoDB
```

**Sezioni configurabili:**

| Section ID | Type | Configura |
|---|---|---|
| `llm` | `integration` | Provider chat: Ollama, OpenAI, Groq — modello e credenziali |
| `embedding` | `integration` | Provider embedding: Ollama, OpenAI — modello e credenziali |
| `observability` | `integration` | Tracing AI: Langfuse (host, public key, secret key) |

**Accesso:** solo utenti con `role: "admin"`. Gli endpoint `/admin/config/*` restituiscono 403 per tutti gli altri utenti. Il ruolo admin si assegna direttamente su MongoDB — non è selezionabile in fase di registrazione.

### LLM Provider Abstraction

```
config_values (MongoDB)
  └─ config_handlers.py  (run_handler → legge DB, istanzia provider)
       └─ provider_cache.py  (singleton in memoria — get/set_langchain_chat_provider)
            └─ LiteLLMChatProvider(model, api_base, api_key)
                 └─ litellm  (routing per prefisso: ollama/ openai/ groq/)
```

`LLM_MODEL` e `EMBEDDING_MODEL` non sono più nel `.env` — sono salvati in `config_values` e configurabili dalla admin console senza riavvio. `api_base` e `api_key` vengono passati direttamente alle chiamate LiteLLM — nessun effetto collaterale su `os.environ` (eccezione: Langfuse richiede variabili d'ambiente per il suo SDK).

**Provider supportati:**

| Modello | Provider | Uso |
|---|---|---|
| `ollama_chat/qwen2.5:7b` | Ollama | Chat RAG e agente ReAct |
| `ollama/nomic-embed-text` | Ollama | Embedding dei chunk (768 dim) |
| `openai/gpt-4o-mini` | OpenAI | Chat RAG e agente (alternativa cloud) |
| `openai/text-embedding-3-small` | OpenAI | Embedding (1536 dim — richiede re-indicizzazione se si cambia da Ollama) |
| `groq/llama-3.3-70b-versatile` | Groq | Chat RAG e agente (alternativa cloud) |

### Observability — Langfuse

Il tracing AI è opzionale e configurabile a runtime dalla admin console. Quando abilitato, strumenta la pipeline RAG e l'agente ReAct senza impatto sul comportamento funzionale.

**Architettura del tracing:**

```
config_values (MongoDB)
  └─ config_handlers._handle_observability()
       └─ langfuse_integration.setup(host, public_key, secret_key)
            ├─ LANGFUSE_HOST / LANGFUSE_OTEL_HOST / LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY
            └─ litellm.callbacks = ["langfuse_otel"]  ← trace automatici per ogni chiamata LiteLLM
```

**Gerarchia dei trace in Langfuse:**

```
execute_rag                     ← @observe — pipeline RAG completa
  └─ generate_embedding         ← @observe as_type="generation"
       └─ litellm_request       ← automatico via langfuse_otel (model, tokens, latency)

run_agent_stream (root span)    ← start_observation manuale (generator SSE)
  ├─ agent_step                 ← @observe — ogni iterazione ReAct
  │    └─ litellm_request       ← automatico via langfuse_otel
  └─ agent_step (final)
       └─ litellm_request
```

Le chiamate LiteLLM (`acompletion`, `aembedding`) diventano span figlie automaticamente grazie al contesto OpenTelemetry propagato da `@observe`. Non è necessario strumentare `litellm_provider.py` — il tracing è trasparente.

**Separazione logica / trasporto SSE:**

`rag_service` e `agent` separano la logica AI dal trasporto SSE perché `@observe` non supporta `AsyncGenerator` (funzioni con `yield`). La logica tracciabile è in funzioni normali (`_execute_rag`, `_run_agent_step`); il trasporto SSE è in generator separati (`stream_rag`, `run_agent_stream`) che li orchestrano.

**Lifecycle:**

- `setup()` — chiamato da `config_handlers` quando l'admin abilita Langfuse; idempotente
- `teardown()` — chiamato quando il provider viene impostato su `none`; rimuove credenziali e callback
- `flush()` — chiamato nel lifespan FastAPI allo shutdown per non perdere trace in coda
- `is_active()` — usato dai servizi per decidere se aprire span manuali

## Frontend

**Stack:** Tauri v2, React 19, Vite, TypeScript, TailwindCSS, shadcn/ui, TipTap ^3, Zustand, react-markdown

See [frontend-spec.md](./frontend-spec.md) for full detail.

## Authentication & Authorization

### Strategia

Autenticazione **stateless JWT** con token rotation. Accesso alle entry e alle funzioni AI è **project-scoped**: un utente può accedere solo ai progetti di cui è membro (come `owner` o `member`). I ruoli di progetto sono gestiti dalla collection `project_members`.

Il ruolo `admin` è un ruolo **a livello di sistema** sul documento `User` — non è legato a un progetto specifico. Gli admin accedono agli endpoint `/admin/config/*` per gestire la configurazione dell'istanza.

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
  → role: "user" assegnato di default (admin si assegna direttamente su MongoDB)
  → Response: UserResponse (senza password)

User → POST /auth/login { email, password }
  → lookup per email + verify argon2 (costante nel tempo — anti timing attack)
  → Response: TokenResponse { access_token, refresh_token, user: UserResponse }
  → Frontend: token salvati in localStorage, profilo in Zustand store

Request autenticata → header Authorization: Bearer <access_token>
  → dependency get_current_user() in app/dependencies/auth.py
  → decodifica JWT, lookup utente per sub (ObjectId _id)
  → 401 se token invalido/scaduto/utente non trovato

Request admin → dependency require_admin()
  → chiama get_current_user() + verifica role == "admin"
  → 403 se ruolo non è admin

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
| `GET/PUT /admin/config/*` | ✅ Bearer token + role: "admin" |

### Frontend

- `ui/src/store/auth.store.ts` — Zustand store: `token`, `refreshToken`, `user`; persistiti in `localStorage`
- `ui/src/api/client.ts` — injetta `Authorization: Bearer` header su ogni request; su 401 tenta refresh silenzioso (singleton promise — evita thundering herd); se il refresh fallisce chiama `logout()`
- `ui/src/api/chat.ts` — idem per le SSE stream di `/chat` e `/agent`
- `ui/src/components/auth/` — `LoginPage`, `RegisterPage`, `AuthBrandingPanel`
- `ui/src/App.tsx` — auth gate: se `token === null` → pagine auth, altrimenti layout principale

## Data Flow

### Register / Login
```
POST /auth/register { email, password, first_name?, last_name?, company? }
  → Valida email univoca → hasha password → salva UserDocument (role: "user")
  → Response: UserResponse (201)

POST /auth/login { email, password }
  → Verifica credenziali (costante nel tempo)
  → Response: TokenResponse { access_token, refresh_token, user }
  → UI: token in localStorage, layout principale sbloccato
```

### Admin Config Update
```
PUT /admin/config/{section_id} { values: { provider, model, api_key, ... } }
  → require_admin: verifica role == "admin" → 403 altrimenti
  → config_service.update_config_section():
      → valida values contro config_schema (required, required_if, select options)
      → cifra campi type:"secret" con Fernet
      → upsert in config_values
  → config_handlers.run_handler(section_id):
      → get_decrypted_values() ← legge DB con secret in chiaro
      → istanzia nuovo provider (LiteLLMChatProvider / LiteLLMEmbeddingProvider)
        oppure chiama langfuse_integration.setup() / teardown()
      → provider_cache.set_*_provider() ← aggiorna singleton
  → Response: ConfigSectionResponse (schema + values merged, secret mascherati)
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
  → embedding → vettore per ogni chunk (provider_cache.get_embedding_provider())
               → generate_embedding() tracciata con @observe se Langfuse attivo
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
  → Backend:
      _execute_rag() [@observe]
        → query embedded (generate_embedding [@observe])
        → vector search sui chunk (collection `chunks`)
        → top-k chunk recuperati + contesto costruito
      stream_rag() [SSE transport]
        → SSE stream aperto:
            data: {"type":"sources","sources":[...]}
            data: {"type":"token","content":"..."}   ← streaming LLM
            data: {"type":"done"}
  → Answer rendered as markdown in chat bubble
```

### Agent Chat
```
User types question in chat panel (modalità Agent)
  → POST /agent { question, project?, max_steps }
  → Backend:
      run_agent_stream() [root span manuale + SSE transport]
        → loop ReAct — max max_steps iterazioni:
            _run_agent_step() [@observe]
              1. LLM ragiona sull'input
              2. Sceglie un tool dal registry
              3. Esegue il tool
            → evento 'step' al client
        → risposta finale in streaming
      → SSE stream:
          data: {"type":"reasoning","content":"..."}
          data: {"type":"step","tool":"...","args":{},"result":{}}
          data: {"type":"token","content":"..."}
          data: {"type":"done","steps":[...],"model":"..."}
```

## Deployment

The application runs fully locally — no mandatory cloud dependencies:

- Tauri bundles the frontend as a native desktop binary
- FastAPI starts on `localhost:8000` (launched by Tauri sidecar or separately during development)
- MongoDB runs locally via Docker container (see `infra/`)
- LLM provider is configured via the admin console — Ollama (local, default) or cloud providers (OpenAI, Groq) are optional and set at runtime without `.env` changes or restarts
- Langfuse tracing is optional — disabled by default, enabled from the admin console without restart

**`.env` contains infrastructure only** — secrets and URLs that cannot change at runtime:

| Variable | Description |
|---|---|
| `MONGODB_URL` | MongoDB connection string |
| `MONGODB_DB` | Database name |
| `MONGODB_USER` | MongoDB user |
| `MONGODB_PASSWORD` | MongoDB password |
| `JWT_SECRET_KEY` | JWT signing key (also used to derive Fernet encryption key) |
| `LOG_LEVEL` | Logging level (default: INFO) |

LLM provider, model, API keys, and observability settings are stored in `config_values` (MongoDB) and managed exclusively via `PUT /admin/config/{section_id}`.