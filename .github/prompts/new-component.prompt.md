---
agent: agent
description: "Scaffold a new React component following MementoAI UI patterns"
tools: ["search/codebase", "vscode/askQuestions"]
---

# New React Component

Ask me the following before generating anything:
1. What is the **component name**? (PascalCase)
2. Where does it live? (`layout/` | `editor/` | `entries/` | `projects/` | `search/` | `chat/` | `admin/`)
3. Does it need **Zustand store access**? Which stores?
4. Does it make **API calls**? Which endpoints?
5. Is it a **dialog/drawer** (modal) or an inline component?
6. Does it handle **SSE streaming** (chat responses)?

Once you have the answers, generate:

## Component file: `ui/src/components/{folder}/{ComponentName}.tsx`

Follow these patterns exactly:

**Imports order:**
```tsx
// 1. React
import { useState, useEffect, useRef } from 'react';
// 2. External libs (shadcn, lucide, etc.)
import { Button } from '@/components/ui/button';
// 3. Internal types
import type { Entry } from '@/types';
// 4. Store hooks
import { useUIStore } from '@/store/ui.store';
// 5. API functions
import { entriesApi } from '@/api/entries';
```

**Component structure:**
- Props interface above the component (not inline)
- Named handlers (not inline arrow functions in JSX)
- Loading and error states where the component makes async calls
- No business logic in the JSX return — extract to handlers

**If it's a dialog/drawer:**
- Use `shadcn/ui` `Dialog` or `vaul` `Drawer` as the base
- Controlled open state via `ui.store.ts` (e.g., `isNewEntryOpen`)
- Always provide a close handler that resets form state

**If it handles SSE streaming:**
- Use `ReadableStream` from the fetch response
- Update state token-by-token: `setContent(prev => prev + token)`
- Show a streaming indicator while `isStreaming === true`

## After generating

Check:
- [ ] Is the component exported as a named export?
- [ ] Is it added to the parent component that uses it?
- [ ] If it introduces a new Zustand state field, is `ui.store.ts` updated?
- [ ] If it adds a keyboard shortcut, is `useKeyboardShortcuts.ts` updated?
