"""
seed.py — Script per popolare il DB con dati di test.

Uso:
    python scripts/seed.py              # inserisce dati (skip se già presenti)
    python scripts/seed.py --reset      # pulisce le collection e reinserisce
    python scripts/seed.py --reset --no-user  # reinserisce progetto + entry (utenti già presenti)

Avvio dalla root del progetto:
    python scripts/seed.py
"""

import asyncio
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from bson import ObjectId

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings
from pymongo import AsyncMongoClient
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hasher = PasswordHash([Argon2Hasher()])

# ==============================================================================
# DATI DI TEST
# ==============================================================================

TEST_USERS = [
    {
        "email": "alex@memento.com",
        "password": "memento123",
        "first_name": "Alex",
        "last_name": "Rossi",
        "company": "Shopflow Team",
    },
    {
        "email": "marco@memento.com",
        "password": "memento123",
        "first_name": "Marco",
        "last_name": "Bianchi",
        "company": "Shopflow Team",
    },
]

TEST_PROJECT = {
    "name": "shopflow",
    "description": "Piattaforma e-commerce del team Shopflow.",
}

NOW = datetime.now(timezone.utc)

def weeks_ago(n: int) -> datetime:
    return NOW - timedelta(weeks=n)

def iso_week(dt: datetime) -> str:
    return f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"


# Template delle entry — projectId, authorId, author vengono iniettati a runtime
ENTRY_TEMPLATES = [
    # ── ADR ───────────────────────────────────────────────────────────────────
    {
        "entry_type": "adr",
        "title": "ADR-001: Adozione di PostgreSQL come database principale",
        "author_key": "alex",
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
        "created_at": weeks_ago(8),
    },
    {
        "entry_type": "adr",
        "title": "ADR-002: API Gateway con Kong invece di Nginx custom",
        "author_key": "alex",
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
        "created_at": weeks_ago(5),
    },
    {
        "entry_type": "adr",
        "title": "ADR-003: Strategia di caching con Redis per le pagine catalogo",
        "author_key": "marco",
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
        "created_at": weeks_ago(3),
    },
    # ── POSTMORTEM ────────────────────────────────────────────────────────────
    {
        "entry_type": "postmortem",
        "title": "PM-001: Downtime 47 minuti — Black Friday 2025",
        "author_key": "alex",
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
        "created_at": weeks_ago(16),
    },
    {
        "entry_type": "postmortem",
        "title": "PM-002: Invio doppio email ordine confermato",
        "author_key": "marco",
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
        "created_at": weeks_ago(10),
    },
    # ── UPDATE ────────────────────────────────────────────────────────────────
    {
        "entry_type": "update",
        "title": "Sprint 24 — Completato modulo pagamenti Stripe",
        "author_key": "alex",
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
        "created_at": weeks_ago(2),
    },
    {
        "entry_type": "update",
        "title": "Sprint 25 — Performance: riduzione LCP da 4.2s a 1.8s",
        "author_key": "marco",
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
        "created_at": weeks_ago(1),
    },
    {
        "entry_type": "update",
        "title": "Setup iniziale infrastruttura — Note di onboarding",
        "author_key": "alex",
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
        "created_at": weeks_ago(20),
    },
]


# ==============================================================================
# INDICE VETTORIALE
# ==============================================================================

VECTOR_INDEX_NAME = "chunks_vector_index"
EMBEDDING_DIMENSIONS = 768

async def drop_vector_index(db) -> None:
    existing_names: list[str] = []
    try:
        cursor = await db.chunks.list_search_indexes()
        async for idx in cursor:
            existing_names.append(idx.get("name", ""))
    except Exception:
        return  # collection non esiste ancora — nulla da eliminare

    if VECTOR_INDEX_NAME not in existing_names:
        return

    try:
        await db.command("dropSearchIndex", "chunks", name=VECTOR_INDEX_NAME)
        print(f"🗑  Indice vettoriale '{VECTOR_INDEX_NAME}' eliminato")
    except Exception as e:
        print(f"⚠️  Impossibile eliminare l'indice: {e}")


