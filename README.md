# Memento

Knowledge base conversazionale per team di sviluppo piccoli. Permette di catturare decisioni tecniche, post-mortem e aggiornamenti di progetto, rendendoli recuperabili tramite ricerca semantica e chat in linguaggio naturale.

---

## Prerequisiti

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) — package manager Python
- [Ollama](https://ollama.com/) in esecuzione su `localhost:11434`
- MongoDB 8.2+ configurato come replica set (richiesto per `$vectorSearch`)

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

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Il flag `--reload` riavvia il server automaticamente ad ogni modifica del codice — utile in sviluppo, da rimuovere in produzione.

L'API è disponibile su:
- **Base URL:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Struttura del progetto

```
MementoAI/
├── app/
│   ├── main.py           # FastAPI entrypoint + lifespan
│   ├── config.py         # Settings con pydantic-settings
│   ├── models/           # Modelli Pydantic (EntryCreate, EntryInDB, EntryResponse, SearchResult)
│   ├── routers/          # Endpoint API (entries, search, chat)
│   ├── services/         # Logica di business (ollama, classifier, embedding, rag)
│   └── db/               # Connessione e query MongoDB
├── .env                  # NON committare — variabili locali
├── .env.example          # Template variabili d'ambiente
├── pyproject.toml        # Dipendenze e metadati progetto
└── uv.lock               # Lockfile versioni esatte
```

---

## Endpoint principali

| Metodo | Endpoint | Descrizione |
|---|---|---|
| `POST` | `/entries` | Crea una nuova entry (genera summary e embedding via Ollama) |
| `GET` | `/entries` | Lista entries con filtri (`project`, `type`, `week`, `limit`, `skip`) |
| `GET` | `/entries/{id}` | Singola entry per ID |
| `PUT` | `/entries/{id}` | Aggiorna entry (ricalcola embedding se `raw_text` cambia) |
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