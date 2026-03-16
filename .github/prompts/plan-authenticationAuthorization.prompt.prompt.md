---
agent: agent
description: "Authentication & Authorization — sviluppa la feature seguendo il piano dettagliato"
---

Leggi il plan qui sotto e inizia ad implementare dalla phase 1, step 1. Procedi step by step seguendo l'ordine indicato, completando ogni step prima di passare al successivo. Se incontri un punto in cui è necessario fare una scelta tecnica, fermati e chiedi istruzioni specifiche su quale opzione preferisco. 

---

# Plan: Authentication & Authorization — MementoAI

**TL;DR:** JWT-based stateless auth su FastAPI (register + login, `get_current_user` dependency su tutti gli endpoint) + login gate nel frontend React. Stack: `passlib[bcrypt]` + `python-jose[cryptography]`, MongoDB raw AsyncMongoClient — nessun ORM, nessun fastapi-users.

---

## Phase 1 — Backend

**Step 1 — `requirements.txt`**
Aggiungere: `PyJWT`, `pwdlib[argon2]`, `python-multipart`

**Step 2 — `app/config.py`**
Aggiungere a `Settings`: `jwt_secret_key: str`, `jwt_algorithm: str = "HS256"`, `access_token_expire_minutes: int = 30`

**Step 3 — `app/models/user.py`** *(parallel con step 4)*
Nuovi modelli: `UserDocument` (interno, include `hashed_password`), `UserCreate` (`email: EmailStr`, `password: str`), `UserResponse` (`id`, `email`, `created_at`), `TokenResponse` (`access_token`, `token_type`)

**Step 4 — `app/db/users_mongo.py`** *(parallel con step 3)*
Raw AsyncMongoClient, stesso stile di `app/db/mongo.py`: `create_user()`, `get_user_by_email()`

**Step 5 — `app/services/auth.py`** *(dipende da 2, 3)*
Funzioni pure: `hash_password()`, `verify_password()` (pwdlib argon2), `create_access_token()`, `decode_access_token()` (PyJWT HS256 + `exp` claim)

**Step 6 — `app/routers/auth.py`** *(dipende da 4, 5)*
- `POST /auth/register` — controlla email unica, hash password, inserisce, ritorna `UserResponse`
- `POST /auth/login` — lookup per email, verifica password, ritorna `TokenResponse`

**Step 7 — `app/dependencies/auth.py`** *(dipende da 5)* — nuova cartella `app/dependencies/`
`OAuth2PasswordBearer(tokenUrl="/auth/login")` + `async def get_current_user(...)` — decodifica JWT, carica utente da DB, 401 se invalido

**Step 8 — Proteggere gli endpoint esistenti** *(dipende da 7)*
Nei 4 router (`entries.py`, `search.py`, `chat.py`, `agent.py`): aggiungere `current_user: UserResponse = Depends(get_current_user)` a ogni endpoint

**Step 9 — `app/main.py` + indice MongoDB** *(dipende da 6)*
Registrare `auth.router` con `prefix="/auth"` + nel blocco `lifespan` aggiungere `create_index("email", unique=True)` sulla collection `users`

---

## Phase 2 — Frontend

**Step 10 — `ui/src/types/index.ts`** *(parallel con step 11)*
Aggiungere `User` e `AuthResponse`

**Step 11 — `ui/src/store/auth.store.ts`** *(parallel con step 10)*
Nuovo Zustand store: `token`, `user`, `setAuth()`, `logout()` — token persistito in `localStorage`

**Step 12 — `ui/src/api/auth.ts`** *(dipende da 10)*
`registerUser()` e `loginUser()` — chiamate senza token (non usano il client autenticato)

**Step 13 — `ui/src/api/client.ts`** *(dipende da 11)*
Modificare `request()`: iniettare `Authorization: Bearer <token>` da `useAuthStore.getState().token`; su 401 chiamare `logout()`

**Step 14 — `LoginPage.tsx` + `RegisterPage.tsx`** *(dipende da 11, 12)*
Nuovi componenti in `ui/src/components/auth/` con shadcn/ui `Input` + `Button`. Toggle via local state tra i due form.

**Step 15 — `ui/src/App.tsx`** *(dipende da 11, 14)*
Auth gate: se `token === null` → `<LoginPage />`, altrimenti layout esistente

---

## File coinvolti

| File | Azione |
|---|---|
| `requirements.txt` | modifica — add `PyJWT`, `pwdlib[argon2]`, `python-multipart` |
| `app/config.py` | modifica |
| `app/models/user.py` | nuovo |
| `app/db/users_mongo.py` | nuovo |
| `app/services/auth.py` | nuovo |
| `app/routers/auth.py` | nuovo |
| `app/dependencies/auth.py` | nuovo (nuova cartella) |
| `app/routers/entries.py`, `chat.py`, `search.py`, `agent.py` | modifica |
| `app/main.py` | modifica |
| `ui/src/types/index.ts` | modifica |
| `ui/src/store/auth.store.ts` | nuovo |
| `ui/src/api/auth.ts` | nuovo |
| `ui/src/api/client.ts` | modifica |
| `ui/src/components/auth/LoginPage.tsx` | nuovo |
| `ui/src/components/auth/RegisterPage.tsx` | nuovo |
| `ui/src/App.tsx` | modifica |

---

## Verifica

1. `POST /auth/register` → 201; duplicato → 400
2. `POST /auth/login` → JWT token
3. `GET /entries` senza token → 401; con token → 200
4. Password errata → 401
5. MongoDB: indice unico su `users.email`; password bcrypt hash in DB (non plaintext)
6. UI: app apre su LoginPage; dopo login → layout principale; refresh → ancora loggato; logout → torna LoginPage

---

## Decisioni

- **`PyJWT` + `pwdlib[argon2]`** — stack raccomandato dalla FastAPI docs aggiornata; `python-jose` e `passlib` escluse perché non più mantenute e con CVE aperte
- **`app/dependencies/`** — nuova cartella per separare i Depends dai service e router
- **`localStorage`** — accettabile in Tauri (no XSS risk da contenuto remoto in webview desktop)
- **Fuori scope**: refresh token, RBAC, isolamento dati per utente, email verification, password reset
