"""
Il ReAct loop. Questo file ha una sola responsabilità: orchestrare
la conversazione tra l'utente, il modello (Qwen) e i tool.

Non definisce tool, non definisce mapping — importa tutto dal registry.
"""

import json
import logging
from uuid import uuid4

from httpcore import request
from langfuse import observe, propagate_attributes

from app.observability import get_llm_callback_handler
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

            yield f"data: {json.dumps({'type': 'session', 'conversation_id': thread_id})}\n\n"

            input_state = {
                "messages": [HumanMessage(content=question)],
                "project_ids": project_ids,
                "conversation_id": thread_id,
            }
        
            steps: list[dict] = []
            
            async for chunk, metadata in graph.astream(
                input_state,
                config=config,
                stream_mode="messages",
            ):
                node = metadata.get("langgraph_node")

                if node == "agent" and isinstance(chunk, AIMessageChunk):

                    if chunk.tool_call_chunks:
                        # il modello sta costruendo una tool call
                        # emettiamo il nome del tool come reasoning
                        for tc in chunk.tool_call_chunks:
                            if tc.get("name"):
                                yield f"data: {json.dumps({'type': 'reasoning', 'content': tc['name']})}\n\n"
                                break

                    elif chunk.content:
                        # token della risposta finale
                        if isinstance(chunk.content, str):
                            full_response += chunk.content
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

                elif node == "tools" and isinstance(chunk, ToolMessage):
                    step = {
                        "tool": chunk.name,
                        "result": chunk.content,
                    }
                    steps.append(step)
                    yield f"data: {json.dumps({'type': 'step', 'tool': chunk.name, 'result': chunk.content}, ensure_ascii=False, default=str)}\n\n"

            # il grafo ha raggiunto END — emetti done
            model_name = "unknown"
            try:
                model_name = get_langchain_chat_provider().model
            except Exception:
                pass

            yield f"data: {json.dumps({'type': 'done', 'steps': steps, 'model': model_name})}\n\n"

        observation.update(output=full_response)