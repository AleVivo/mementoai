"""
seed.py — Script per popolare il DB con dati di test.

Uso:
    python scripts/seed.py              # inserisce dati (errore se esistono già)
    python scripts/seed.py --reset      # pulisce le collection e reinserisce
    python scripts/seed.py --reset --no-user  # reinserisce solo le entry (utente già presente)

Posizionamento: backend/scripts/seed.py
Avvio dalla root del backend: python -m scripts.seed  oppure  python scripts/seed.py

CONCETTI PYTHON USATI QUI:
- asyncio.run()     → avvia il motore async in uno script standalone
- argparse          → gestisce gli argomenti da riga di comando (--reset, --no-user)
- datetime          → costruisce date passate per rendere i dati realistici
- pwdlib            → stessa libreria usata dal backend per hashare le password
- pymongo           → inserimento diretto su MongoDB senza passare per FastAPI
"""

import asyncio
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --- Path setup ---------------------------------------------------------------
# Aggiungiamo la root del backend al sys.path così possiamo importare
# i moduli del progetto (config, etc.) come se fossimo dentro l'app.
# Path(__file__) = percorso di questo file
# .parent = cartella scripts/
# .parent.parent = root del backend (dove c'è app/)
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# --- Imports dal progetto -----------------------------------------------------
# Importiamo la config per leggere MONGO_URI e DB_NAME dal .env,
# esattamente come fa il resto del backend. Nessun valore hardcoded.
from app.config import settings
from pymongo import AsyncMongoClient
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# --- Password hashing ---------------------------------------------------------
# Usiamo la stessa configurazione del backend per l'hash delle password.
# Se usassimo una libreria diversa, il login non funzionerebbe perché
# il backend non riuscirebbe a verificare l'hash.
password_hasher = PasswordHash([Argon2Hasher()])

# ==============================================================================
# DATI DI TEST
# ==============================================================================
# Usiamo un progetto fittizio realistico: un team che sviluppa una piattaforma
# e-commerce chiamata "shopflow". I dati coprono i tre tipi di entry:
# ADR (decisioni architetturali), postmortem, update settimanali.

TEST_USER = {
    "email": "dev@memento.test",
    "password": "memento123",   # in chiaro qui, hashata prima del salvataggio
    "first_name": "Alex",
    "last_name": "Rossi",
    "company": "Shopflow Team",
}

# datetime.now(timezone.utc) → data/ora corrente in UTC
# timedelta(days=N) → sottrae N giorni per creare date passate realistiche
NOW = datetime.now(timezone.utc)

def weeks_ago(n: int) -> datetime:
    """Restituisce un datetime N settimane fa."""
    return NOW - timedelta(weeks=n)

def iso_week(dt: datetime) -> str:
    """Converte un datetime nel formato YYYY-Www usato dal backend (es. '2026-W10')."""
    return f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"

