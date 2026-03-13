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
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

| Modello | Uso |
|---|---|
| `qwen2.5:7b` | Generazione risposte RAG chat |
| `nomic-embed-text` | Embedding vettoriale dei chunk (768 dimensioni) |

> All'avvio del backend entrambi i modelli vengono pre-caricati in memoria (`keep_alive: -1`) e scaricati solo allo spegnimento. Questo elimina il cold-start sulla prima richiesta.

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
LOG_LEVEL=INFO   # DEBUG per log dettagliati con timing, INFO per flusso normale
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
│   ├── main.py           # FastAPI entrypoint + lifespan (preload/unload modelli Ollama)
│   ├── config.py         # Settings con pydantic-settings (.env)
│   ├── models/           # Modelli Pydantic (Entry, Chunk, VectorStatus, SearchResult...)
│   ├── routers/          # Endpoint API (entries, search, chat, agent)
│   ├── services/
│   │   ├── ollama.py     # Client Ollama — qwen2.5:7b (generate) + nomic-embed-text (embed)
│   │   ├── chunker.py    # HTML chunking: segmentazione per heading, max 300 token/chunk
│   │   ├── embedding.py  # Wrapper generate_embedding → ollama
│   │   ├── classifier.py # DEPRECATED — enrich_entry (summary/tag LLM) rimosso dalla pipeline
│   │   ├── rag.py        # Costruzione context + prompt + chiamata generate
│   │   ├── agent.py      # Loop ReAct: ragiona → sceglie tool → esegue → itera fino alla risposta
│   │   ├── agent_registry.py # Catalogo tool disponibili all'agente (search, filtri, conteggi)
│   │   ├── chat_service.py
│   │   ├── search_service.py
│   │   └── entry_service.py
│   └── db/
│       ├── mongo.py       # Collection entries
│       └── chunks_mongo.py # Collection chunks + vector search
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
| `POST` | `/entries` | Crea una nuova entry (no LLM — solo persistenza, `vector_status: pending`) |
| `GET` | `/entries` | Lista entries con filtri (`project`, `type`, `week`, `limit`, `skip`) |
| `GET` | `/entries/{id}` | Singola entry per ID |
| `PUT` | `/entries/{id}` | Aggiorna entry (no LLM — imposta `vector_status: outdated`) |
| `POST` | `/entries/{id}/index` | Indicizza manualmente: chunking HTML + embedding vettoriale (`nomic-embed-text`) |
| `DELETE` | `/entries/{id}` | Elimina entry e relativi chunk |
| `POST` | `/search` | Ricerca semantica vettoriale sui chunk con score di cosine similarity |
| `POST` | `/chat` | Chat RAG — risponde citando le fonti per titolo (`[Titolo nota]`); `project` opzionale (omesso = tutta la KB) |
| `POST` | `/agent` | Chat agente ReAct — usa tool (ricerca, filtri, conteggi) per rispondere in più step; `project` opzionale |

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

La ricerca vettoriale opera sulla collection **`chunks`** (non `entries`). Creare l'indice una volta dalla shell di MongoDB:

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
        path: "project"
      }
    ]
  }
)
```

Verifica che lo status sia `READY` prima di usare `/search`, `/chat` e `/agent`:

```javascript
db.chunks.getSearchIndexes()
```