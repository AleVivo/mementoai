---
name: backend-patterns
description: Pattern FastAPI/MongoDB per file in app/ — 3-layer, auth deps, AsyncMongoClient, modelli Pydantic
type: project
---

# Backend Patterns — MementoAI

Si attiva automaticamente quando lavori su file in `app/`.

## Pattern 3-layer

```
router (app/routers/)
  └─ chiama service (app/services/domain/)
       └─ chiama repository (app/db/repositories/)
            └─ AsyncMongoClient → MongoDB
```

- **Router**: gestisce HTTP, dipendenze FastAPI, `HTTPException`. Nessuna logica di business.
- **Service**: logica di business, trasforma Document → Response. Nessun `HTTPException`.
- **Repository**: query MongoDB, ritorna dict o Document. Nessuna logica.

File canonici: @app/routers/entries.py | @app/services/domain/entry_service.py | @app/db/repositories/entry_repository.py

## Dipendenze auth

Tutte disponibili in @app/dependencies/auth.py:

```python
from app.dependencies.auth import get_current_user, require_admin
from app.dependencies.entries import verify_entry_access
from app.dependencies.project import verify_project_access

# Endpoint autenticato
@router.get("/{id}")
async def get_item(current_user = Depends(get_current_user)): ...

# Solo admin
@router.put("/config")
async def update_config(current_user = Depends(require_admin)): ...
```

## MongoDB — AsyncMongoClient (NON Motor)

```python
# CORRETTO
from pymongo import AsyncMongoClient

# SBAGLIATO — Motor è deprecato dal 14/05/2025
from motor.motor_asyncio import AsyncIOMotorClient  # NON usare
```

La connessione è centralizzata in @app/db/client.py.

## ObjectId ↔ str

MongoDB usa `ObjectId`, l'API espone `str`. Conversione tramite `PyObjectId` in @app/models/types.py.

```python
# Nel modello Response: id è str
class EntryResponse(BaseModel):
    id: str
    ...

# Nel mapper: converti _id
def to_response(doc: dict) -> EntryResponse:
    return EntryResponse(id=str(doc["_id"]), ...)
```

## 4 modelli Pydantic per entity

Segui lo schema di @app/models/entry.py:

| Modello | Uso | Campi id |
|---|---|---|
| `<Resource>Document` | Storage MongoDB | `id: PyObjectId = Field(alias="_id")` |
| `<Resource>Create` | Body POST | nessun id |
| `<Resource>Update` | Body PUT | tutti `Optional`, nessun id |
| `<Resource>Response` | Output API | `id: str` |

## Gestione errori

```python
# Nel router — HTTPException qui, non nel service
if not entry:
    raise HTTPException(status_code=404, detail="Entry not found")

# Nel service — ritorna None o lancia eccezioni di dominio custom
async def get_entry(id: str) -> EntryResponse | None:
    doc = await self.repo.find_by_id(id)
    return to_response(doc) if doc else None
```

## Nota critica: vector_status

Dopo ogni `PUT /entries/:id`, il service deve aggiornare `vector_status = "outdated"`.
Il valore NON diventa `"pending"` automaticamente — solo la chiamata a `/index` avvia il pipeline.
