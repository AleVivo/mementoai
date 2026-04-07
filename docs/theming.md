---
generated_by: GitHub Copilot (GPT-5.3-Codex)
last_updated: 2026-04-07
---
# MementoAI — Guida al Theming

Tutto il sistema di colori è centralizzato in un unico file: `ui/src/App.css`.
Per cambiare tema basta modificare le variabili CSS in quel file — nessuna altra modifica è necessaria.

## Struttura del sistema

```
App.css
 ├── :root { ... }        ← token light mode
 ├── .dark { ... }        ← token dark mode
 └── @theme inline { ... } ← espone i token come classi Tailwind
```

Il dark mode è attivato aggiungendo la classe `.dark` su `document.documentElement`
(gestito da `ui/src/components/layout/ThemeToggle.tsx`).

---

## Token semantici personalizzati

Questi token sono definiti nel blocco `:root` / `.dark` di `App.css` e usati direttamente
nei componenti tramite la sintassi `var(--nome-token)` o come classi Tailwind `text-[var(--nome-token)]`.

### Layout e struttura

| Token | Light | Dark | Uso |
|---|---|---|---|
| `--bg-subtle` | `#F7F7F8` | `#141414` | Sfondi secondari, aree input, sidebar |
| `--bg-hover` | `#F0F0F1` | `#1E1E1E` | Hover su elementi interattivi |
| `--border-ui` | `rgba(0,0,0,0.08)` | `rgba(255,255,255,0.08)` | Bordi di separazione |
| `--text-muted-ui` | `#6B7280` | `#8B8B8B` | Testo secondario, placeholder |
| `--accent-ui` | `#6366F1` | `#818CF8` | Accento primario (indigo) |
| `--accent-hover-ui` | `#4F46E5` | `#6366F1` | Accento hover |
| `--shadow-sm/md/lg` | valori chiari | valori scuri | Ombre componenti |

### Colori entry type

I badge `ADR`, `PM`, `UPD`, `OTH` leggono questi token.
Cambiando i valori qui il badge si aggiorna in tutta l'app.

| Token | Light | Dark |
|---|---|---|
| `--color-adr` | `#3B82F6` (blue-500) | `#60a5fa` (blue-400) |
| `--color-adr-bg` | `#dbeafe` (blue-100) | `rgba(59,130,246,0.15)` |
| `--color-postmortem` | `#D97706` (amber-600) | `#fbbf24` (amber-400) |
| `--color-postmortem-bg` | `#fef3c7` (amber-100) | `rgba(245,158,11,0.15)` |
| `--color-update` | `#16A34A` (green-600) | `#4ade80` (green-400) |
| `--color-update-bg` | `#dcfce7` (green-100) | `rgba(34,197,94,0.15)` |
| `--color-other` | `#6B7280` (gray-500) | `#9ca3af` (gray-400) |
| `--color-other-bg` | `#f3f4f6` (gray-100) | `rgba(107,114,128,0.2)` |

### Status colors

Usati per stati di indicizzazione, messaggi di errore, badge stato provider.

| Token | Light | Dark | Uso |
|---|---|---|---|
| `--color-success` | `#16A34A` | `#4ade80` | "Indicizzato", provider attivo |
| `--color-success-bg` | `#dcfce7` | `rgba(74,222,128,0.1)` | Badge "attivo" admin |
| `--color-warning` | `#D97706` | `#fbbf24` | "Non indicizzato", "In attesa" |
| `--color-warning-bg` | `#fef3c7` | `rgba(251,191,36,0.1)` | Badge warning |
| `--color-error` | `#ef4444` | `#f87171` | Errori form, badge "errore", asterischi required |
| `--color-error-bg` | `#fee2e2` | `rgba(239,68,68,0.1)` | Badge "errore" admin |
| `--color-destructive-hover-bg` | `#fef2f2` | `rgba(239,68,68,0.15)` | Hover su icon button delete |

---

## Token shadcn/ui (OKLCH)

Questi token sono usati dai componenti shadcn (`Button`, `Dialog`, `Select`, ecc.).
Sono definiti anch'essi in `:root` / `.dark` di `App.css` e esposti in `@theme inline`
come classi Tailwind (`bg-background`, `text-foreground`, `bg-destructive`, ecc.).

