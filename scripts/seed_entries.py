"""
seed_entries.py — Inserisce le entry di demo.
"""

from datetime import datetime, timedelta, timezone
from bson import ObjectId

NOW = datetime.now(timezone.utc)

def weeks_ago(n: int) -> datetime:
    return NOW - timedelta(weeks=n)

def iso_week(dt: datetime) -> str:
    return f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"


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


async def run(
    db,
    project_id: ObjectId,
    user_ids: dict[str, ObjectId],
    user_names: dict[str, str],
) -> None:
    owner_id = user_ids.get("alex")
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

    if entries_to_insert:
        result = await db.entries.insert_many(entries_to_insert)
        print(f"✅ Inserite {len(result.inserted_ids)} entry")