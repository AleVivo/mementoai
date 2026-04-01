Diagnosi guidata di un bug con contesto architetturale MementoAI.

## Istruzioni

Se l'utente non ha già specificato area e sintomi in $ARGUMENTS, chiedi:
1. **Area**: backend / frontend / ai-pipeline / auth
2. **Sintomi**: cosa succede, cosa ti aspettavi, eventuale errore/stacktrace

Poi segui il processo di diagnosi per l'area indicata.

---

## Backend (`app/`)

Leggi i file rilevanti prima di proporre fix:
- @app/routers/ — il router dell'endpoint coinvolto
- @app/services/domain/ — il service corrispondente
- @app/db/repositories/ — il repository coinvolto
- @app/dependencies/auth.py — se il problema riguarda auth/permessi

**Trappole comuni da verificare per prime:**

1. **`vector_status` non aggiornato** — dopo `PUT /entries/:id` deve essere `"outdated"`. Cerca:
   ```bash
   grep -n "vector_status" app/routers/entries.py app/services/domain/entry_service.py
   ```

2. **ObjectId non convertito** — MongoDB ritorna `ObjectId`, l'API deve ritornare `str`. Cerca:
   ```bash
   grep -n "_id\|ObjectId\|PyObjectId" app/routers/ app/services/domain/ -r
   ```

3. **Motor invece di AsyncMongoClient** — deve essere `from pymongo import AsyncMongoClient`:
   ```bash
   grep -rn "import motor\|from motor" app/
   ```

---

## Frontend (`ui/src/`)

Leggi i file rilevanti prima di proporre fix:
- @ui/src/api/ — il modulo API coinvolto
- @ui/src/store/ — lo store Zustand coinvolto
- @ui/src/hooks/ — l'hook coinvolto
- @ui/src/api/client.ts — se il problema riguarda auth/request

**Trappole comuni da verificare per prime:**

1. **Autosave che chiama `/index`** — l'autosave (debounce 1.5s) deve chiamare solo `PUT /entries/:id`:
   ```bash
   grep -n "index\|Index" ui/src/hooks/useEntries.ts ui/src/components/editor/EntryEditor.tsx
   ```

2. **Token non refreshato** — 401 non gestito silenziosamente. Controlla:
   ```bash
   grep -n "401\|refresh\|token" ui/src/api/client.ts
   ```

3. **`vector_status` non aggiornato localmente** — dopo save deve essere `"outdated"` nello store:
   ```bash
   grep -n "vector_status\|outdated" ui/src/store/entries.store.ts ui/src/hooks/useEntries.ts
   ```

---

## AI pipeline (`app/services/ai/`, `retrieval/`, `ingestion/`)

Leggi i file rilevanti prima di proporre fix:
- @app/services/ai/rag_service.py
- @app/services/ai/sse.py
- @app/services/llm/provider_cache.py
- @app/services/ai/agent_state.py (se riguarda l'agent)

**Trappole comuni da verificare per prime:**

1. **LLM chiamato direttamente** — mai fuori da `provider_cache.py`:
   ```bash
   grep -rn "LiteLLM\|ChatOllama\|OpenAI(" app/services/ai/ app/services/retrieval/ app/services/ingestion/
   ```

2. **SSE non separato dalla logica AI** — `@observe` e `AsyncGenerator` non sono compatibili:
   ```bash
   grep -n "@observe\|async def stream\|AsyncGenerator" app/services/ai/rag_service.py app/services/ai/agent_service.py
   ```

3. **`project_ids` passato come argomento LLM** — deve essere in `InjectedState`:
   ```bash
   grep -n "project_ids" app/services/ai/agent_tools.py app/services/ai/agent_state.py
   ```

---

Dopo la diagnosi: proponi il fix con il codice corretto e applica direttamente se l'utente non specifica diversamente.
