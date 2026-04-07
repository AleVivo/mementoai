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

### Frontend (desktop app)
- [Node.js 20+](https://nodejs.org/)
- [Rust + cargo](https://rustup.rs/) — toolchain `stable-x86_64-pc-windows-msvc`
- **Windows:** [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) con workload *Sviluppo di applicazioni desktop con C++* (richiesto da Rust per il linker `link.exe`)

### LLM Provider

Il provider LLM è configurato a runtime dalla **admin console** — non richiede modifiche al `.env`.

Il default è **Ollama** in locale. Prima di avviare il backend, assicurati di avere Ollama in esecuzione e i modelli scaricati:

```bash
ollama pull qwen2.5:7b        # chat RAG e agente ReAct
ollama pull nomic-embed-text  # embedding vettoriale (768 dim)
```

> LiteLLM gestisce il routing verso Ollama, OpenAI e Groq tramite prefisso modello (`ollama/...`, `openai/...`, `groq/...`).
> Per i modelli Ollama usati in RAG e agente ReAct usa il prefisso `ollama_chat` — non `ollama` — per richiamare l'endpoint corretto con supporto tool e reasoning.

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
LOG_LEVEL=INFO            # DEBUG per log dettagliati, INFO per flusso normale
JWT_SECRET_KEY=<stringa-casuale-lunga>  # es. openssl rand -hex 32
```

> **Il file `.env` contiene solo variabili infrastrutturali.** Provider LLM, modelli, API key e observability sono configurati dalla admin console e salvati su MongoDB — non nel `.env`.

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

Il seed è suddiviso in moduli separati orchestrati da `seed.py`:

| File | Contenuto |
|---|---|
| `seed_config.py` | `config_schema` (struttura admin console) + `config_values` con default Ollama |
| `seed_users.py` | Utenti di test |
| `seed_project.py` | Progetto + membri |
| `seed_entries.py` | Entry di demo |

Credenziali di test:
- `alex@memento.com` / `memento123` — **admin** + owner del progetto `shopflow`
- `marco@memento.com` / `memento123` — membro del progetto `shopflow`

> `scripts/seed.py` crea automaticamente l'indice vettoriale `chunks_vector_index` su MongoDB e inserisce la configurazione di default per Ollama — non è necessario configurare nulla manualmente prima del primo avvio.

### 3. Admin console (primo avvio)

Il seed inserisce una configurazione di default per Ollama. Per verificarla o modificarla, accedi con `alex@memento.com` (ruolo admin) e apri la admin console.

Da lì puoi configurare:
- **LLM Provider** — provider e modello per chat RAG e agente (Ollama, OpenAI, Groq)
- **Embedding Provider** — provider e modello per la vettorializzazione (Ollama, OpenAI)
- **Observability** — tracing AI con Langfuse (opzionale, vedi sezione dedicata)

> La configurazione è salvata su MongoDB e applicata immediatamente senza riavviare il backend.

### 4. Frontend (Tauri desktop app)

```bash
cd ui
npm install        # solo la prima volta
npm run tauri dev
```

Alla prima esecuzione Rust compila il layer nativo — richiede 2-5 minuti. Le esecuzioni successive sono molto più veloci grazie alla cache di Cargo.

La finestra desktop si apre automaticamente e punta al backend su `http://localhost:8000`.

> **Modifiche al codice React** (`.tsx`/`.ts`) si riflettono live via HMR senza ricompilare Rust.  
> **Modifiche a `src-tauri/`** (configurazione Tauri, codice Rust) richiedono ricompilazione automatica.

### Build produzione

```bash
cd ui
npm run tauri build
```

Produce un installer `.exe` standalone in `ui/src-tauri/target/release/bundle/`.

---

## Observability (opzionale)

MementoAI supporta il tracing AI tramite **Langfuse** self-hosted. Quando abilitato, ogni chiamata alla pipeline RAG e all'agente ReAct viene tracciata con latenze, token count e gerarchia delle span.

### Setup Langfuse

Avvia Langfuse in locale con Docker Compose (fornito da Langfuse):

```bash
# Dalla directory di Langfuse
docker compose up -d
```

La dashboard è disponibile su `http://localhost:3000`. Al primo avvio crea un account, una organization e un progetto, poi genera le API keys da **Settings → API Keys**.

### Configurazione in MementoAI

Dalla admin console (`alex@memento.com`), sezione **Observability**:

| Campo | Valore |
|---|---|
| Provider | `langfuse` |
| Host | `http://localhost:3000` (o l'IP della macchina che ospita Langfuse) |
| Public Key | `pk-lf-...` (dalla dashboard Langfuse) |
| Secret Key | `sk-lf-...` (dalla dashboard Langfuse) |

La configurazione è applicata immediatamente senza riavvio. Per disabilitare il tracing, imposta il provider su `none`.

### Cosa viene tracciato

| Trace | Contenuto |
|---|---|
| `rag_call` | Pipeline RAG completa: retrieval, reranking, sintesi risposta LLM, token streaming |
| `entry_indexing` | Pipeline di indicizzazione: parsing HTML, chunking gerarchico, embedding e scrittura su MongoDB |
| `agent_call` | Conversazione agente LangGraph: tutti gli step del grafo (agent + tool nodes) |
| `litellm_request` | Ogni chiamata LLM con prompt, risposta, token, latenza (span figlia automatica) |

---

## Struttura del progetto

```
MementoAI/
├── app/
│   ├── main.py           # FastAPI entrypoint + lifespan (avvia run_all_handlers)
│   ├── config.py         # Settings con pydantic-settings (.env)
│   ├── models/           # Modelli Pydantic (Entry, Project, User, Config...)
│   │   └── folder.py      # Schemi cartelle: create/update/move, tree response
│   ├── routers/          # Endpoint API
│   │   ├── entries.py
│   │   ├── search.py
│   │   ├── chat.py
│   │   ├── agent.py
│   │   ├── auth.py
│   │   ├── project.py
│   │   ├── users.py
│   │   ├── folders.py     # CRUD cartelle progetto: /projects/{project_id}/folders
│   │   └── admin.py      # GET/PUT /admin/config — protetto da require_admin
│   ├── dependencies/
│   │   ├── auth.py       # get_current_user + require_admin
│   │   ├── entries.py    # Validazione accesso entry per progetto
│   │   └── project.py    # Validazione membership progetto
│   ├── handlers/
│   │   └── config_handlers.py  # Dispatch table SECTION_HANDLERS — reload provider LLM e observability
│   ├── observability/
│   │   └── langfuse_integration.py  # Lifecycle Langfuse: setup, teardown, flush, is_active
│   ├── services/
│   │   ├── ai/           # Logica AI: RAG, ricerca semantica, agente LangGraph
│   │   │   ├── rag_service.py    # Pipeline RAG con LlamaIndex QueryEngine + streaming SSE
│   │   │   ├── search_service.py # Ricerca semantica via retriever LlamaIndex
│   │   │   ├── agent_graph.py    # Grafo LangGraph: StateGraph con nodi agent/tools e MemorySaver
│   │   │   ├── agent_state.py    # AgentState TypedDict (messages, project_ids, conversation_id)
│   │   │   ├── agent_service.py  # run_agent_stream(): esecuzione grafo + trasporto SSE
│   │   │   └── agent_tools.py    # Tool LangChain (@tool): search_semantic, filter_entries, get_entry, count_entries
│   │   ├── ingestion/    # Pipeline di indicizzazione LlamaIndex
│   │   │   ├── pipeline.py       # Orchestratore: reader → HierarchicalNodeParser → embedding → MongoDB
│   │   │   └── readers/
│   │   │       └── html_reader.py # HTML TipTap → Document LlamaIndex con testo strutturato
│   │   ├── retrieval/    # Retrieval LlamaIndex
│   │   │   ├── llama_store.py    # Singleton MongoDBAtlasVectorSearch + MongoDocumentStore
│   │   │   ├── retriever.py      # get_retriever(): AutoMergingRetriever con pre-filter project_id
│   │   │   └── reranker.py       # get_reranker(): SentenceTransformerRerank cross-encoder locale
│   │   ├── domain/       # Business logic di dominio
│   │   │   ├── entry_service.py   # CRUD entry + pipeline di indicizzazione
│   │   │   ├── project_service.py # CRUD progetti + gestione membri
│   │   │   ├── folder_service.py  # Gestione cartelle: create/rename/move/delete + tree
│   │   │   ├── auth_service.py    # JWT, hashing argon2, build_token_response
│   │   │   └── config_service.py  # Merge schema+values, validazione, cifratura secret
│   │   └── llm/          # Astrazione LLM (pattern Strategy)
│   │       ├── base.py
│   │       ├── factory.py          # Re-export da provider_cache (backward compat)
│   │       ├── provider_cache.py   # Singleton in memoria — aggiornabile a runtime
│   │       └── litellm_provider.py # LiteLLMChatProvider / LiteLLMEmbeddingProvider
│   ├── utils/
│   │   └── encryption.py   # Fernet AES-128 — encrypt/decrypt/mask_secret
│   └── db/
│       ├── client.py
│       └── repositories/
│           ├── entry_repository.py   # CRUD collection entries
│           ├── folder_repository.py  # CRUD collection folders + move path cascata
│           ├── project_repository.py # CRUD collection projects + project_members
│           ├── users_repository.py   # CRUD collection users
│           ├── chunks_repository.py  # insert/delete/vector search collection chunks
│           └── config_repository.py  # get/upsert config_schema e config_values
├── infra/                # Script per la gestione del container MongoDB
│   ├── docker_mongo.py   # Lifecycle container (pull, run, start, stop, health check)
│   ├── docker-compose.yaml # Compose alternativo per gestione manuale
│   ├── start.py          # python infra/start.py — avvia il container
│   └── stop.py           # python infra/stop.py — ferma il container
├── scripts/
│   ├── seed.py           # Orchestratore — chiama i moduli seed_*, popola il DB con dati di test e crea l'indice vettoriale
│   ├── seed_config.py    # config_schema + config_values default Ollama
│   ├── seed_users.py     # Utenti di test
│   ├── seed_project.py   # Progetto + membri
│   └── seed_entries.py   # Entry di demo
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
| `POST` | `/entries` | Crea una nuova entry (no LLM — solo persistenza, `vector_status: pending`, `folder_id` opzionale) |
| `GET` | `/entries` | Lista entries con filtri (`project_id`, `entry_type`, `week`, `folder_id`, `recursive`, `limit`, `skip`) |
| `GET` | `/entries/{id}` | Singola entry per ID |
| `PUT` | `/entries/{id}` | Aggiorna entry (no LLM — imposta `vector_status: outdated`, inclusi move cartella) |
| `POST` | `/entries/{id}/index` | Indicizza manualmente: chunking HTML + embedding vettoriale |
| `DELETE` | `/entries/{id}` | Elimina entry e relativi chunk |
| `POST` | `/projects/{id}/folders` | Crea cartella (root o subfolder) |
| `GET` | `/projects/{id}/folders` | Albero cartelle del progetto |
| `PUT` | `/projects/{id}/folders/{folderId}` | Rinomina cartella |
| `PUT` | `/projects/{id}/folders/{folderId}/move` | Sposta cartella con aggiornamento path discendenti |
| `DELETE` | `/projects/{id}/folders/{folderId}` | Elimina cartella vuota (no figli/no entry) |
| `POST` | `/search` | Ricerca semantica vettoriale sui chunk con score di cosine similarity |
| `POST` | `/chat` | Chat RAG in streaming SSE — emette eventi `sources` (fonti), `token` (risposta incrementale) e `done`; `project_id` opzionale (omesso = tutta la KB) |
| `POST` | `/agent` | Chat agente ReAct — usa tool (ricerca, filtri, conteggi) per rispondere in più step; `project_id` opzionale |
| `GET` | `/admin/config` | Lista tutte le sezioni di configurazione — **solo admin** |
| `GET` | `/admin/config/{section_id}` | Singola sezione con schema + valori correnti — **solo admin** |
| `PUT` | `/admin/config/{section_id}` | Aggiorna configurazione + reload provider immediato — **solo admin** |

---

## Pipeline di indicizzazione

L'indicizzazione è **manuale** — si avvia cliccando il pulsante "Indicizza" nella toolbar dell'editor. Non viene mai avviata automaticamente al salvataggio.

```
POST /entries/{id}/index
  1. html_reader: HTML TipTap → testo strutturato (heading → ## markdown)
                  → Document LlamaIndex con metadati (entry_id, project_id, entry_type, ...)
  2. HierarchicalNodeParser (chunk_sizes=[2048, 512, 128] token):
       - root   ~2048 token → nodi padre, contesto ampio (AutoMergingRetriever)
       - medio  ~512  token → nodi intermedi
       - leaf   ~128  token → nodi foglia (unici ad essere embeddati)
  3. MongoDB — scrittura:
       - TUTTI i nodi → collection node_docstore/data (MongoDocumentStore)
       - leaf + embedding → collection chunks (MongoDBAtlasVectorSearch)
       - imposta vector_status = indexed
```

Al recupero (`/chat`, `/search`, `/agent`), l'`AutoMergingRetriever` usa `node_docstore` per espandere i leaf node in nodi padre se abbastanza fratelli vengono recuperati insieme — aumenta il contesto passato all'LLM senza aumentare il numero di chiamate embedding.

Summary e tag dell'entry sono **sempre manuali** — inseriti dall'utente nell'editor.

---

## MongoDB — Vector Search Index

La ricerca vettoriale opera sulla collection **`chunks`** (leaf node con embedding). I nodi padre (root ~2048t, medi ~512t) sono conservati nella collection **`node_docstore/data`** — nessun indice vettoriale necessario su questa collection.

L'indice viene creato automaticamente da `scripts/seed.py` al primo avvio — non è necessario crearlo manualmente.

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
        path: "metadata.project_id"
      }
    ]
  }
)
```

> **Nota:** LlamaIndex scrive i metadati sotto il campo `metadata` (oggetto nested). Il path del filtro è `metadata.project_id`, non `projectId` al top-level.

Verifica che lo status sia `READY` prima di usare `/search`, `/chat` e `/agent`:

```javascript
db.chunks.getSearchIndexes()
```

---

## Documentazione

| File | Contenuto |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Architettura del sistema, domain model, data flow dettagliato (autenticazione, create/save/index entry, RAG, agent, admin config update), admin console e configurazione dinamica dei provider,  strategia di autenticazione JWT e project-scoped access control | 
| [docs/frontend-spec.md](docs/frontend-spec.md) | Specifiche frontend: stack tecnologico, struttura directory, TypeScript types, layout UI, configurazione TipTap, comportamenti UX (autosave, indicizzazione, chat, shortcut) |
| [docs/theming.md](docs/theming.md) | Sistema di design token semantici (light/dark), mapping colori per tipo entry e stati UI, linee guida per usare token invece di classi colore hardcoded |