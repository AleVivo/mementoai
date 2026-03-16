---
agent: agent
description: Code review e cleanup del codebase MementoAI. Rimuove codice morto, allinea la documentazione e verifica la consistenza tra frontend e backend. Eseguibile dopo ogni fase di sviluppo.
---

Esegui una code review e cleanup completa del codebase MementoAI. Segui le istruzioni del progetto in `.github/copilot-instructions.md` per capire struttura, stack e convenzioni. Prima di iniziare questa fase scrivi in chat "INIZIO CODE REVIEW" e al termine scrivi "TERMINE CODE REVIEW"

## 1. Rimozione file e componenti obsoleti

- Cerca file importati da nessun altro modulo (`grep -r "import.*from"` nel contrario)
- Cerca componenti React definiti ma mai usati in `ui/src/`
- Rimuovi i file confermati come non più referenziati
- Verifica in particolare: file rinominati o sostituiti durante refactor recenti

## 2. Audit import inutilizzati

Esegui nel terminale:
```
cd ui && npx tsc --noEmit
```
Risolvi tutti gli errori e warning TypeScript. Per ogni file con import inutilizzati, rimuovi solo quelli non usati senza alterare la logica.

## 3. Consistenza convenzioni

Verifica che il codice rispetti le convenzioni del progetto:
- **Componenti**: PascalCase, file `.tsx`
- **Hook**: prefisso `use`, file `.ts`
- **API calls**: sempre tramite `ui/src/api/` — mai `fetch()` diretto nei componenti
- **Styling**: solo classi TailwindCSS — niente `style={{}}` inline salvo casi documentati (es. padding dinamico non generato da Tailwind v4)
- **Icone**: solo `lucide-react`
- **State condiviso**: Zustand stores — niente prop drilling su più di 2 livelli

## 4. Revisione store Zustand

Leggi `ui/src/store/ui.store.ts`, `entries.store.ts`, `chat.store.ts` e verifica:
- Nessun campo nello store è orfano (definito ma mai letto o scritto da componenti)
- I campi `isDirty`, `isSaving`, `isIndexing` sono correttamente resettati dopo ogni operazione
- Le azioni dello store non duplicano logica già presente negli hook

## 5. Allineamento Frontend ↔ Backend

Verifica la corrispondenza tra:
- `ui/src/types/index.ts` e i modelli Pydantic in `app/models/`
- I campi inviati nelle chiamate `apiPost/apiPut` e i DTO accettati dal backend
- I campi ricevuti nelle risposte e i tipi TypeScript usati per deserializzarle

Segnala ogni mismatch trovato. Applica le correzioni solo se il fix è non ambiguo; altrimenti elenca i mismatch con una proposta.

## 6. Allineamento documentazione

Aggiorna i seguenti file per rispecchiare lo stato reale del codice:
- `.github/copilot-instructions.md`: struttura directory, tipi TypeScript, store Zustand, UX patterns
- `docs/frontend-spec.md`: TypeScript types, project structure, stack versions
- `docs/architecture.md`: data flow, stack

Non aggiungere sezioni nuove — aggiorna solo ciò che è cambiato.

## 7. Dead code backend

Leggi i file Python in `app/models/`, `app/services/`, `app/routers/` e verifica:
- Nessun campo nei modelli Pydantic è definito ma mai usato
- Nessuna funzione nei service è definita ma mai chiamata da un router senza essere commentata come deprecata o in attesa di rimozione
- I DTO di request/response sono allineati a ciò che il frontend invia e si aspetta

## 8. Deduplicazione codice

Analizza il codebase alla ricerca di logica duplicata introdotta durante lo sprint:

**Backend:**
- Funzioni o blocchi di codice logicamente identici in più file `app/routers/`, `app/services/`, `app/db/`
- Costruzione ripetuta degli stessi modelli Pydantic (pattern `ModelName(field=x.field, ...)` in più punti) — valuta l'estrazione di un helper o factory
- Query MongoDB con lo stesso pattern ripetute in più funzioni DB

**Frontend:**
- Componenti React o sezioni JSX identiche usate in più pagine — valuta l'estrazione in un componente condiviso
- Logica di stato o side effect duplicata tra hook o componenti — valuta l'estrazione in un hook custom
- Stili Tailwind identici ripetuti su più elementi — valuta l'uso di una classe componente o variabile

Per ogni duplicazione identificata: applica la refactoring solo se la logica appare almeno 2 volte ed è identica (non solo simile). Non introdurre astrazioni per casi che potrebbero divergere in futuro.

## Output atteso

Al termine:
1. Lista dei file eliminati
2. Lista delle modifiche applicate (file + descrizione sintetica)
3. Lista di eventuali mismatch non risolti con proposta di fix
4. Conferma che `tsc --noEmit` termina senza errori
