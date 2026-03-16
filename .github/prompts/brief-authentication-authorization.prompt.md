---
agent: Plan
description: "Authentication & Authorization — genera il piano di sviluppo dal brief"
---

Leggi il brief qui sotto e produci un piano di sviluppo dettagliato per MementoAI (backend FastAPI + frontend React/Tauri), con task suddivisi per area, dipendenze e ordine di implementazione.

---

# MementoAI — Authentication & Authorization

## Context

MementoAI is a local-first knowledge base app for small dev teams. The backend is built with FastAPI + PyMongo async (AsyncMongoClient, no ODM) + MongoDB. All existing endpoints are currently unprotected.

The project is moving toward a multi-user / SaaS deployment, so authentication needs to be implemented correctly from the start — user identity must be a first-class concept in the data model.

## Goal

Add authentication and authorization to the FastAPI backend so that:

- Users can register and log in
- Every existing API endpoint requires a valid authenticated session
- User identity is available on every request for future use (e.g. per-user data isolation, memory layer)

## Hard Constraints

- **Do not introduce any ORM or ODM** (no Beanie, no SQLAlchemy). All MongoDB access must stay as raw AsyncMongoClient calls, consistent with the existing codebase.
- **Do not use fastapi-users** — it is in maintenance mode and requires Beanie.
- Use only libraries that are actively maintained and recommended by the official FastAPI documentation.
- Registration must be open (anyone can create an account).
- The implementation must be stateless (no server-side sessions).

## What is out of scope for this iteration

- Per-user data isolation (entries are still readable by all authenticated users for now)
- Password reset or email verification
- Role-based access control