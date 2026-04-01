---
applyTo: "ui/**/*.{ts,tsx}"
---

# Frontend — React 19 / TypeScript / Tauri Rules

## TypeScript

- `strict: true` always. No `any`, no `as unknown as X` unless there is a comment explaining why.
- Mirror backend Pydantic models exactly in `ui/src/types/index.ts`. When the backend adds a field, add it here too.
- Use `type` for union types and object shapes. Use `interface` only when you need declaration merging (rare).
- Prefer `const` everywhere. `let` only when reassignment is unavoidable.

## React 19 Patterns

- Functional components only. No class components.
- Hooks at the top of the component, in this order: `useState`, `useEffect`, `useRef`, custom hooks, store hooks.
- No inline arrow functions in JSX for event handlers that do more than one thing — extract a named handler.
- Keep components under ~150 lines. Split into sub-components early.
- `key` props must be stable IDs (MongoDB ObjectId strings), never array indices.

```tsx
// Good
const handleSave = async () => {
  setIsSaving(true);
  await entriesApi.update(entry.id, draft);
  setIsSaving(false);
};
<button onClick={handleSave}>Save</button>

// Bad
<button onClick={async () => { setIsSaving(true); await entriesApi.update(...); }}>Save</button>
```

## Zustand Store Rules

Four stores, strict boundaries:
- `entries.store.ts` — entry list and active entry data
- `projects.store.ts` — project list
- `ui.store.ts` — UI state (open/closed, dirty, saving, indexing, chatMode, isAdminOpen)
- `auth.store.ts` — token, refreshToken, user (persisted to localStorage)
- `chat.store.ts` — messages keyed by projectId (`"__all__"` for global scope)

Never put API calls inside a store. Stores hold state and expose actions; hooks (`useEntries`, `useChat`, etc.) orchestrate the API calls and store updates.

## API Client

All HTTP calls go through `ui/src/api/client.ts`. The client:
- Injects `Authorization: Bearer <token>` on every request.
- On 401: attempts silent refresh (singleton promise to avoid thundering herd).
- On refresh failure: calls `logout()` and redirects.

Never use `fetch` directly in a component or store — always import from `ui/src/api/`.

SSE streams (chat, agent) use the same auth injection pattern — see `ui/src/api/chat.ts`.

## TailwindCSS

- Utility classes only. No custom CSS files, no `style={{}}` props except for truly dynamic values (e.g., calculated widths).
- Use `shadcn/ui` components as the base. Extend with Tailwind utilities, don't override with CSS.
- Color palette: follow the existing Notion-like minimal design — neutral grays, amber for warnings, green for success.
- Responsive: `sm:` prefix for anything that should differ on smaller windows. Min window: 1024px.

## Vector Status Badge Pattern

The `vector_status` field drives UI state in the editor toolbar. Always use this mapping:
```
pending   → ⚠ In attesa (amber)
outdated  → ⚠ Non indicizzato (amber)
indexing  → ⟳ Indicizzazione... (spinner, button disabled)
indexed   → ✓ Indicizzato (green, disappears after 3s)
```

## Save vs Index — Critical Distinction

**Save** (`PUT /entries/:id`): triggered by autosave (1.5s debounce) or Cmd+S. No LLM. Fast. Sets `isDirty = false`, `isSaving` spinner. Backend sets `vector_status = "outdated"`.

**Index** (`POST /entries/:id/index`): triggered only by the `[Indicizza]` button. Calls the AI pipeline. Sets `isIndexing = true`. Button is disabled while indexing.

Never conflate these two operations in the UI.

## Keyboard Shortcuts

Registered globally in `useKeyboardShortcuts.ts`:
- `Cmd/Ctrl+S` → immediate save
- `Cmd/Ctrl+K` → open search
- `Cmd/Ctrl+J` → toggle chat panel
- `Cmd/Ctrl+N` → new entry dialog

Don't add new global shortcuts without updating this hook.

## Tauri-Specific

- HTTP `fetch` to `localhost:8000` is allowed (configured in `tauri.conf.json` CSP).
- Do not use Node.js APIs — Tauri's WebView runs in a browser context.
- For desktop features (file system, shell), use `@tauri-apps/api` — never bypass it.
