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
- [Ollama](https://ollama.com/) in esecuzione su `localhost:11434`
- MongoDB 8.2+ configurato come replica set (richiesto per `$vectorSearch`)

### Frontend (desktop app)
- [Node.js 20+](https://nodejs.org/)
- [Rust + cargo](https://rustup.rs/) — toolchain `stable-x86_64-pc-windows-msvc`
- **Windows:** [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) con workload *Sviluppo di applicazioni desktop con C++* (richiesto da Rust per il linker `link.exe`)

### Modelli Ollama richiesti

```bash
ollama pull mistral
ollama pull nomic-embed-text
```

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

> Avvia sempre il backend **prima** del frontend.

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

### 2. Frontend (Tauri desktop app)

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
│   ├── main.py           # FastAPI entrypoint + lifespan
│   ├── config.py         # Settings con pydantic-settings
│   ├── models/           # Modelli Pydantic (Entry, VectorStatus, SearchResult...)
│   ├── routers/          # Endpoint API (entries, search, chat)
│   ├── services/         # Logica di business (ollama, classifier, embedding, rag)
│   └── db/               # Connessione e query MongoDB
├── ui/                   # Desktop app Tauri v2 + React + TipTap
│   ├── src/              # Codice React (types, api, store, components)
│   ├── src-tauri/        # Layer Rust + configurazione Tauri
│   └── package.json
├── docs/                 # Architettura, spec frontend, istruzioni Copilot
├── .github/prompts/      # Prompt Copilot per sviluppo guidato
├── .env                  # NON committare — variabili locali
├── .env.example          # Template variabili d'ambiente
├── pyproject.toml        # Dipendenze e metadati progetto
└── uv.lock               # Lockfile versioni esatte
```

---

## Endpoint principali

| Metodo | Endpoint | Descrizione |
|---|---|---|
| `POST` | `/entries` | Crea una nuova entry (no LLM — solo persistenza) |
| `GET` | `/entries` | Lista entries con filtri (`project`, `type`, `week`, `limit`, `skip`) |
| `GET` | `/entries/{id}` | Singola entry per ID |
| `PUT` | `/entries/{id}` | Aggiorna entry (no LLM — imposta `vector_status: outdated`) |
| `POST` | `/entries/{id}/index` | Avvia pipeline LLM: genera summary, tags e embedding vettoriale |
| `DELETE` | `/entries/{id}` | Elimina entry |
| `POST` | `/search` | Ricerca semantica vettoriale con score di cosine similarity |
| `POST` | `/chat` | Chat RAG — risponde in linguaggio naturale citando le fonti |

---

## MongoDB — Vector Search Index

Il `$vectorSearch` richiede un indice dedicato sulla collection `entries`. Crearlo una volta dalla shell di MongoDB:

```javascript
use memento

db.entries.createSearchIndex(
  "vector_index",
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
        path: "project"
      }
    ]
  }
)
```

Verifica che lo status sia `READY` prima di usare `/search` e `/chat`:

```javascript
db.entries.getSearchIndexes()
```