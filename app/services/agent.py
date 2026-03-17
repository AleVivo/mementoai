"""
Il ReAct loop. Questo file ha una sola responsabilità: orchestrare
la conversazione tra l'utente, il modello (Qwen) e i tool.

Non definisce tool, non definisce mapping — importa tutto dal registry.
"""

import json
import logging
from typing import Optional
from app.services.agent_registry import TOOLS, TOOL_FUNCTIONS
from app.services.llm.factory import get_chat_provider

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
# ReAct loop - Streaming
# ---------------------------------------------------------------------------
    
async def run_agent_stream(question: str, project: Optional[str] = None, max_steps: int = 5) -> AsyncGenerator[str, None]:
    """
    ReAct loop in streaming.

    Comportamento del provider con stream_chat_with_tools:
      · evento {"type": "token",     "content": "..."}          → token di reasoning
      · evento {"type": "tool_call", "name": "...", "args": {}} → decisione tool
      · evento {"type": "done",      "has_tool_calls": bool}    → fine stream del passo

    Strategia per ogni step (identica all'originale):
      - buffer accumula i token durante lo streaming
      - tool_calls vengono catturati dagli eventi "tool_call"
      - Se lo step produce tool_calls:
          · Il buffer (eventuale reasoning) viene emesso come evento 'reasoning'
          · Ogni tool viene eseguito → evento 'step' inviato in real-time
      - Se lo step NON produce tool_calls (risposta finale):
          · Il buffer viene re-emesso come eventi 'token' word-by-word
      - Fallback max_steps: stream_chat senza tools → token reali in real-time
    """
    steps: list[dict] = []
    messages = [{"role": "user", "content": question}]

    system_prompt = AGENT_SYSTEM_PROMPT
    if project:
        system_prompt += PROJECT_CONTEXT_SNIPPET.format(project=project)

    provider = get_chat_provider()

    for step_num in range(max_steps):
        logger.info(f"[agent] Step {step_num + 1}/{max_steps}")

        buffer = ""
        tool_calls: list[dict] = []

        async for event in provider.stream_chat_with_tools(
            messages=messages,
            tools=TOOLS,
            system_prompt=system_prompt,
        ):
            if event["type"] == "token":
                # Accumula — nel tuo originale non veniva emesso subito durante i passi intermedi
                buffer += event["content"]
            elif event["type"] == "tool_call":
                tool_calls.append(event)

            # "done" è il segnale di fine stream del provider — non serve gestirlo qui,
            # usciamo dal loop naturalmente

        # Ricostruisce assistant_message per la conversation history.
        # Delegato al provider perché il formato wire è diverso tra Ollama e OpenAI:
        #   - Ollama: {"type": "function", ...} senza id obbligatorio
        #   - OpenAI: {"id": "call_xyz", "type": "function", ...} con id obbligatorio
        if tool_calls:
            messages.append(provider.build_assistant_message(buffer, tool_calls))
        else:
            messages.append({"role": "assistant", "content": buffer})

        if not tool_calls:
            # Risposta finale — re-emetti il buffer come token word-by-word
            logger.info(f"[agent] Direct answer after {step_num + 1} step(s)")
            words = buffer.split(" ")
            for i, word in enumerate(words):
                content = word if i == len(words) - 1 else word + " "
                yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'steps': steps, 'model': getattr(provider, 'model', 'unknown')})}\n\n"
            return

        # tool_calls presente — emetti il reasoning accumulato (spesso vuoto per qwen2.5)
        if buffer:
            yield f"data: {json.dumps({'type': 'reasoning', 'content': buffer})}\n\n"

        # Esegui ogni tool e invia evento 'step' in real-time
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

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

            messages.append(provider.build_tool_message(tool_call, tool_result))


        # Fallback: max_steps raggiunto — risposta finale senza tools, stream=True reale
    logger.warning(f"[agent] Max steps ({max_steps}) reached — forcing final answer")
    async for token in provider.stream_chat(
        messages=messages,
        system_prompt=AGENT_SYSTEM_PROMPT + "\nRispondi ora con quello che hai raccolto.",
    ):
        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

    yield f"data: {json.dumps({'type': 'done', 'steps': steps, 'model': getattr(provider, 'model', 'unknown')})}\n\n"