---
applyTo: "app/*.py"
---

# Backend — Python / FastAPI Rules

## Python Version & Style

- Python 3.11+. Use `match` statements instead of long `if/elif` chains where applicable.
- **Type hints everywhere** — all function parameters and return types. No `Any` unless unavoidable.
- Use f-strings. Never `%` formatting or `.format()`.
- Docstrings in Google style for public functions.
- `pathlib.Path` instead of `os.path`.
- Prefer `dataclasses` or Pydantic models over plain dicts for structured data.

## FastAPI Patterns

**Router structure:** Every router file follows this pattern:
```python
router = APIRouter(prefix="/entries", tags=["entries"])

@router.post("/", response_model=EntryResponse, status_code=201)
async def create_entry(
    body: EntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncMongoClient = Depends(get_db),
) -> EntryResponse:
```

- Always use `Depends()` for auth and DB injection — never instantiate them inside the handler.
- Return Pydantic response models, not raw dicts.
- Use `status_code` explicitly on POST (201) and DELETE (204).
- HTTP exceptions: `raise HTTPException(status_code=404, detail="Entry not found")` — never return error dicts.

**3-layer architecture:** Routers call services; services call DB or AI layers. Never put MongoDB queries directly in routers. Never put FastAPI request/response models in services.

**Async everywhere:** All DB calls, all HTTP calls (Ollama/LiteLLM), all file I/O must be `async/await`. Use `asyncio.gather()` to run independent async operations in parallel.

## MongoDB / PyMongo

- Driver: `AsyncMongoClient` from `pymongo` (Motor is deprecated).
- ObjectIds: convert to `str` in response models. Accept `str` from clients and cast with `ObjectId(id)` in services.
- Always use the `get_db()` dependency — never create a new client per request.
- Index creation: only in `db/indexes.py`, called from lifespan.
- Vector search uses `$vectorSearch` pipeline stage — never do similarity search in Python (that's what mongot is for).

## Pydantic Models

Four-model pattern for every entity:
```
EntityCreate   → POST request body (required fields only)
EntityUpdate   → PUT request body (all fields Optional)
EntityInDB     → MongoDB document (includes embedding, hashed_password, etc.)
EntityResponse → API response (id as str, no secrets, no embedding)
```

`EntityInDB` fields that must never reach the client: `embedding`, `hashed_password`, `vector`.

## Error Handling

```python
# Good — explicit, at the boundary
entry = await entry_service.get_by_id(entry_id)
if entry is None:
    raise HTTPException(status_code=404, detail="Entry not found")

# Bad — silent failure
entry = await entry_service.get_by_id(entry_id)
return entry or {}
```

For AI pipeline failures (LLM, embedding): catch and log, never let them crash the endpoint. Return partial results with a degraded-mode flag if needed.

## Authentication Dependencies

```python
# Standard protected endpoint
current_user: User = Depends(get_current_user)

# Admin-only endpoint
current_user: User = Depends(require_admin)

# Project membership check (returns project doc if user is member)
project: Project = Depends(get_project_member)
```

Never check `current_user.role` inside a handler — use the `require_admin` dependency.

## Testing Conventions

- Use `pytest` with `pytest-asyncio`.
- Mock external calls (LiteLLM, MongoDB) with `pytest-mock`.
- Test files mirror the source structure: `app/services/entry_service.py` → `tests/services/test_entry_service.py`.
- One test file per service/router. Test the public interface, not private helpers.