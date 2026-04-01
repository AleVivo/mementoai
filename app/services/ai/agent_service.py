"""
Il ReAct loop. Questo file ha una sola responsabilità: orchestrare
la conversazione tra l'utente, il modello (Qwen) e i tool.

Non definisce tool, non definisce mapping — importa tutto dal registry.
"""

import logging
from uuid import uuid4

from langfuse import observe, propagate_attributes

from app.observability import get_llm_callback_handler
from app.services.ai.sse import (
    session_event, token_event, reasoning_event,
    tool_start_event, step_event, done_event, error_event,
)
from app.services.llm.factory import get_langchain_chat_provider

from typing import AsyncGenerator

from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage

logger = logging.getLogger(__name__)

async def run_agent_stream(
    question: str,
    project_ids: list[str],
    graph,
    conversation_id: str | None = None,
) -> AsyncGenerator[str, None]:
    
    from langfuse import get_client

    langfuse = get_client()

    with langfuse.start_as_current_observation(
        name="agent_call",
        as_type="span",
        input={
            "question": question,
            "project_ids": project_ids,
            "conversation_id": conversation_id,
            }
    ) as observation:
        full_response = ""
    
        thread_id = conversation_id or str(uuid4())
        
        with propagate_attributes(session_id=thread_id):

            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "project_ids": project_ids,
                },
                "callbacks": [get_llm_callback_handler()]
            }

            yield session_event(thread_id)

            input_state = {
                "messages": [HumanMessage(content=question)],
                "project_ids": project_ids,
                "conversation_id": thread_id,
            }
        
            steps: list[dict] = []
            # Traccia l'indice delle tool call già annunciate al FE con tool_start.
            # tool_call_chunks arrivano in frammenti multipli per lo stesso indice;
            # emettiamo tool_start una sola volta per indice.
            announced_tool_indices: set[int] = set()

            try:
                async for chunk, metadata in graph.astream(
                    input_state,
                    config=config,
                    stream_mode="messages",
                ):
                    node = metadata.get("langgraph_node")

                    if node == "agent" and isinstance(chunk, AIMessageChunk):

                        # ── Reasoning/thinking tokens ──────────────────────────────────────
                        # Presente solo in modelli che lo supportano esplicitamente:
                        #   - DeepSeek-R1 / Qwen3 (thinking mode): reasoning_content in additional_kwargs
                        #   - Claude extended thinking: content è una lista di blocchi tipizzati
                        # Nei modelli standard (GPT-4, Llama3, Qwen2.5 base) questo ramo
                        # non produce nulla — comportamento corretto.

                        reasoning_text: str | None = (
                            chunk.additional_kwargs.get("reasoning_content")
                            or chunk.additional_kwargs.get("thinking")
                        )
                        if reasoning_text:
                            yield reasoning_event(reasoning_text)

                        # ── Contenuto del chunk ────────────────────────────────────────────
                        # content può essere str (modelli standard) o lista di blocchi
                        # tipizzati (Anthropic extended thinking).

                        if isinstance(chunk.content, list):
                            # Anthropic-style: lista di blocchi {"type": "thinking"|"text", ...}
                            for block in chunk.content:
                                if not isinstance(block, dict):
                                    continue
                                if block.get("type") == "thinking":
                                    thinking_text = block.get("thinking", "")
                                    if thinking_text:
                                        yield reasoning_event(thinking_text)
                                elif block.get("type") == "text":
                                    text = block.get("text", "")
                                    if text:
                                        full_response += text
                                        yield token_event(text)
                        elif chunk.content:
                            # Stringa semplice — token di risposta finale
                            full_response += chunk.content
                            yield token_event(chunk.content)

                        # ── Tool call in costruzione ───────────────────────────────────────
                        # Emettiamo tool_start alla prima occorrenza del nome per ogni indice.
                        # Il successivo evento `step` (da ToolMessage) porta il risultato.
                        if chunk.tool_call_chunks:
                            for tc in chunk.tool_call_chunks:
                                idx: int = tc.get("index") or 0
                                name = tc.get("name", "")
                                if name and idx not in announced_tool_indices:
                                    announced_tool_indices.add(idx)
                                    yield tool_start_event(name)

                    elif node == "tools" and isinstance(chunk, ToolMessage):
                        tool_name = chunk.name or ""
                        steps.append({"tool": tool_name, "result": chunk.content})
                        yield step_event(tool=tool_name, result=chunk.content)

                # il grafo ha raggiunto END — emetti done
                model_name = "unknown"
                try:
                    model_name = get_langchain_chat_provider().model
                except Exception:
                    pass

                yield done_event(steps=steps, model=model_name)

            except Exception as e:
                logger.exception(f"[agent] ERRORE durante lo stream: {e}")
                yield error_event(e)
                raise

        observation.update(output=full_response)