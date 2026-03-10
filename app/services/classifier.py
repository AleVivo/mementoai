import json
from app.services import ollama

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

async def enrich_entry(content: str, user_tags: list[str] | None, existing_summary: str | None = None) -> dict:
    existing_tags = user_tags or []
    prompt = ENRICH_PROMPT.format(content=content, existing_tags=", ".join(existing_tags), existing_summary=existing_summary or "")
    
    raw_response = await ollama.generate_by_prompt(prompt)

    try:
        result = json.loads(raw_response)
        all_tags = list(set(existing_tags + result.get("tags", [])))
        return {
            "summary": result.get("summary", ""),
            "tags": all_tags
        }
    except json.JSONDecodeError:
        return {
                    "summary": "",
                    "tags": existing_tags
                }