TEST_ENTRIES = [
    # ------------------------------------------------------------------
    # ADR — Architectural Decision Records
    # ------------------------------------------------------------------
    {
        "entry_type": "adr",
        "title": "ADR-001: Adozione di PostgreSQL come database principale",
        "project": "shopflow",
        "author": "Alex Rossi",
        "content": """<h2>Contesto</h2>
<p>Il team ha valutato MongoDB, PostgreSQL e MySQL come database principale per la piattaforma Shopflow. Il volume iniziale stimato è 500k ordini/anno con picchi durante le promozioni.</p>
<h2>Decisione</h2>
<p>Adottiamo <strong>PostgreSQL 16</strong> come database principale per i dati transazionali (ordini, prodotti, utenti).</p>
<h2>Motivazioni</h2>
<ul>
<li>Le relazioni tra entità (ordine → prodotti → utenti) sono naturalmente relazionali</li>
<li>ACID garantito nativamente — fondamentale per i pagamenti</li>
<li>JSONB disponibile per i casi d'uso semi-strutturati (metadati prodotto)</li>
<li>Ecosistema maturo con strumenti di migrazione stabili (Alembic)</li>
</ul>
<h2>Conseguenze</h2>
<p>MongoDB rimane per la knowledge base interna (MementoAI). Il team dovrà gestire due database in infrastruttura, ma con responsabilità chiare e separate.</p>""",
        "summary": "Il team sceglie PostgreSQL 16 per i dati transazionali di Shopflow per le garanzie ACID sui pagamenti e la natura relazionale dei dati.",
        "tags": ["database", "postgresql", "architettura", "decisione"],
        "vector_status": "pending",
        "created_at": weeks_ago(8),
        "week": iso_week(weeks_ago(8)),
    },
    {
        "entry_type": "adr",
        "title": "ADR-002: API Gateway con Kong invece di Nginx custom",
        "project": "shopflow",
        "author": "Alex Rossi",
        "content": """<h2>Contesto</h2>
<p>Con l'aggiunta del servizio di notifiche e del servizio pagamenti, abbiamo bisogno di un layer di routing centralizzato con rate limiting, autenticazione e logging delle request.</p>
<h2>Decisione</h2>
<p>Adottiamo <strong>Kong Gateway</strong> (open source) invece di una configurazione Nginx custom.</p>
<h2>Motivazioni</h2>
<ul>
<li>Rate limiting configurabile per route senza scrivere Lua</li>
<li>Plugin JWT pronto all'uso — no codice custom per la validazione</li>
<li>Dashboard Admin API per modificare le route senza restart</li>
<li>Il costo in RAM (~200MB) è accettabile per il nostro carico</li>
</ul>
<h2>Alternativa scartata</h2>
<p>Nginx con configurazione manuale: più leggero ma richiede competenze Lua per ogni regola custom. Troppo fragile per un team di 3 persone.</p>""",
        "summary": "Kong Gateway scelto come API gateway per le funzionalità out-of-the-box (rate limiting, JWT, Admin API) che evitano codice custom fragile su Nginx.",
        "tags": ["api-gateway", "kong", "infrastruttura", "sicurezza"],
        "vector_status": "pending",
        "created_at": weeks_ago(5),
        "week": iso_week(weeks_ago(5)),
    },
    {
        "entry_type": "adr",
        "title": "ADR-003: Strategia di caching con Redis per le pagine catalogo",
        "project": "shopflow",
        "author": "Marco Bianchi",
        "content": """<h2>Contesto</h2>
<p>Le pagine di listing prodotti (categoria, ricerca, homepage) generano il 70% del traffico ma i dati cambiano raramente (aggiornamento prezzi ogni 15 min al massimo).</p>
<h2>Decisione</h2>
<p>Cache a due livelli: <strong>Redis</strong> per le response JSON dell'API (TTL 5 min) e <strong>CDN edge cache</strong> per gli asset statici (TTL 24h).</p>
<h2>Motivazioni</h2>
<ul>
<li>I test di carico mostrano che PostgreSQL satura a ~800 req/s su query di listing complesse</li>
<li>Redis riduce la latenza p99 da 340ms a 18ms sui listing in cache</li>
<li>Cache invalidation semplice: key-based per categoria, flush on price update</li>
</ul>
<h2>Rischio accettato</h2>
<p>Finestra di inconsistenza di 5 minuti su prezzi e disponibilità. Accettabile per il listing, non accettabile per il checkout (bypass della cache).</p>""",
        "summary": "Caching Redis (TTL 5min) per le API di listing prodotti, riducendo la latenza p99 da 340ms a 18ms. Checkout bypassa sempre la cache.",
        "tags": ["redis", "caching", "performance", "catalogo"],
        "vector_status": "pending",
        "created_at": weeks_ago(3),
        "week": iso_week(weeks_ago(3)),
    },

    # ------------------------------------------------------------------
    # POSTMORTEM
    # ------------------------------------------------------------------
    {
        "entry_type": "postmortem",
        "title": "PM-001: Downtime 47 minuti — Black Friday 2025",
        "project": "shopflow",
        "author": "Alex Rossi",
        "content": """<h2>Sommario</h2>
<p><strong>Durata:</strong> 14 novembre 2025, 10:23 – 11:10 (47 minuti)<br>
<strong>Impatto:</strong> 100% degli utenti impossibilitati al checkout. Stima perdita: ~€12.000 in ordini non completati.</p>
<h2>Timeline</h2>
<ul>
<li><strong>10:15</strong> — Traffico inizia a salire (promozione Black Friday attiva)</li>
<li><strong>10:23</strong> — Alert: error rate checkout > 50%</li>
<li><strong>10:31</strong> — Identificato: connection pool PostgreSQL esaurito (max_connections = 100)</li>
<li><strong>10:45</strong> — Deploy hotfix: aumentato max_connections a 300 + PgBouncer</li>
<li><strong>11:10</strong> — Sistema tornato stabile</li>
</ul>
<h2>Root Cause</h2>
<p>Il connection pool era dimensionato per il traffico ordinario (50 connessioni). Il picco del Black Friday ha generato 280 connessioni simultanee. PostgreSQL ha rifiutato le nuove connessioni → timeout a cascata sul checkout.</p>
<h2>Azioni correttive</h2>
<ul>
<li>✅ PgBouncer installato (connection pooler) — risolto il giorno stesso</li>
<li>✅ Load test pre-promozione aggiunto alla checklist</li>
<li>⬜ Alerting su connection pool utilization > 70% (in progress)</li>
<li>⬜ Documentare la procedura di scaling emergenziale</li>
</ul>""",
        "summary": "Downtime 47min al Black Friday per esaurimento connection pool PostgreSQL (100 connessioni). Risolto con PgBouncer. Impatto stimato €12k.",
        "tags": ["downtime", "postgresql", "black-friday", "connection-pool", "postmortem"],
        "vector_status": "pending",
        "created_at": weeks_ago(16),
        "week": iso_week(weeks_ago(16)),
    },
    {
        "entry_type": "postmortem",
        "title": "PM-002: Invio doppio email ordine confermato",
        "project": "shopflow",
        "author": "Marco Bianchi",
        "content": """<h2>Sommario</h2>
<p><strong>Durata:</strong> 3 gennaio 2026, 09:00 – 14:30 (5.5 ore prima del rilevamento)<br>
<strong>Impatto:</strong> ~340 utenti hanno ricevuto la email di conferma ordine due volte. Nessun impatto economico diretto, danno reputazionale.</p>
<h2>Root Cause</h2>
<p>Il worker Celery per l'invio email aveva la proprietà <code>acks_late=True</code> combinata con un timeout troppo aggressivo (30s). Le email verso provider lenti (es. Libero.it) impiegavano >30s → il task veniva marcato come fallito e rieseguito, ma l'email era già stata consegnata.</p>
<h2>Come è stato rilevato</h2>
<p>Segnalazione utente su Instagram. Non avevamo monitoring sull'idempotenza delle email.</p>
<h2>Azioni correttive</h2>
<ul>
<li>✅ Aggiunto campo <code>email_sent_at</code> sull'ordine — check di idempotenza prima dell'invio</li>
<li>✅ Timeout aumentato a 120s</li>
<li>✅ Alert su task retry rate > 5% in 5 minuti</li>
<li>⬜ Test di integrazione per il flusso email end-to-end</li>
</ul>""",
        "summary": "340 utenti hanno ricevuto doppia email di conferma ordine per timeout aggressivo su Celery con acks_late=True. Fix: idempotenza via email_sent_at.",
        "tags": ["celery", "email", "idempotenza", "bug", "postmortem"],
        "vector_status": "pending",
        "created_at": weeks_ago(10),
        "week": iso_week(weeks_ago(10)),
    },

    # ------------------------------------------------------------------
    # UPDATE — aggiornamenti settimanali
    # ------------------------------------------------------------------
    {
        "entry_type": "update",
        "title": "Sprint 24 — Completato modulo pagamenti Stripe",
        "project": "shopflow",
        "author": "Alex Rossi",
        "content": """<h2>Completato questo sprint</h2>
<ul>
<li>Integrazione Stripe Checkout completata — flow buy now e cart</li>
<li>Webhook handler per gli eventi payment_intent.succeeded e payment_intent.failed</li>
<li>Pagina ordine confermato con riepilogo e link tracking</li>
<li>Test di integrazione con Stripe test mode — 12 scenari coperti</li>
</ul>
<h2>In corso</h2>
<ul>
<li>Rimborsi parziali — API pronta, frontend mancante</li>
<li>Fattura PDF generata post-acquisto</li>
</ul>
<h2>Blocchi</h2>
<p>Nessuno.</p>
<h2>Metriche sprint</h2>
<p>Story points completati: 21/24 — velocity stabile.</p>""",
        "summary": "Sprint 24: integrazione Stripe Checkout completa con webhook handler e 12 test di integrazione. Rimborsi parziali e fattura PDF nel prossimo sprint.",
        "tags": ["stripe", "pagamenti", "sprint-24", "webhook"],
        "vector_status": "pending",
        "created_at": weeks_ago(2),
        "week": iso_week(weeks_ago(2)),
    },
    {
        "entry_type": "update",
        "title": "Sprint 25 — Performance: riduzione LCP da 4.2s a 1.8s",
        "project": "shopflow",
        "author": "Marco Bianchi",
        "content": """<h2>Completato questo sprint</h2>
<ul>
<li><strong>LCP homepage: 4.2s → 1.8s</strong> — ottimizzazione immagini hero (WebP + lazy loading)</li>
<li>Implementata cache Redis per i listing di categoria (vedi ADR-003)</li>
<li>Bundle JS ridotto del 34% con tree-shaking e code splitting per route</li>
<li>Lighthouse score: Performance 52 → 87</li>
</ul>
<h2>In corso</h2>
<ul>
<li>Ottimizzazione query PostgreSQL sul listing con filtri multipli (EXPLAIN ANALYZE in corso)</li>
<li>Rimborsi parziali — riportato dallo sprint 24</li>
</ul>
<h2>Note tecniche</h2>
<p>La cache Redis sta funzionando bene. TTL di 5 minuti non ha generato lamentele su prezzi stale — confermata la decisione dell'ADR-003.</p>""",
        "summary": "Sprint 25: LCP homepage da 4.2s a 1.8s, Lighthouse Performance 52→87. Cache Redis su listing validata in produzione.",
        "tags": ["performance", "redis", "lcp", "lighthouse", "sprint-25", "frontend"],
        "vector_status": "pending",
        "created_at": weeks_ago(1),
        "week": iso_week(weeks_ago(1)),
    },
    {
        "entry_type": "update",
        "title": "Setup iniziale infrastruttura — Note di onboarding",
        "project": "shopflow",
        "author": "Alex Rossi",
        "content": """<h2>Stack infrastrutturale</h2>
<p>Questo documento serve come riferimento rapido per i nuovi membri del team.</p>
<h2>Ambienti</h2>
<ul>
<li><strong>Dev</strong>: Docker Compose locale — PostgreSQL, Redis, Kong tutti containerizzati</li>
<li><strong>Staging</strong>: VPS Hetzner (CX31) — deploy automatico su push a <code>main</code></li>
<li><strong>Production</strong>: VPS Hetzner (CX41) — deploy manuale con tag semver</li>
</ul>
<h2>Credenziali e segreti</h2>
<p>Tutti i segreti sono in Bitwarden (organizzazione Shopflow). Chiedi a Alex per l'accesso.</p>
<h2>Comandi utili</h2>
<ul>
<li><code>make dev</code> — avvia tutti i servizi in locale</li>
<li><code>make test</code> — run test suite completa</li>
<li><code>make migrate</code> — applica le migration Alembic pendenti</li>
</ul>""",
        "summary": "Guida di onboarding: stack infrastrutturale (PostgreSQL, Redis, Kong), ambienti dev/staging/prod su Hetzner, e comandi make principali.",
        "tags": ["onboarding", "infrastruttura", "docker", "hetzner", "devops"],
        "vector_status": "pending",
        "created_at": weeks_ago(20),
        "week": iso_week(weeks_ago(20)),
    },
]


