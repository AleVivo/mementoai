import json
import logging
from app.services import ollama

logger = logging.getLogger(__name__)

ENRICH_PROMPT = """Analizza il seguente testo tecnico e restituisci SOLO un oggetto JSON valido, senza testo aggiuntivo, senza markdown, senza backtick.

Il JSON deve avere esattamente questa struttura:
{{
  "summary": "riassunto in massimo 2 frasi",
  "tags": ["tag1", "tag2", "tag3"]
}}

Testo da analizzare:
{content}

Tag già presenti (non duplicare):
{existing_tags}

Summary già presente: {existing_summary}. 
Se il summary è già presente, mantieni lo stesso summary. Altrimenti, genera un nuovo summary.

Rispondi SOLO con il JSON."""

# DEPRECATED: enrich_entry non è più usata nella pipeline di indicizzazione.
# Il classifier LLM (summary + tag automatici) è stato rimosso da index_entry
# per ridurre la latenza. Summary e tag sono ora gestiti esclusivamente dall'utente
# tramite l'editor. Questo metodo è mantenuto per eventuali usi futuri o sperimentazioni.
async def enrich_entry(content: str, user_tags: list[str] | None, existing_summary: str | None = None) -> dict:
    existing_tags = user_tags or []
    logger.info(f"[classifier] enrich_entry — content: {len(content)} chars, existing_tags: {existing_tags}")

    prompt = ENRICH_PROMPT.format(
        content=content,
        existing_tags=", ".join(existing_tags),
        existing_summary=existing_summary or "",
    )

    raw_response = await ollama.generate_by_prompt(prompt)
    logger.info(f"[classifier] Raw response: {raw_response[:200]!r}{'...' if len(raw_response) > 200 else ''}")

    try:
        result = json.loads(raw_response)
        all_tags = list(set(existing_tags + result.get("tags", [])))
        enriched = {
            "summary": result.get("summary", ""),
            "tags": all_tags,
        }
        logger.info(f"[classifier] Enriched — summary: {enriched['summary'][:80]!r}, tags: {enriched['tags']}")
        return enriched
    except json.JSONDecodeError:
        logger.warning(f"[classifier] JSON parse failed on response: {raw_response!r}")
        return {"summary": "", "tags": existing_tags}