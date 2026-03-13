"""
Il ReAct loop. Questo file ha una sola responsabilità: orchestrare
la conversazione tra l'utente, il modello (Qwen) e i tool.

Non definisce tool, non definisce mapping — importa tutto dal registry.
"""

import json
import logging
from typing import Optional
import httpx
from app.config import settings
from app.services.agent_registry import TOOLS, TOOL_FUNCTIONS

logger = logging.getLogger(__name__)

AGENT_MODEL = "qwen2.5:7b"

# ---------------------------------------------------------------------------
# System prompt dell'agente
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """Sei un assistente per una knowledge base tecnica di un team di sviluppo.
La knowledge base contiene decisioni architetturali (ADR), post-mortem e aggiornamenti di progetto.

Hai accesso a tool per interrogare la knowledge base. Usali quando necessario per rispondere
in modo accurato. Puoi usare più tool in sequenza se la domanda lo richiede.

Quando rispondi:
- Cita le entry specifiche che hai trovato (titolo e tipo)
- Sii conciso ma completo
- Se non trovi informazioni rilevanti, dillo chiaramente
- Rispondi in italiano
"""

PROJECT_CONTEXT_SNIPPET = """
Contesto attivo: stai operando sul progetto "{project}".
Quando usi i tool, applica questo progetto come filtro predefinito
a meno che la domanda non riguardi esplicitamente altri progetti.
"""

# ---------------------------------------------------------------------------
# ReAct loop
# ---------------------------------------------------------------------------

async def run_agent(question: str, project: Optional[str] = None, max_steps: int = 5) -> dict:
    """
    Esegue il ReAct loop per rispondere alla domanda dell'utente.

    Args:
        question:  domanda in linguaggio naturale
        project:   progetto attivo (opzionale)
        max_steps: numero massimo di tool call prima di forzare la risposta

    Returns:
        {"answer": str, "steps": list[dict], "model": str}
    """
    steps: list[dict] = []
    messages = [{"role": "user", "content": question}]

    system_prompt = AGENT_SYSTEM_PROMPT
    if project:
        system_prompt += PROJECT_CONTEXT_SNIPPET.format(project=project)

    async with httpx.AsyncClient(timeout=None) as client:

        for step_num in range(max_steps):
            logger.info(f"[agent] Step {step_num + 1}/{max_steps}")

            response = await client.post(
                f"{settings.ollama_url}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        *messages,
                    ],
                    "tools": TOOLS,   # <-- viene dal registry
                    "stream": False,
                },
            )
            response.raise_for_status()

            assistant_message = response.json()["message"]
            tool_calls = assistant_message.get("tool_calls")

            # Nessun tool call → Qwen ha risposto direttamente → fine loop
            if not tool_calls:
                answer = assistant_message.get("content", "")
                logger.info(f"[agent] Direct answer after {step_num + 1} step(s)")
                return {"answer": answer, "steps": steps, "model": AGENT_MODEL}

            # Qwen vuole usare uno o più tool
            # Aggiungiamo il messaggio dell'assistant alla conversazione prima
            # di eseguire i tool — Qwen ha bisogno di vedere la propria richiesta
            # per contestualizzare i risultati che arriveranno nel prossimo giro
            messages.append(assistant_message)

            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                raw_args = tool_call["function"]["arguments"]
                tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                logger.info(f"[agent] Tool call: {tool_name}({tool_args})")

                tool_fn = TOOL_FUNCTIONS.get(tool_name)  # <-- viene dal registry
                if tool_fn is None:
                    tool_result = {"error": f"Tool '{tool_name}' non trovato"}
                    logger.warning(f"[agent] Unknown tool requested: {tool_name}")
                else:
                    try:
                        tool_result = await tool_fn(**tool_args)
                        logger.info(f"[agent] Tool {tool_name} returned {type(tool_result).__name__}")
                    except Exception as e:
                        tool_result = {"error": str(e)}
                        logger.error(f"[agent] Tool {tool_name} raised: {e}")

                steps.append({"tool": tool_name, "args": tool_args, "result": tool_result})

                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                })

        # Fallback: max_steps raggiunto — forziamo una risposta senza tool
        logger.warning(f"[agent] Max steps ({max_steps}) reached — forcing final answer")
        final = await client.post(
            f"{settings.ollama_url}/api/chat",
            json={
                "model": AGENT_MODEL,
                "messages": [
                    {"role": "system", "content": AGENT_SYSTEM_PROMPT + "\nRispondi ora con quello che hai raccolto."},
                    *messages,
                ],
                "stream": False,
            },
        )
        final.raise_for_status()
        return {
            "answer": final.json()["message"].get("content", "Impossibile generare una risposta."),
            "steps": steps,
            "model": AGENT_MODEL,
        }