Scaffold un nuovo endpoint FastAPI seguendo il pattern 3-layer del progetto.

## Utilizzo

```
/new-endpoint <NomeRisorsa>
```

Esempio: `/new-endpoint Comment`

## Istruzioni

Leggi prima i file canonici per rispettare esattamente i pattern esistenti:
- @app/routers/entries.py (pattern router)
- @app/services/domain/entry_service.py (pattern service)
- @app/models/entry.py (pattern modelli Pydantic)
- @app/dependencies/auth.py (dipendenze auth disponibili)
- @app/main.py (dove registrare il router)

Poi chiedi all'utente (se non già specificato in $ARGUMENTS):
1. Nome della risorsa (es. `Comment`)
2. Metodi HTTP necessari (GET list, GET by id, POST, PUT, DELETE)
3. Se richiede accesso admin (`require_admin`) o solo autenticazione (`get_current_user`)
4. Se è scoped a un progetto (richiede `verify_project_access`)

Genera i seguenti file:

### `app/models/<resource_lower>.py`
4 modelli Pydantic seguendo la stessa struttura di `app/models/entry.py`:
- `<Resource>Document` — documento MongoDB (con `id: PyObjectId`)
- `<Resource>Create` — body POST
- `<Resource>Update` — body PUT (tutti i campi `Optional`)
- `<Resource>Response` — output API (id come `str`)

### `app/services/domain/<resource_lower>_service.py`
Service con metodi async. Segui `app/services/domain/entry_service.py`:
- Inietta repository via parametro (non singleton)
- Ritorna modelli Response, non Document
- Gestisce solo logica di business — nessun `HTTPException` (quelli vanno nel router)

### `app/routers/<resource_lower>.py`
Router FastAPI seguendo `app/routers/entries.py`:
- `APIRouter` con `prefix` e `tags`
- Dipendenze auth corrette (vedi punto 3 sopra)
- `HTTPException` per 404/403/400
- Type hints su tutti i parametri e return type

### Aggiornamento `app/main.py`
Aggiungi l'import e `app.include_router(...)` nella sezione router esistente.

Dopo aver generato i file, esegui:
```bash
uv run pyright app/
```
e correggi eventuali type error prima di restituire il risultato.
