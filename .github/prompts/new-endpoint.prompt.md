---
agent: agent
description: "Scaffold a complete new FastAPI endpoint following MementoAI patterns"
tools: ["search/codebase", "vscode/askQuestions"]
---

# New FastAPI Endpoint

Ask me the following before generating anything:
1. What is the **resource name**? (e.g., "tags", "comments")
2. What **HTTP methods** are needed? (GET list / GET by id / POST / PUT / DELETE)
3. Does it require **authentication**? If yes, is it user-level or admin-only?
4. Does it require **project membership check**?
5. Does any operation trigger the **AI pipeline** (LLM or embedding)?

Once you have the answers, generate:

## Files to create or modify

**`app/routers/{resource}.py`**
- Import `APIRouter`, `Depends`, `HTTPException`
- Use `get_current_user` or `require_admin` dependency from `app/dependencies/auth.py`
- No MongoDB queries here — delegate to the service layer
- Match the 3-layer pattern from `app/routers/entries.py`

**`app/services/domain/{resource}_service.py`**
- All business logic and DB calls here
- Return Pydantic models, not raw dicts or MongoDB documents
- Handle `ObjectId` ↔ `str` conversion here, not in the router

**`app/models/{resource}.py`**
- Four models: `{Resource}Create`, `{Resource}Update`, `{Resource}Document`, `{Resource}Response`
- `Document` contains all DB fields including any fields that must never reach the client
- `Response` contains `id: str` (converted from ObjectId)

**`app/main.py`** (modify)
- Register the new router: `app.include_router({resource}.router)`

**`app/db/indexes.py`** (modify if new indexes are needed)
- Add index creation for any new fields that will be queried or sorted

After generating, remind me to:
- Add the endpoint to the architecture diagram in `architecture.md`
- Add the TypeScript type to `ui/src/types/index.ts`
- Add the API function to the appropriate `ui/src/api/*.ts` file
