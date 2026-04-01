# MementoAI — GitHub Copilot Instructions

## Project Overview

MementoAI is a **local-first** knowledge base for dev teams. Architecture: Tauri v2 desktop shell → React 19 frontend → FastAPI backend → MongoDB + LiteLLM + LlamaIndex + LangGraph.

The repo is organized as a monorepo:
- `app/` — FastAPI Python app (`app/`)
- `ui/` — Tauri + React frontend (`ui/src/`)

## Non-Obvious Project Decisions (read before generating code)

**PyMongo AsyncMongoClient, NOT Motor.** Motor was deprecated on 14/05/2025. Use `from pymongo import AsyncMongoClient`.

**No AI on save.** `PUT /entries/:id` is a pure DB write. The LLM pipeline runs only on `POST /entries/:id/index`. Never add LLM calls to save/autosave flows.

**Vector status lifecycle:** `pending` → (user clicks Indicizza) → `indexed`. After any content PUT, set `vector_status = "outdated"`. The field lives on the Entry document.

**LLM provider is runtime-configurable.** Never hardcode `ollama` or model names. All LLM/embedding calls go through `services/llm/provider_cache.py` singletons. Use `Settings.llm` and `Settings.embed_model` from LlamaIndex settings, which are wired by `handlers/config_handlers.py` at startup.

**Secrets are Fernet-encrypted in MongoDB.** `config_values` stores encrypted secrets. Use `utils/encryption.py` — never read secrets directly from the DB without decrypting.

**Auth is stateless JWT.** No sessions. `get_current_user()` dependency decodes the token. `require_admin()` checks `role == "admin"`. Project access uses membership check via `project_members` collection.

**LlamaIndex pipeline for indexing.** Chunking is hierarchical: 2048 / 512 / 128 tokens via `HierarchicalNodeParser`. Only leaf nodes (128 token) are embedded. `AutoMergingRetriever` promotes leaf clusters back to parent nodes at query time.

**SSE streaming separation pattern.** RAG and agent services separate AI logic from SSE transport because `@observe` (Langfuse) does not support `AsyncGenerator`. The pattern: `_execute_rag()` returns the AI result, `stream_rag()` wraps it as SSE.

## Code Style — All Files

- Prefer explicit over implicit. Name things after what they do, not what they are.
- No magic numbers. Use named constants or config values.
- Handle errors at the boundary, not deep in the call stack.
- When in doubt, write a comment explaining *why*, not *what*.

## Commit Message Format

```
type(scope): short description

type: feat | fix | refactor | test | docs | chore
scope: backend | frontend | ai | auth | infra
```