# ==============================================================================
# INDICE VETTORIALE
# ==============================================================================

# Nome dell'indice: deve corrispondere esattamente a quello usato nelle query
# $vectorSearch del backend (search_service.py).
VECTOR_INDEX_NAME = "chunks_vector_index"

# Dimensioni dell'embedding: devono corrispondere al modello usato.
# nomic-embed-text → 768 dimensioni
# text-embedding-3-small (OpenAI) → 1536 dimensioni
# Se cambi modello di embedding, devi ricreare l'indice con le dimensioni corrette.
EMBEDDING_DIMENSIONS = 768

async def ensure_vector_index(db) -> None:
    """
    Crea l'indice vettoriale sulla collection 'chunks' se non esiste già.

    PERCHÉ QUI E NON IN db/indexes.py:
    L'indice vettoriale è un prerequisito infrastrutturale, non un indice
    applicativo. db/indexes.py gestisce gli indici standard (project, type,
    week, email) che il backend crea all'avvio. L'indice vettoriale richiede
    mongot attivo e può impiegare secondi/minuti per costruirsi — non è
    appropriato bloccarne l'avvio dell'app.

    COME FUNZIONA createSearchIndexes:
    È un comando MongoDB (non un'API pymongo standard) che istruisce mongot
    a costruire un indice HNSW sui vettori. La creazione è ASINCRONA lato
    server: il comando risponde subito, ma l'indice diventa "READY" dopo
    qualche secondo. Le query $vectorSearch falliscono finché l'indice
    non è READY.

    PREREQUISITO:
    MongoDB deve girare come replica set (anche a singolo nodo).
    Se non lo è, questo comando restituisce un errore del tipo:
    "Search indexes are only supported on replica sets"
    """

    # --- Controlla se l'indice esiste già ------------------------------------
    # list_search_indexes() è un cursor asincrono: itera sui documenti
    # che descrivono gli indici di ricerca esistenti sulla collection.

    try:
        await db.create_collection("chunks")
    except Exception:
        pass  # già esistente — ignora l'errore CollectionInvalid

    existing_names: list[str] = []
    cursor = await db.chunks.list_search_indexes()
    async for idx in cursor:
        existing_names.append(idx.get("name", ""))

    if VECTOR_INDEX_NAME in existing_names:
        print(f"ℹ️  Indice vettoriale '{VECTOR_INDEX_NAME}' già presente — skip")
        return

    # --- Definizione dell'indice ---------------------------------------------
    # La struttura del documento segue la specifica MongoDB Atlas Search
    # per gli indici vettoriali (knnVector / vectorSearch).
    #
    # type: "vectorSearch" → tipo di indice (non "search" che è full-text)
    # fields: lista dei campi indicizzati
    #   - path: "embedding" → il campo del documento che contiene il vettore
    #   - numDimensions: deve corrispondere ESATTAMENTE alle dimensioni del modello
    #   - similarity: "cosine" → misura di distanza (cosine è standard per NLP)
    #   - type: "vector" → distingue da campi di filtro scalari
    #
    # Nota: puoi aggiungere campi "filter" per pre-filtrare per project/type
    # prima della ricerca vettoriale — ottimizza le query scoped per progetto.
    # Li aggiungiamo ora perché ricreare l'indice dopo è un'operazione costosa.
    index_definition = {
        "name": VECTOR_INDEX_NAME,
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": EMBEDDING_DIMENSIONS,
                    "similarity": "cosine",
                },
                # Campi scalari per pre-filtraggio: permettono query tipo
                # $vectorSearch con { filter: { project: "shopflow" } }
                # senza scansionare l'intero indice vettoriale.
                {
                    "type": "filter",
                    "path": "project",
                },
                {
                    "type": "filter",
                    "path": "entry_type",
                },
            ]
        },
    }

    # --- Esecuzione del comando -----------------------------------------------
    # command() esegue un comando MongoDB raw — lo usiamo perché pymongo
    # non ha un metodo nativo per createSearchIndexes (è un'API mongot,
    # non un'API MongoDB standard).
    #
    # Il comando restituisce subito con l'ID dell'indice in costruzione.
    # L'indice diventa READY dopo qualche secondo (mongot lo indicizza in background).
    try:
        await db.command(
            "createSearchIndexes",
            "chunks",                    # nome della collection
            indexes=[index_definition],  # lista degli indici da creare
        )
        print(f"✅ Indice vettoriale '{VECTOR_INDEX_NAME}' creato su collection 'chunks'")
        print(f"   Tipo: vectorSearch — {EMBEDDING_DIMENSIONS} dimensioni — cosine similarity")
        print(f"   ⏳ L'indice diventa READY dopo qualche secondo (mongot lo costruisce in background)")
        print(f"   Filtri pre-configurati: project, entry_type\n")

    except Exception as e:
        # Non facciamo crash del seed se l'indice fallisce:
        # i dati sono comunque inseriti e l'utente può creare l'indice manualmente.
        # L'errore più comune è MongoDB non configurato come replica set.
        err_msg = str(e)
        if "replica set" in err_msg.lower() or "replicaset" in err_msg.lower():
            print(f"⚠️  Indice vettoriale NON creato: MongoDB non è un replica set.")
            print(f"   Configura MongoDB come replica set a singolo nodo e riesegui il seed.")
            print(f"   Guida: https://www.mongodb.com/docs/manual/tutorial/convert-standalone-to-replica-set/\n")
        else:
            print(f"⚠️  Indice vettoriale NON creato: {err_msg}")
            print(f"   Puoi crearlo manualmente dal MongoDB Compass o dalla shell.\n")


