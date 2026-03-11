# MementoAI — UI Restyling Plan

## Riferimento visivo: Raycast / Vercel Dashboard + Dark mode opzionale
## Scope: Redesign completo

---

## Stato attuale (problemi identificati)

| Problema | Causa | Impatto |
|---|---|---|
| Font base 14px | `App.css` | Testo piccolo ovunque |
| Sidebar cramped | `w-56`, `px-3 py-2` | Sensazione datata |
| Zero shadows | Nessun `shadow-*` | Piatto, poco depth |
| Border radius 4px | `rounded` ovunque | Spigoloso |
| Colori hardcoded | Nessun design token | Impossibile cambiare tema |
| Nessun dark mode | — | Mancante |

---

## Fase 1 — Design Tokens (prerequisito di tutte le fasi)

**`App.css`** — definire CSS variables e Tailwind v4 dark mode:

```
--bg: #FFFFFF             dark: #0C0C0C
--bg-subtle: #F7F7F8      dark: #141414
--bg-hover: #F0F0F1       dark: #1E1E1E
--border: rgba(0,0,0,.08) dark: rgba(255,255,255,.08)
--text: #0A0A0A           dark: #FAFAFA
--text-muted: #6B7280     dark: #8B8B8B
--accent: #6366F1         dark: #818CF8
--accent-hover: #4F46E5   dark: #6366F1
--shadow-sm, --shadow-md, --shadow-lg
```

- Dark mode via `@custom-variant dark (&:where(.dark, .dark *))` + classe `.dark` su `<html>`
- Font base: 15px
- Rimpiazzare tutti gli usi diretti di `#FAFAFA`, `#1A1A1A`, `#E5E5E5`, `#6B7280` con riferimenti alle variabili

---

## Fase 2 — Layout Shell *(dipende da Fase 1)*

**`App.tsx`** — montare `ThemeToggle`, applicare classe `dark` su `<html>` al cambio tema

**`ThemeToggle.tsx`** (NEW) — bottone `Sun/Moon` da `lucide-react`, persiste in `localStorage`

**`Sidebar.tsx`** — nuove classi:
- Larghezza `w-64` (invece di `w-56`)
- Background `bg-[--bg-subtle]`
- Header: `px-4 py-3`, font brand `text-sm font-semibold tracking-tight`
- Project pills: `rounded-lg`, `hover:bg-[--bg-hover]`, `px-3 py-1.5`, `text-sm`
- Sezioni separate da `border-[--border]`
- Footer: `px-4 py-3`

**`MainPanel.tsx`** — redesign top bar:
- Altezza `h-12` (invece di `h-10`)
- Background `bg-[--bg]`, `border-b border-[--border]`
- `ThemeToggle` a destra nella top bar
- Placeholder state più moderna

---

## Fase 3 — Entry List *(parallela con Fase 4)*

**`EntryListItem.tsx`**:
- Padding `px-4 py-2.5` (era `px-3 py-2`)
- Titolo `text-sm` (era `text-xs font-medium`)
- Autore/progetto `text-xs` (era `text-[11px]`)
- Hover background `hover:bg-[--bg-hover]`
- Trash icon: sempre visibile su active, visibile su hover per gli altri

**`EntryTypeBadge.tsx`**:
- `rounded-full`, `text-[11px] font-medium px-2 py-0.5`
- Badge colors più saturate e moderne

**`EntryList.tsx`**:
- Skeleton con le nuove misure

---

## Fase 4 — Editor Area *(parallela con Fase 3)*

**`EntryMeta.tsx`**:
- Titolo: `text-3xl` (era `text-2xl`)
- Tag pills: `rounded-full bg-[--bg-hover]`, stile più moderno
- Summary textarea: `rounded-lg`, `bg-[--bg-subtle]`
- Spacing tra sezioni: `gap-4` (era `gap-3`)

**`EditorToolbar.tsx`**:
- Pulsanti come gruppo pill: `rounded-lg`, sfondo `bg-[--bg-subtle]`, `gap-0`
- Divider con `bg-[--border]`
- Bottone Delete iconicamente separato a destra