| Token | Uso |
|---|---|
| `--background` / `--foreground` | Colore base pagina e testo |
| `--card` / `--card-foreground` | Card e dialog |
| `--primary` / `--primary-foreground` | Pulsante primario |
| `--destructive` / `--destructive-foreground` | Pulsante distruttivo (elimina) |
| `--muted` / `--muted-foreground` | Aree muted, testo secondario shadcn |
| `--border` | Bordi shadcn |
| `--radius` | Raggio di base (moltiplicato in `--radius-sm` … `--radius-4xl`) |

---

## Come cambiare il tema

### Cambiare il colore accent (indigo → altro)

```css
/* App.css — :root */
--accent-ui: #0ea5e9;        /* sky-500 */
--accent-hover-ui: #0284c7;  /* sky-600 */

/* App.css — .dark */
--accent-ui: #38bdf8;        /* sky-400 */
--accent-hover-ui: #0ea5e9;  /* sky-500 */
```

Cambia anche il colore primario shadcn (pulsante principale, ring di focus):
```css
/* :root */
--primary: oklch(0.60 0.19 220);   /* sky — calcola con oklch.com */

/* .dark */
--primary: oklch(0.68 0.17 220);
```

### Cambiare i colori dei badge entry type

```css
/* Es: rendere ADR viola invece di blu */
--color-adr: #7c3aed;          /* violet-600 */
--color-adr-bg: #ede9fe;       /* violet-100 */

/* dark */
--color-adr: #a78bfa;          /* violet-400 */
--color-adr-bg: rgba(124,58,237,0.15);
```

### Aggiungere un nuovo tipo di entry

1. Aggiungere il tipo in `ui/src/types/index.ts`:
   ```ts
   export type EntryType = 'adr' | 'postmortem' | 'update' | 'other' | 'nuovotipo';
   ```
2. Aggiungere i token in `App.css`:
   ```css
   /* :root */
   --color-nuovotipo: #0d9488;
   --color-nuovotipo-bg: #ccfbf1;

   /* .dark */
   --color-nuovotipo: #2dd4bf;
   --color-nuovotipo-bg: rgba(13,148,136,0.15);
   ```
3. Aggiungere la voce in `EntryTypeBadge.tsx`:
   ```ts
   nuovotipo: { label: "NEW", colorVar: "--color-nuovotipo", bgVar: "--color-nuovotipo-bg" },
   ```

### Cambiare il raggio di arrotondamento globale

```css
/* :root */
--radius: 0.375rem;   /* più squadrato */
/* oppure */
--radius: 0.875rem;   /* più arrotondato */
```

Tutti i componenti che usano `--radius-sm/md/lg/xl` si adatteranno automaticamente.

---

## Pattern di utilizzo nei componenti

```tsx
// ✅ CORRETTO — usa il token CSS
<p className="text-[var(--color-error)]">Errore</p>
<div className="bg-[var(--bg-subtle)] border border-[var(--border-ui)]">...</div>
<span style={{ color: "var(--color-adr)", backgroundColor: "var(--color-adr-bg)" }}>ADR</span>

// ✅ CORRETTO — usa token shadcn esposti come classe Tailwind
<button className="bg-destructive hover:bg-destructive/90 text-destructive-foreground">Elimina</button>
<div className="bg-background text-foreground">...</div>

// ❌ EVITARE — colori hardcoded non tematizzabili
<p className="text-red-500">Errore</p>
<div className="bg-gray-100 dark:bg-gray-800">...</div>
```

---

## File di riferimento

| File | Ruolo |
|---|---|
| `ui/src/App.css` | **Unico punto di verità** per tutti i token |
| `ui/src/components/layout/ThemeToggle.tsx` | Logica attivazione dark mode |
| `ui/index.html` | Script anti-flash: legge `localStorage.theme` e applica `.dark` prima del render |
| `ui/src/components/entries/EntryTypeBadge.tsx` | Esempio di utilizzo token entry type |
| `ui/src/components/editor/EntryMeta.tsx` | Esempio di utilizzo token status |
