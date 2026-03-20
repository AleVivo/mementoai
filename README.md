# Memento

Knowledge base conversazionale per team di sviluppo piccoli. Permette di catturare decisioni tecniche, post-mortem e aggiornamenti di progetto, rendendoli recuperabili tramite ricerca semantica e chat in linguaggio naturale.

---

> **Nota sperimentale — Frontend**
> Il frontend desktop (`ui/`) è stato sviluppato interamente con **GitHub Copilot** (Claude Sonnet 4.6) come esperimento di sviluppo AI-assisted. Lo stack scelto (Tauri v2 + React + TipTap + shadcn/ui) era sconosciuto all'autore prima di questo progetto. L'obiettivo era valutare fino a che punto un agente AI può guidare lo sviluppo su tecnologie mai usate, dalla scelta dello stack all'implementazione.

---

## Prerequisiti

### Backend
- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) — package manager Python
- **MongoDB** con supporto `$vectorSearch` (mongot) — una delle opzioni seguenti:
  - [MongoDB Atlas](https://www.mongodb.com/atlas) (cloud)
  - MongoDB locale con mongot configurato
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) + `python infra/start.py` — opzione più semplice per lo sviluppo locale (usa `mongodb/mongodb-atlas-local` che include mongot)
- [Ollama](https://ollama.com/) in esecuzione su `localhost:11434`

### Frontend (desktop app)
- [Node.js 20+](https://nodejs.org/)
- [Rust + cargo](https://rustup.rs/) — toolchain `stable-x86_64-pc-windows-msvc`
- **Windows:** [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) con workload *Sviluppo di applicazioni desktop con C++* (richiesto da Rust per il linker `link.exe`)

### Modelli Ollama (provider default)

Necessari solo se `LLM_PROVIDER=ollama` (default):

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

| Modello | Uso |
|---|---|
| `qwen2.5:7b` | Generazione risposte RAG e agente ReAct |
| `nomic-embed-text` | Embedding vettoriale dei chunk (768 dimensioni) |

> Con Ollama, entrambi i modelli vengono pre-caricati in memoria (`keep_alive: -1`) e scaricati allo spegnimento. Con provider cloud (OpenAI, Groq) il preload viene saltato.

> **Alternativa cloud:** imposta `LLM_PROVIDER=openai` o `LLM_PROVIDER=groq` nel `.env` — in questo caso Ollama non è necessario. Vedi la sezione Configurazione.

---

## Configurazione

Crea un file `.env` nella root del progetto copiando il template:

```bash
cp .env.example .env
```

Modifica `.env` con i tuoi valori:

```dotenv
MONGODB_URL=mongodb://<host>:<port>
MONGODB_USER=<utente>
MONGODB_PASSWORD=<password>
MONGODB_DB=memento
OLLAMA_URL=http://localhost:11434
LOG_LEVEL=INFO            # DEBUG per log dettagliati con timing, INFO per flusso normale
JWT_SECRET_KEY=<stringa-casuale-lunga>  # es. openssl rand -hex 32

# Provider LLM (default: ollama — non richiedono API key)
LLM_PROVIDER=ollama        # ollama | openai | groq
EMBEDDING_PROVIDER=ollama  # ollama | openai  (può differire da LLM_PROVIDER)

# Opzionale — richiesti solo con i rispettivi provider
# OPENAI_API_KEY=sk-...
# GROQ_API_KEY=gsk_...
```

> **Il file `.env` non deve mai essere committato su git.** Contiene credenziali sensibili ed è già incluso nel `.gitignore`.

---

## Installazione dipendenze

```bash
uv sync
```

uv legge `pyproject.toml`, crea automaticamente il virtual environment in `.venv` e installa tutte le dipendenze alle versioni esatte del lockfile.

---

## Avvio

> Avvia sempre MongoDB e il backend **prima** del frontend.

### 0. MongoDB

Assicurati di avere un'istanza MongoDB raggiungibile con supporto `$vectorSearch` e configura `MONGODB_URL`, `MONGODB_USER`, `MONGODB_PASSWORD` nel `.env`.

**Opzione sviluppo locale (Docker):** se non hai Atlas o un MongoDB con mongot, usa gli script in `infra/`:

```bash
python infra/start.py   # avvia il container (pull automatico al primo avvio)
python infra/stop.py    # ferma il container (dati preservati)
```

In alternativa con Docker Compose:

```bash
cd infra
docker compose up -d     # avvia
docker compose stop      # ferma (dati preservati)
docker compose down -v   # reset completo dei dati
```

### 1. Backend

```bash
# Dalla root del progetto
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Il flag `--reload` riavvia il server automaticamente ad ogni modifica del codice — utile in sviluppo, da rimuovere in produzione.

L'API è disponibile su:
- **Base URL:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### 2. Seed (primo avvio)

Al primo avvio, popola il database con dati di test e crea l'indice vettoriale:

```bash
python scripts/seed.py
```

| Flag | Descrizione |
|---|---|
| _(nessuno)_ | Inserisce dati di test (skip se già presenti) |
| `--reset` | Cancella tutto e reinserisce |
| `--reset --no-user` | Reinserisce progetto + entry (utenti già presenti) |

Credenziali di test:
- `alex@memento.com` / `memento123` — owner del progetto `shopflow`
- `marco@memento.com` / `memento123` — membro del progetto `shopflow`

> `scripts/seed.py` crea automaticamente l'indice vettoriale `chunks_vector_index` su MongoDB — non è necessario crearlo manualmente.

### 3. Frontend (Tauri desktop app)

```bash
cd ui
npm install        # solo la prima volta
npm run tauri dev
```

Alla prima esecuzione Rust compila il layer nativo — richiede 2-5 minuti. Le esecuzioni successive sono molto più veloci grazie alla cache di Cargo.

La finestra desktop si apre automaticamente e punta al backend su `http://localhost:8000`.

> **Modifche al codice React** (`.tsx`/`.ts`) si riflettono live via HMR senza ricompilare Rust.  
> **Modifiche a `src-tauri/`** (configurazione Tauri, codice Rust) richiedono ricompilazione automatica.

### Build produzione

```bash
cd ui
npm run tauri build
```

Produce un installer `.exe` standalone in `ui/src-tauri/target/release/bundle/`.

---

## Struttura del progetto

```
MementoAI/
├── app/
│   ├── main.py           # FastAPI entrypoint + lifespan (preload/unload modelli Ollama)
│   ├── config.py         # Settings con pydantic-settings (.env)
│   ├── models/           # Modelli Pydantic (Entry, Project, ProjectMember, User, Chunk...)
│   ├── routers/          # Endpoint API (entries, search, chat, agent, auth, project, users)
│   ├── dependencies/
│   │   ├── auth.py       # get_current_user — dependency FastAPI per tutti gli endpoint protetti
│   │   ├── entries.py    # Validazione accesso entry per progetto
│   │   └── project.py    # Validazione membership progetto
│   ├── services/
│   │   ├── ai/           # Logica AI: RAG, ricerca semantica, agente ReAct
│   │   │   ├── rag_service.py    # Ricerca chunk + costruzione prompt + streaming SSE
│   │   │   ├── search_service.py # Embedding query + vector search
│   │   │   ├── agent.py          # Loop ReAct: ragiona → tool → osserva → risponde
│   │   │   ├── agent_registry.py # Catalogo tool disponibili all'agente
│   │   │   └── agent_tools.py    # Implementazione Python dei tool
│   │   ├── domain/       # Business logic di dominio
│   │   │   ├── entry_service.py   # CRUD entry + pipeline di indicizzazione
│   │   │   ├── project_service.py # CRUD progetti + gestione membri
│   │   │   └── auth_service.py    # JWT, hashing argon2, build_token_response
│   │   ├── processing/   # Pipeline di trasformazione dati
│   │   │   ├── chunker.py        # HTML → chunk per heading, max 300 token
│   │   │   └── embedder.py       # Thin wrapper → llm.factory.get_embedding_provider().embed()
│   │   └── llm/          # Provider LLM (pattern Strategy)
│   │       ├── base.py           # ABC: EmbeddingProvider, ChatProvider, ToolChatProvider
│   │       ├── factory.py        # get_embedding_provider() / get_chat_provider() — lru_cache
│   │       ├── ollama_provider.py # OllamaEmbeddingProvider, OllamaChatProvider, preload/unload
│   │       └── openai_provider.py # OpenAIEmbeddingProvider, OpenAIChatProvider, GroqChatProvider
│   └── db/
│       ├── client.py      # Singleton AsyncMongoClient — get_client(), get_db(), close_client()
│       ├── indexes.py     # Creazione indici MongoDB all'avvio
│       └── repositories/
│           ├── entry_repository.py   # CRUD collection entries
│           ├── project_repository.py # CRUD collection projects + project_members
│           ├── users_repository.py   # CRUD collection users
│           └── chunks_repository.py  # insert/delete/vector search collection chunks
├── infra/                # Script per la gestione del container MongoDB
│   ├── docker_mongo.py   # Lifecycle container (pull, run, start, stop, health check)
│   ├── docker-compose.yaml # Compose alternativo per gestione manuale
│   ├── start.py          # python infra/start.py — avvia il container
│   └── stop.py           # python infra/stop.py — ferma il container
├── scripts/
│   └── seed.py           # Popola il DB con dati di test e crea l'indice vettoriale
├── docs/
│   ├── architecture.md   # Architettura del sistema, domain model, data flow, auth
│   └── frontend-spec.md  # Spec frontend: stack, struttura, TypeScript types, UX behaviors
├── ui/                   # Desktop app Tauri v2 + React + TipTap
│   ├── src/              # Codice React (types, api, store, components)
│   ├── src-tauri/        # Layer Rust + configurazione Tauri
│   └── package.json
├── .github/
│   ├── copilot-instructions.md  # Istruzioni per GitHub Copilot
│   └── prompts/                 # Prompt riutilizzabili per sviluppo guidato
├── .env                  # NON committare — variabili locali
├── .env.example          # Template variabili d'ambiente
├── pyproject.toml        # Dipendenze e metadati progetto
└── uv.lock               # Lockfile versioni esatte
```

---

## Endpoint principali

| Metodo | Endpoint | Descrizione |
|---|---|---|
| `POST` | `/auth/register` | Registra un nuovo utente — `{ email, password, first_name?, last_name?, company? }` |
| `POST` | `/auth/login` | Login — restituisce `access_token` (30 min), `refresh_token` (7 gg) e profilo utente |
| `POST` | `/auth/refresh` | Rinnova access token da refresh token; restituisce nuova coppia di token |
| `GET` | `/projects` | Lista dei progetti di cui l'utente è membro |
| `POST` | `/projects` | Crea un nuovo progetto |
| `GET` | `/projects/{id}` | Dettaglio progetto (solo se membro) |
| `PUT` | `/projects/{id}` | Aggiorna nome/descrizione progetto (solo owner) |
| `DELETE` | `/projects/{id}` | Elimina progetto e tutte le sue entry (solo owner) |
| `GET` | `/projects/{id}/members` | Lista membri del progetto |
| `POST` | `/projects/{id}/members` | Aggiunge membro al progetto (solo owner) — `{ email, role }` |
| `DELETE` | `/projects/{id}/members/{userId}` | Rimuove membro (solo owner) |
| `GET` | `/users/search` | Ricerca utente per email — `?email=...` (usato per aggiungere membri) |
| `POST` | `/entries` | Crea una nuova entry (no LLM — solo persistenza, `vector_status: pending`) |
| `GET` | `/entries` | Lista entries con filtri (`project_id`, `type`, `week`, `limit`, `skip`) |
| `GET` | `/entries/{id}` | Singola entry per ID |
| `PUT` | `/entries/{id}` | Aggiorna entry (no LLM — imposta `vector_status: outdated`) |
| `POST` | `/entries/{id}/index` | Indicizza manualmente: chunking HTML + embedding vettoriale (`nomic-embed-text`) |
| `DELETE` | `/entries/{id}` | Elimina entry e relativi chunk |
| `POST` | `/search` | Ricerca semantica vettoriale sui chunk con score di cosine similarity |
| `POST` | `/chat` | Chat RAG in streaming SSE — emette eventi `sources` (fonti), `token` (risposta incrementale) e `done`; `project_id` opzionale (omesso = tutta la KB) |
| `POST` | `/agent` | Chat agente ReAct — usa tool (ricerca, filtri, conteggi) per rispondere in più step; `project_id` opzionale |

---

## Pipeline di indicizzazione

L'indicizzazione è **manuale** — si avvia cliccando il pulsante "Indicizza" nella toolbar dell'editor. Non viene mai avviata automaticamente al salvataggio.

```
POST /entries/{id}/index
  1. Imposta vector_status = indexed
  2. Chunking HTML (BeautifulSoup)
       - divide per heading h1/h2/h3 — ogni sezione diventa un chunk
       - max 300 token per chunk (tokenizer cl100k_base via tiktoken)
       - soglia minima 30 token — chunk più piccoli vengono fusi
       - liste e blocchi codice trattati come unità atomiche
  3. Embedding di ogni chunk → nomic-embed-text (768 dim)
  4. Salvataggio chunk nella collection MongoDB `chunks`
```

Summary e tag dell'entry sono **sempre manuali** — inseriti dall'utente nell'editor.

---

## MongoDB — Vector Search Index

La ricerca vettoriale opera sulla collection **`chunks`** (non `entries`). L'indice viene creato automaticamente da `scripts/seed.py` al primo avvio — non è necessario crearlo manualmente.

Se necessario, è possibile ricrearlo manualmente dalla shell di MongoDB:

```javascript
use memento

db.chunks.createSearchIndex(
  "chunks_vector_index",
  "vectorSearch",
  {
    fields: [
      {
        type: "vector",
        path: "embedding",
        numDimensions: 768,
        similarity: "cosine"
      },
      {
        type: "filter",
        path: "projectId"
      },
      {
        type: "filter",
        path: "entry_type"
      }
    ]
  }
)
```

Verifica che lo status sia `READY` prima di usare `/search`, `/chat` e `/agent`:

```javascript
db.chunks.getSearchIndexes()
```

---

## Documentazione

| File | Contenuto |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Architettura del sistema, domain model (Entry, Project, User), data flow dettagliato (autenticazione, create/save/index entry, RAG, agent), strategia di autenticazione JWT e project-scoped access control |
| [docs/frontend-spec.md](docs/frontend-spec.md) | Specifiche frontend: stack tecnologico, struttura directory, TypeScript types, layout UI, configurazione TipTap, comportamenti UX (autosave, indicizzazione, chat, shortcut) |