**`EntryEditor.tsx`**:
- Stili TipTap aggiornati: `h1` → `text-2xl`, `h2` → `text-xl`, code block più moderno
- Padding editor: `px-10 py-10` (era `px-8 py-8`)

---

## Fase 5 — Chat & Search *(parallela con Fasi 3 e 4)*

**`ChatDrawer.tsx`**: shadow `shadow-2xl`, `rounded-l-2xl`, `bg-[--bg]`, header più alta (`py-3`)

**`ChatMessage.tsx`**:
- User: `bg-[--accent] text-white rounded-2xl rounded-br-sm`
- AI: `bg-[--bg-hover] rounded-2xl rounded-bl-sm`
- Padding `px-4 py-2.5`

**`ChatInput.tsx`**: `rounded-xl`, `bg-[--bg-subtle]`, bordo accent on focus

**`SearchBar.tsx`**: `h-8 rounded-lg`, `bg-[--bg-subtle]`

**`SearchResults.tsx`**: card con `rounded-xl shadow-sm`, `hover:shadow-md transition`

---

## Fase 6 — Dialogs & Polish *(dipende da tutte le fasi)*

**`NewEntryDialog.tsx`**: input `rounded-lg`, spacing `gap-5`, dialog più ampio `sm:max-w-lg`

**`AlertDialog`**: pulsante Elimina con stile coerente

Micro-animazioni: `transition-colors duration-150` sui hover (già parzialmente presenti)

---

## File modificati

- `src/App.css` — design tokens, dark mode variant, font base
- `src/App.tsx` — dark mode logic
- `src/components/layout/ThemeToggle.tsx` — NEW
- `src/components/layout/Sidebar.tsx`
- `src/components/layout/MainPanel.tsx`
- `src/components/entries/EntryList.tsx`
- `src/components/entries/EntryListItem.tsx`
- `src/components/entries/EntryTypeBadge.tsx`
- `src/components/editor/EntryEditor.tsx`
- `src/components/editor/EntryMeta.tsx`
- `src/components/editor/EditorToolbar.tsx`
- `src/components/chat/ChatDrawer.tsx`
- `src/components/chat/ChatMessage.tsx`
- `src/components/chat/ChatInput.tsx`
- `src/components/chat/ChatHistory.tsx`
- `src/components/search/SearchBar.tsx`
- `src/components/search/SearchResults.tsx`
- `src/components/entries/NewEntryDialog.tsx`

---

## Verifica

1. `tsc --noEmit` — zero errori
2. Visivamente: testo leggibile a 15px base, sidebar spaziosa a 256px, shadows su dialogs e drawer
3. Dark mode: toggle Sun/Moon nella top bar, persistenza dopo refresh (localStorage)
4. Nessuna regressione funzionale (autosave, index, delete, search, chat)
5. Eseguire: [code-review-cleanup](./code-review-cleanup.prompt.md)

---

## Decisioni

- **Accento indigo** (`#6366F1`) — unico colore "vivo"; tutto il resto rimane neutro (come Vercel)
- **Dark mode class-based** (`.dark` su `<html>`) — non `prefers-color-scheme`, per dare controllo esplicito all'utente
- **No glassmorphism** — blur/frosted glass non incluso nel piano base
- **Animazioni conservative** — solo `transition-colors duration-150`, nessun animazione di layout
- **Shadcn components**: non vengono riscritti, si sovrascrivono solo via `className` inline

---

## Note

1. **Migrazione colori hardcoded**: tutti i `#FAFAFA`, `#1A1A1A`, `#E5E5E5`, `#6B7280` vanno sostituiti con le variabili CSS — è il lavoro più ripetitivo. Le Fasi 2-6 dipendono dalla Fase 1 ma non bloccano ulteriori discussioni.
2. **Dark mode e shadcn/ui**: i componenti shadcn usano già variabili CSS (`--background`, `--foreground`, ecc.) internamente. Potrebbe essere necessario allineare i nuovi token al sistema di shadcn per evitare conflitti.
3. **Scope incrementale**: le Fasi 3, 4 e 5 sono indipendenti tra loro e possono essere eseguite in parallelo — oppure iterativamente se si vuole validare il risultato fase per fase.