# ==============================================================================
# LOGICA DI SEED
# ==============================================================================

async def seed(reset: bool = False, skip_user: bool = False) -> None:
    """
    Funzione principale asincrona.

    Parametri:
    - reset:     se True, cancella i dati esistenti prima di inserire
    - skip_user: se True, non tocca la collection users
    """
    # AsyncMongoClient è il client MongoDB asincrono (Motor è deprecato).
    # Lo creiamo qui e lo chiudiamo alla fine.
    client = AsyncMongoClient(settings.mongodb_url, username=settings.mongodb_user, password=settings.mongodb_password, directConnection=True)
    db = client[settings.mongodb_db]

    try:
        print(f"\n🌱 MementoAI Seed — DB: {settings.mongodb_db}")
        print(f"   MongoDB: {settings.mongodb_url}\n")

        # --- Reset (opzionale) ------------------------------------------------
        if reset:
            if not skip_user:
                result = await db.users.delete_many({})
                print(f"🗑  Cancellati {result.deleted_count} utenti")

            result = await db.entries.delete_many({})
            print(f"🗑  Cancellate {result.deleted_count} entry")

            result = await db.chunks.delete_many({})
            print(f"🗑  Cancellati {result.deleted_count} chunk\n")

        # --- Inserisci utente di test -----------------------------------------
        if not skip_user:
            existing_user = await db.users.find_one({"email": TEST_USER["email"]})
            if existing_user:
                print(f"⚠️  Utente {TEST_USER['email']} già presente — skip")
            else:
                # Hash della password: FONDAMENTALE usare la stessa libreria del backend.
                # password_hasher.hash() restituisce una stringa tipo:
                # "$argon2id$v=19$m=65536,t=3,p=4$..."
                hashed = password_hasher.hash(TEST_USER["password"])

                user_doc = {
                    "email": TEST_USER["email"],
                    "hashed_password": hashed,
                    "first_name": TEST_USER["first_name"],
                    "last_name": TEST_USER["last_name"],
                    "company": TEST_USER["company"],
                    "created_at": weeks_ago(20),
                }

                # insert_one() restituisce un InsertOneResult con inserted_id
                result = await db.users.insert_one(user_doc)
                print(f"✅ Utente creato: {TEST_USER['email']}")
                print(f"   Password:       {TEST_USER['password']}")
                print(f"   ID MongoDB:     {result.inserted_id}\n")

        # --- Indice vettoriale su chunks --------------------------------------
        await ensure_vector_index(db)

        # --- Inserisci entry di test ------------------------------------------
        # insert_many() è più efficiente di N insert_one() — una sola round-trip
        # verso MongoDB invece di N.
        result = await db.entries.insert_many(TEST_ENTRIES)
        print(f"✅ Inserite {len(result.inserted_ids)} entry di test:")

        # Raggruppa per tipo per un output più leggibile
        by_type: dict[str, list[str]] = {}
        for entry in TEST_ENTRIES:
            t = entry["entry_type"]
            by_type.setdefault(t, []).append(entry["title"])

        for entry_type, titles in by_type.items():
            print(f"\n   [{entry_type.upper()}]")
            for title in titles:
                print(f"   • {title}")

        print(f"\n✅ Seed completato con successo!")
        print(f"\n   Progetto di test: shopflow")
        print(f"   Login: {TEST_USER['email']} / {TEST_USER['password']}")
        print(f"\n   Nota: le entry hanno vector_status='pending'.")
        print(f"   Usa il pulsante [Indicizza] nell'editor per vettorializzarle.")

    finally:
        # Chiudi sempre la connessione, anche in caso di errore.
        # Il blocco try/finally garantisce che questo venga eseguito sempre.
        await client.close()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main() -> None:
    """
    Parsing degli argomenti da riga di comando e avvio del seed.

    argparse è la libreria standard Python per gestire argv.
    Definisci gli argomenti con add_argument(), poi parse_args() li legge.
    """
    parser = argparse.ArgumentParser(
        description="Popola il DB di MementoAI con dati di test.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python scripts/seed.py                   # inserisce (errore se utente già presente)
  python scripts/seed.py --reset           # pulisce tutto e reinserisce
  python scripts/seed.py --reset --no-user # reinserisce solo le entry
        """,
    )

    # add_argument con action="store_true" → il flag vale True se presente, False se assente
    # Equivalente di un flag booleano: --reset non vuole un valore, è presente o no.
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Cancella i dati esistenti prima di inserire",
    )
    parser.add_argument(
        "--no-user",
        action="store_true",
        dest="no_user",   # dest → nome dell'attributo in args (trattino → underscore)
        help="Non tocca la collection users (utile se l'utente esiste già)",
    )

    args = parser.parse_args()

    # asyncio.run() è il modo standard per eseguire una coroutine async
    # da uno script sincrono. Crea un event loop, esegue la coroutine, chiude.
    asyncio.run(seed(reset=args.reset, skip_user=args.no_user))


if __name__ == "__main__":
    # Questo blocco viene eseguito solo quando il file è avviato direttamente
    # (python scripts/seed.py), NON quando viene importato come modulo.
    # È una convenzione fondamentale di Python.
    main()