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

from typing import AsyncGenerator

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
# DEPRECATED - non chiamato da nessun router, mantenuto solo per riferimento fino a quando non siamo sicuri di non averne più bisogno
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
    
# ---------------------------------------------------------------------------
# ReAct loop - Streaming
# ---------------------------------------------------------------------------
    
async def run_agent_stream(question: str, project: Optional[str] = None, max_steps: int = 5) -> AsyncGenerator[str, None]:
    """
    ReAct loop in streaming.

    Comportamento di Ollama con stream=True + tools (API /api/chat, marzo 2026):
      · Chunk done=false, content="token" → token di reasoning del modello
      · Chunk done=false, tool_calls=[...], content="" → decisione tool (i tool_calls
        arrivano in un chunk INTERMEDIO, NON nel chunk done=true)
      · Chunk done=true, content="" → segnale di fine, sempre vuoto in presenza di tool_calls

    Strategia per ogni step:
      - Buffer accumula i content tokens durante lo streaming
      - tool_calls vengono catturati dai chunk intermedi (done=false)
      - Se lo step produce tool_calls:
          · Il buffer (eventuale reasoning) viene emesso come evento 'reasoning'
          · Ogni tool viene eseguito → evento 'step' inviato in real-time
      - Se lo step NON produce tool_calls (risposta finale):
          · Il buffer viene re-emesso come eventi 'token' uno per uno (word-by-word)
    - Fallback max_steps: stream=True senza tools → token reali in real-time
    """
    steps: list[dict] = []
    messages = [{"role": "user", "content": question}]

    system_prompt = AGENT_SYSTEM_PROMPT
    if project:
        system_prompt += PROJECT_CONTEXT_SNIPPET.format(project=project)

    async with httpx.AsyncClient(timeout=None) as client:

        for step_num in range(max_steps):
            logger.info(f"[agent] Step {step_num + 1}/{max_steps}")

            buffer = ""
            tool_calls = None

            async with client.stream(
                "POST",
                f"{settings.ollama_url}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        *messages,
                    ],
                    "tools": TOOLS,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    msg = chunk.get("message", {})

                    # Accumula content tokens (reasoning prima della tool call)
                    token = msg.get("content", "")
                    if token:
                        buffer += token

                    # I tool_calls arrivano in chunk intermedi (done=false), non nel chunk done=true
                    if msg.get("tool_calls"):
                        tool_calls = msg["tool_calls"]

                    if chunk.get("done"):
                        break

            # Ricostruisce assistant_message per la conversation history
            assistant_message: dict = {"role": "assistant", "content": buffer}
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
            messages.append(assistant_message)

            if not tool_calls:
                # Risposta finale — re-emetti il buffer come token word-by-word
                logger.info(f"[agent] Direct answer after {step_num + 1} step(s)")
                words = buffer.split(" ")
                for i, word in enumerate(words):
                    content = word if i == len(words) - 1 else word + " "
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'steps': steps, 'model': AGENT_MODEL})}\n\n"
                return

            # tool_calls presente — emetti il reasoning accumulato (spesso vuoto per qwen2.5)
            if buffer:
                yield f"data: {json.dumps({'type': 'reasoning', 'content': buffer})}\n\n"

            # Esegui ogni tool e invia evento 'step' in real-time
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                raw_args = tool_call["function"]["arguments"]
                tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                logger.info(f"[agent] Tool call: {tool_name}({tool_args})")

                tool_fn = TOOL_FUNCTIONS.get(tool_name)
                if tool_fn is None:
                    tool_result = {"error": f"Tool '{tool_name}' non trovato"}
                    logger.warning(f"[agent] Unknown tool: {tool_name}")
                else:
                    try:
                        tool_result = await tool_fn(**tool_args)
                        logger.info(f"[agent] Tool {tool_name} returned {type(tool_result).__name__}")
                    except Exception as e:
                        tool_result = {"error": str(e)}
                        logger.error(f"[agent] Tool {tool_name} raised: {e}")

                steps.append({"tool": tool_name, "args": tool_args, "result": tool_result})

                yield f"data: {json.dumps({'type': 'step', 'tool': tool_name, 'args': tool_args, 'result': tool_result}, ensure_ascii=False, default=str)}\n\n"

                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                })

        # Fallback: max_steps raggiunto — risposta finale senza tools, stream=True reale
        logger.warning(f"[agent] Max steps ({max_steps}) reached — forcing final answer")
        async with client.stream(
            "POST",
            f"{settings.ollama_url}/api/chat",
            json={
                "model": AGENT_MODEL,
                "messages": [
                    {"role": "system", "content": AGENT_SYSTEM_PROMPT + "\nRispondi ora con quello che hai raccolto."},
                    *messages,
                ],
                "stream": True,
            },
        ) as final:
            final.raise_for_status()
            async for line in final.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                if chunk.get("done"):
                    break
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'steps': steps, 'model': AGENT_MODEL})}\n\n"