Scaffold un nuovo componente React seguendo i pattern di ui/src/.

## Utilizzo

```
/new-component <NomeComponente>
```

Esempio: `/new-component CommentList`

## Istruzioni

Leggi prima i file canonici per rispettare esattamente i pattern esistenti:
- @ui/src/components/editor/EntryEditor.tsx (pattern componente complesso)
- @ui/src/hooks/useEntries.ts (pattern hook con store + API)
- @ui/src/api/entries.ts (pattern API client)
- @ui/src/api/client.ts (fetch wrapper con auth)
- @ui/src/store/entries.store.ts (pattern Zustand store)
- @ui/src/types/index.ts (tipi TypeScript disponibili)

Poi chiedi all'utente (se non già specificato in $ARGUMENTS):
1. Nome del componente (PascalCase)
2. Dominio di appartenenza (editor, chat, entries, projects, admin, layout, search)
3. Ha bisogno di chiamate API? Se sì, quale endpoint
4. Ha bisogno di stato locale/globale? Se globale, quale store
5. Ha keyboard shortcuts? (vedi @ui/src/hooks/useKeyboardShortcuts.ts)

Genera i seguenti file (solo quelli necessari):

### `ui/src/components/<domain>/<Name>.tsx`
- Props tipizzate con `interface <Name>Props`
- Usa i tipi da `@ui/src/types/index.ts`
- Import da shadcn/ui se servono elementi UI standard
- Nessun `fetch` diretto — usa sempre il client in `@ui/src/api/client.ts`

### `ui/src/hooks/use<Name>.ts` (solo se serve logica con stato o API)
- Segui la struttura di `useEntries.ts`
- Legge dallo store Zustand appropriato
- Espone solo le funzioni e i dati necessari al componente

### `ui/src/api/<resource>.ts` (solo se serve un nuovo modulo API)
- Segui la struttura di `entries.ts`
- Usa `apiClient` da `client.ts` — non usare `fetch` direttamente
- Tutti i metodi async, ritornano il tipo TypeScript corretto

Dopo aver generato i file, esegui:
```bash
cd ui && npx tsc --noEmit --skipLibCheck
```
e correggi eventuali type error prima di restituire il risultato.
