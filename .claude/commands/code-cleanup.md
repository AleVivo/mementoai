Analizza il codice con strumenti reali e proponi fix per i problemi trovati.

## Istruzioni

Esegui questi comandi nell'ordine indicato e raccogli l'output completo prima di proporre fix.

### Step 1 — Type errors frontend
```bash
cd ui && npx tsc --noEmit --skipLibCheck 2>&1
```

### Step 2 — Type errors backend
```bash
uv run pyright app/ 2>&1
```

### Step 3 — Console.log non rimossi
```bash
grep -rn "console\.log" ui/src/ --include="*.ts" --include="*.tsx"
```

### Step 4 — Annotazioni pendenti
```bash
grep -rn "TODO\|FIXME\|HACK\|XXX" app/ ui/src/ --include="*.py" --include="*.ts" --include="*.tsx"
```

### Step 5 — Import non usati (pattern comune)
```bash
grep -rn "^import " ui/src/ --include="*.ts" --include="*.tsx" | grep -v "from" | head -20
```

### Step 6 — Verifica vector_status dopo PUT
```bash
grep -rn "vector_status" app/routers/ app/services/domain/
```
Controlla che ogni `PUT /entries` aggiorni `vector_status = "outdated"`.

### Step 7 — Verifica provider cache
```bash
grep -rn "LiteLLM\|litellm\|OpenAI\|ChatOllama" app/services/ --include="*.py" | grep -v "provider_cache\|factory\|litellm_provider"
```
Eventuali istanziazioni LLM fuori da `provider_cache.py` / `factory.py` sono un problema.

---

Per ogni problema trovato:
1. Mostra il file e la riga esatta
2. Spiega perché è un problema nel contesto di MementoAI
3. Proponi il fix con il codice corretto
4. Applica il fix direttamente se l'utente non specifica diversamente