async def ensure_vector_index(db) -> None:
    try:
        await db.create_collection("chunks")
    except Exception:
        pass

    existing_names: list[str] = []
    cursor = await db.chunks.list_search_indexes()
    async for idx in cursor:
        existing_names.append(idx.get("name", ""))

    if VECTOR_INDEX_NAME in existing_names:
        print(f"ℹ️  Indice vettoriale '{VECTOR_INDEX_NAME}' già presente — skip")
        return

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
                # Filtro per project scope (ObjectId stringificato)
                {"type": "filter", "path": "project_id"},
                {"type": "filter", "path": "entry_type"},
            ]
        },
    }

    try:
        await db.command("createSearchIndexes", "chunks", indexes=[index_definition])
        print(f"✅ Indice vettoriale '{VECTOR_INDEX_NAME}' creato")
        print(f"   {EMBEDDING_DIMENSIONS} dimensioni — cosine — filtri: projectId, entry_type")
        print(f"   ⏳ Diventa READY dopo qualche secondo (mongot lo costruisce in background)\n")
    except Exception as e:
        err_msg = str(e)
        if "replica set" in err_msg.lower() or "replicaset" in err_msg.lower():
            print(f"⚠️  Indice vettoriale NON creato: MongoDB non è configurato come replica set.")
        else:
            print(f"⚠️  Indice vettoriale NON creato: {err_msg}")


# ==============================================================================
# LOGICA DI SEED
# ==============================================================================

