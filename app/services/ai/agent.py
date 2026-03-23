"""
Il ReAct loop. Questo file ha una sola responsabilità: orchestrare
la conversazione tra l'utente, il modello (Qwen) e i tool.

Non definisce tool, non definisce mapping — importa tutto dal registry.
"""

import json
import logging

from langfuse import get_client, observe

from app.services.ai import agent_registry
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

_PROJECT_SCOPED_TOOLS = {"search_semantic", "filter_entries", "count_entries"}

# ---------------------------------------------------------------------------
# ReAct loop - Streaming
# ---------------------------------------------------------------------------

@observe(name="agent_step")
async def _run_agent_step(
    step_num: int,
    messages: list[dict],
    project_ids: list[str],
    provider,
) -> dict:
    """
    Esegue un singolo step del ReAct loop e ritorna un dizionario con:
      - buffer: testo di reasoning accumulato
      - tool_calls: lista delle tool call richieste dall'LLM
      - tool_results: lista dei risultati dei tool eseguiti
      - has_final_answer: True se lo step ha prodotto una risposta finale
 
    Tracciato con @observe — ogni step appare come span figlia del trace
    principale run_agent_stream, con input (messages) e output (tool_calls/risposta).
    """
    langfuse = get_client()
    logger.info(f"[agent] Step {step_num}")
 
    buffer = ""
    tool_calls: list[dict] = []
 
    async for event in provider.stream_chat_with_tools(
        messages=messages,
        tools=agent_registry.TOOLS,
        system_prompt=AGENT_SYSTEM_PROMPT,
    ):
        if event["type"] == "token":
            buffer += event["content"]
        elif event["type"] == "tool_call":
            tool_calls.append(event)
 
    tool_results: list[dict] = []
 
    if tool_calls:
        # Esegui ogni tool e raccogli i risultati
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_fn = agent_registry.TOOL_FUNCTIONS.get(tool_name)
 
            logger.info(f"[agent] Tool call: {tool_name}({tool_args})")
 
            if tool_fn is None:
                tool_result = {"error": f"Tool '{tool_name}' non trovato"}
                logger.warning(f"[agent] Unknown tool: {tool_name}")
            else:
                try:
                    if tool_name in _PROJECT_SCOPED_TOOLS:
                        tool_result = await tool_fn(**tool_args, project_ids=project_ids)
                    else:
                        tool_result = await tool_fn(**tool_args)
                except Exception as e:
                    tool_result = {"error": str(e)}
                    logger.error(f"[agent] Tool {tool_name} raised: {e}")
 
            tool_results.append({
                "tool": tool_name,
                "args": tool_args,
                "result": tool_result,
            })
 
    # Aggiorna la span con i dettagli dello step — visibili nella dashboard
    langfuse.update_current_span(
        input={"step": step_num, "messages_count": len(messages)},
        output={
            "reasoning": buffer[:500] if buffer else None,  # tronca per leggibilità
            "tool_calls": [{"name": tc["name"], "args": tc["args"]} for tc in tool_calls],
            "has_final_answer": not bool(tool_calls),
        },
        metadata={
            "tools_called": [tc["name"] for tc in tool_calls],
            "tool_results_count": len(tool_results),
        },
    )
 
    return {
        "buffer": buffer,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "has_final_answer": not bool(tool_calls),
    }
    
async def run_agent_stream(
    question: str,
    project_ids: list[str],
    max_steps: int = 5,
) -> AsyncGenerator[str, None]:
    """
    ReAct loop in streaming.
 
    Struttura del trace in Langfuse:
      run_agent_stream (trace root — span aperta manualmente)
        ├─ agent_step (step 1 — @observe)
        ├─ agent_step (step 2 — @observe)
        └─ agent_step (step N — risposta finale)
 
    Usiamo start_observation manuale invece di @observe perché questa
    funzione è un AsyncGenerator (contiene yield) — @observe non supporta
    funzioni con yield.
    """
    from app.observability import langfuse_integration
 
    langfuse = get_client()
    root_span = None
 
    if langfuse_integration.is_active():
        root_span = langfuse.start_observation(
            as_type="span",
            name="run_agent_stream",
            input={"question": question, "project_ids": project_ids, "max_steps": max_steps},
        )
 
    steps: list[dict] = []
    messages = [{"role": "user", "content": question}]
    provider = get_chat_provider()
 
    try:
        for step_num in range(1, max_steps + 1):
 
            # _run_agent_step è @observe — diventa span figlia di root_span
            # grazie al contesto OTEL attivo
            step_result = await _run_agent_step(
                step_num=step_num,
                messages=messages,
                project_ids=project_ids,
                provider=provider,
            )
 
            buffer = step_result["buffer"]
            tool_calls = step_result["tool_calls"]
            tool_results = step_result["tool_results"]
 
            # Aggiorna conversation history
            if tool_calls:
                messages.append(provider.build_assistant_message(buffer, tool_calls))
            else:
                messages.append({"role": "assistant", "content": buffer})
 
            if step_result["has_final_answer"]:
                # Risposta finale — re-emetti il buffer come token word-by-word
                logger.info(f"[agent] Direct answer after {step_num} step(s)")
                words = buffer.split(" ")
                for i, word in enumerate(words):
                    content = word if i == len(words) - 1 else word + " "
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
 
                yield f"data: {json.dumps({'type': 'done', 'steps': steps, 'model': getattr(provider, 'model', 'unknown')})}\n\n"
                return
 
            # Emetti reasoning (spesso vuoto per qwen2.5)
            if buffer:
                yield f"data: {json.dumps({'type': 'reasoning', 'content': buffer})}\n\n"
 
            # Emetti ogni tool result come evento 'step' in real-time
            for tr in tool_results:
                steps.append(tr)
                yield f"data: {json.dumps({'type': 'step', 'tool': tr['tool'], 'args': tr['args'], 'result': tr['result']}, ensure_ascii=False, default=str)}\n\n"
                messages.append(provider.build_tool_message(
                    {"name": tr["tool"], "id": tool_calls[tool_results.index(tr)].get("id")},
                    tr["result"],
                ))
 
        # Fallback: max_steps raggiunto
        logger.warning(f"[agent] Max steps ({max_steps}) reached — forcing final answer")
        async for token in provider.stream_chat(
            messages=messages,
            system_prompt=AGENT_SYSTEM_PROMPT + "\nRispondi ora con quello che hai raccolto.",
        ):
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
 
        yield f"data: {json.dumps({'type': 'done', 'steps': steps, 'model': getattr(provider, 'model', 'unknown')})}\n\n"
 
    finally:
        # Il finally garantisce che il trace venga sempre chiuso,
        # anche in caso di eccezione a metà stream
        if root_span:
            root_span.update(
                output={
                    "steps_executed": len(steps),
                    "tools_used": list({s["tool"] for s in steps}),
                }
            )
            root_span.end()