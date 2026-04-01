---
agent: agent
description: "Code review e cleanup completo del codebase MementoAI. Rimuove codice morto, verifica pattern architetturali, allinea documentazione e verifica consistenza frontend ↔ backend. Eseguibile dopo ogni fase di sviluppo."
tools: ["search/codebase", "vscode/runCommand"]
---

Prima di iniziare scrivi in chat **"INIZIO CODE REVIEW"**. Al termine scrivi **"TERMINE CODE REVIEW"**.

Segui le istruzioni del progetto in `.github/copilot-instructions.md` per capire struttura, stack e convenzioni prima di procedere.

---

## 1. Rimozione file e componenti obsoleti

- Cerca file non importati da nessun altro modulo (inverso di `grep -r "import.*from"`)
- Cerca componenti React definiti ma mai usati in `ui/src/`
- Rimuovi i file confermati come non più referenziati
- Verifica in particolare: file rinominati o sostituiti durante refactor recenti

## 2. Audit import inutilizzati

Esegui nel terminale:
```bash
cd ui && npx tsc --noEmit
```
Risolvi tutti gli errori e warning TypeScript. Per ogni file con import inutilizzati, rimuovi solo quelli non usati senza alterare la logica.

## 3. Checklist pattern architetturali

Verifica i seguenti problemi sul codice modificato o aggiunto di recente. Classificali per severità e segnala quelli trovati prima di procedere alle fasi successive.

### 🔴 Critici (blocca il merge)

**Backend:**
- [ ] Query MongoDB dentro un router — devono stare nel service layer
- [ ] Import di `Motor` — deprecato dal 14/05/2025, usare `AsyncMongoClient` da `pymongo`
- [ ] Chiamata LLM o embedding dentro `PUT /entries/:id` — il save deve essere LLM-free
- [ ] Secret letto da `config_values` senza passare per `utils/encryption.decrypt()`
- [ ] Endpoint protetto senza `Depends(get_current_user)` o `Depends(require_admin)`
- [ ] `ObjectId` restituito direttamente in un response model — deve essere convertito a `str`
- [ ] Nome modello hardcoded (es. `"qwen2.5:7b"`) invece di usare `provider_cache`
- [ ] Chiamata diretta a Ollama/LiteLLM via `fetch` o `httpx` — deve passare per `provider_cache`

**Frontend:**
- [ ] `fetch()` diretto in un componente invece di usare `ui/src/api/*.ts`
- [ ] Mutazione di `vector_status` da un'azione di save — il save imposta solo `outdated`, mai avvia l'indicizzazione
- [ ] Nuova keyboard shortcut globale non registrata in `useKeyboardShortcuts.ts`
- [ ] Accesso a `localStorage` fuori da `auth.store.ts`
- [ ] Header `Authorization` mancante su una chiamata fetch — usare il wrapper del client API

### 🟡 Importanti (correggere prima possibile)

- [ ] Funzione Python senza type hints sui parametri o sul return
- [ ] Tipo `any` in TypeScript senza commento che spieghi perché
- [ ] Componente React più lungo di 150 righe che potrebbe essere suddiviso
- [ ] Errore catturato silenziosamente senza logging
- [ ] Stringa hardcoded che dovrebbe essere una costante (tipi entry, valori status)
- [ ] `useEffect` con dipendenza mancante nell'array
- [ ] Nuovo campo MongoDB senza il corrispondente indice in `backend/app/db/indexes.py`

### 🟢 Stile (nice to fix)

- [ ] Arrow function inline nel JSX per un handler di più righe — estrarre come funzione nominata
- [ ] Ordine degli import non conforme alla convenzione del progetto
- [ ] Nome variabile non autoesplicativo
- [ ] Funzione pubblica Python senza docstring in stile Google

## 4. Consistenza convenzioni

**Frontend:**
- Componenti: PascalCase, file `.tsx`
- Hook: prefisso `use`, file `.ts`
- API calls: sempre tramite `ui/src/api/` — mai `fetch()` diretto nei componenti
- Styling: solo classi TailwindCSS — niente `style={{}}` inline salvo casi documentati
- Icone: solo `lucide-react`
- State condiviso: Zustand stores — niente prop drilling su più di 2 livelli

## 5. Revisione store Zustand

Leggi `ui/src/store/ui.store.ts`, `entries.store.ts`, `chat.store.ts` e verifica:
- Nessun campo è orfano (definito ma mai letto o scritto da componenti)
- I campi `isDirty`, `isSaving`, `isIndexing` sono correttamente resettati dopo ogni operazione
- Le azioni dello store non duplicano logica già presente negli hook

## 6. Allineamento Frontend ↔ Backend

Verifica la corrispondenza tra:
- `ui/src/types/index.ts` e i modelli Pydantic in `backend/app/models/`
- I campi inviati nelle chiamate `apiPost`/`apiPut` e i DTO accettati dal backend
- I campi ricevuti nelle risposte e i tipi TypeScript usati per deserializzarle

Segnala ogni mismatch trovato. Applica le correzioni solo se il fix è non ambiguo; altrimenti elenca i mismatch con una proposta.

## 7. Allineamento documentazione

Aggiorna i seguenti file per rispecchiare lo stato reale del codice:
- `.github/copilot-instructions.md`: struttura directory, tipi, store, pattern UX
- `docs/frontend-spec.md`: TypeScript types, struttura progetto, versioni stack
- `docs/architecture.md`: data flow, stack

Non aggiungere sezioni nuove — aggiorna solo ciò che è cambiato.

## 8. Dead code backend

Leggi i file Python in `backend/app/models/`, `backend/app/services/`, `backend/app/routers/` e verifica:
- Nessun campo nei modelli Pydantic è definito ma mai usato
- Nessuna funzione nei service è definita ma mai chiamata da un router (salvo deprecate commentate)
- I DTO di request/response sono allineati a ciò che il frontend invia e si aspetta

## 9. Deduplicazione codice

Cerca logica duplicata introdotta durante lo sprint:

**Backend:**
- Funzioni o blocchi logicamente identici in più file in `routers/`, `services/`, `db/`
- Costruzione ripetuta degli stessi modelli Pydantic — valuta factory o helper
- Query MongoDB con lo stesso pattern ripetute in più funzioni

**Frontend:**
- Componenti o sezioni JSX identiche usate in più pagine — valuta estrazione in componente condiviso
- Logica di stato o side effect duplicata tra hook — valuta hook custom
- Classi Tailwind identiche ripetute su più elementi

Per ogni duplicazione: applica la refactoring solo se la logica appare almeno 2 volte ed è identica (non solo simile). Non introdurre astrazioni per casi che potrebbero divergere in futuro.

---

## Output atteso

Al termine fornisci:
1. Lista dei file eliminati
2. Lista delle modifiche applicate (file + descrizione sintetica)
3. Riepilogo checklist fase 3: quanti problemi per severità, il più critico da risolvere prima del merge
4. Lista di eventuali mismatch frontend ↔ backend non risolti con proposta di fix
5. Conferma che `npx tsc --noEmit` termina senza errori