async def seed(reset: bool = False, skip_user: bool = False) -> None:
    client = AsyncMongoClient(
        settings.mongodb_url,
        username=settings.mongodb_user,
        password=settings.mongodb_password,
        directConnection=True,
    )
    db = client[settings.mongodb_db]

    try:
        print(f"\n🌱 MementoAI Seed — DB: {settings.mongodb_db}")
        print(f"   MongoDB: {settings.mongodb_url}\n")

        # ── Reset ────────────────────────────────────────────────────────────
        if reset:
            if not skip_user:
                r = await db.users.delete_many({})
                print(f"🗑  Cancellati {r.deleted_count} utenti")

            for coll in ("entries", "chunks", "projects", "project_members"):
                r = await db[coll].delete_many({})
                print(f"🗑  Cancellati {r.deleted_count} documenti da '{coll}'")
            await drop_vector_index(db)
            print()

        # ── Utenti ───────────────────────────────────────────────────────────
        user_ids: dict[str, ObjectId] = {}   # "alex" → ObjectId
        user_names: dict[str, str] = {}      # "alex" → "Alex Rossi"

        if not skip_user:
            for u in TEST_USERS:
                key = u["first_name"].lower()
                existing = await db.users.find_one({"email": u["email"]})
                if existing:
                    user_ids[key] = existing["_id"]
                    user_names[key] = f"{u['first_name']} {u['last_name']}"
                    print(f"⚠️  Utente {u['email']} già presente — skip")
                else:
                    hashed = password_hasher.hash(u["password"])
                    doc = {
                        "email": u["email"],
                        "hashed_password": hashed,
                        "first_name": u["first_name"],
                        "last_name": u["last_name"],
                        "company": u["company"],
                        "created_at": weeks_ago(20),
                    }
                    result = await db.users.insert_one(doc)
                    user_ids[key] = result.inserted_id
                    user_names[key] = f"{u['first_name']} {u['last_name']}"
                    print(f"✅ Utente creato: {u['email']} (password: {u['password']})")
        else:
            # Recupera gli utenti esistenti dal DB
            for u in TEST_USERS:
                key = u["first_name"].lower()
                existing = await db.users.find_one({"email": u["email"]})
                if existing:
                    user_ids[key] = existing["_id"]
                    user_names[key] = f"{u['first_name']} {u['last_name']}"
                else:
                    print(f"⚠️  Utente {u['email']} non trovato — alcune entry non avranno authorId corretto")

        print()

        # ── Indice vettoriale ────────────────────────────────────────────────
        await ensure_vector_index(db)

        # ── Progetto ─────────────────────────────────────────────────────────
        owner_id = user_ids.get("alex")
        if not owner_id:
            print("❌ Utente 'alex' non trovato — impossibile creare il progetto.")
            return

        existing_project = await db.projects.find_one({"name": TEST_PROJECT["name"]})
        if existing_project:
            project_id = existing_project["_id"]
            print(f"⚠️  Progetto '{TEST_PROJECT['name']}' già presente — skip")
        else:
            project_doc = {
                "name": TEST_PROJECT["name"],
                "description": TEST_PROJECT["description"],
                "ownerId": owner_id,
                "createdAt": weeks_ago(20),
            }
            result = await db.projects.insert_one(project_doc)
            project_id = result.inserted_id
            print(f"✅ Progetto creato: '{TEST_PROJECT['name']}' (id: {project_id})")

        # ── Membri del progetto ───────────────────────────────────────────────
        for key, uid in user_ids.items():
            role = "owner" if key == "alex" else "member"
            existing_member = await db.project_members.find_one(
                {"projectId": project_id, "userId": uid}
            )
            if existing_member:
                print(f"⚠️  {user_names.get(key, key)} già membro — skip")
            else:
                await db.project_members.insert_one({
                    "projectId": project_id,
                    "userId": uid,
                    "role": role,
                    "addedAt": weeks_ago(20),
                })
                print(f"✅ Membro aggiunto: {user_names.get(key, key)} ({role})")

        print()

        # ── Entry ─────────────────────────────────────────────────────────────
        entries_to_insert = []
        for tmpl in ENTRY_TEMPLATES:
            author_key = tmpl["author_key"]
            author_id = user_ids.get(author_key, owner_id)
            author_name = user_names.get(author_key, "Unknown")
            created_at = tmpl["created_at"]
            entries_to_insert.append({
                "entry_type": tmpl["entry_type"],
                "title": tmpl["title"],
                "content": tmpl["content"],
                "summary": tmpl["summary"],
                "tags": tmpl["tags"],
                "projectId": project_id,
                "authorId": author_id,
                "author": author_name,
                "vector_status": "pending",
                "created_at": created_at,
                "week": iso_week(created_at),
            })

        result = await db.entries.insert_many(entries_to_insert)
        print(f"✅ Inserite {len(result.inserted_ids)} entry:")

        by_type: dict[str, list[str]] = {}
        for e in entries_to_insert:
            by_type.setdefault(e["entry_type"], []).append(e["title"])
        for entry_type, titles in by_type.items():
            print(f"\n   [{entry_type.upper()}]")
            for title in titles:
                print(f"   • {title}")

        print(f"\n✅ Seed completato!")
        print(f"\n   Progetto : {TEST_PROJECT['name']} (id: {project_id})")
        for u in TEST_USERS:
            print(f"   Login    : {u['email']} / {u['password']}")
        print(f"\n   Nota: le entry sono vector_status='pending'.")
        print(f"   Usa il pulsante [Indicizza] nell'editor per vettorializzarle.")

    finally:
        await client.close()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Popola il DB di MementoAI con dati di test.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python scripts/seed.py                   # inserisce (skip se già presenti)
  python scripts/seed.py --reset           # pulisce tutto e reinserisce
  python scripts/seed.py --reset --no-user # reinserisce progetto + entry (utenti già presenti)
        """,
    )
    parser.add_argument("--reset", action="store_true", help="Cancella i dati esistenti prima di inserire")
    parser.add_argument("--no-user", action="store_true", dest="no_user", help="Non tocca la collection users")
    args = parser.parse_args()
    asyncio.run(seed(reset=args.reset, skip_user=args.no_user))


if __name__ == "__main__":
    main()