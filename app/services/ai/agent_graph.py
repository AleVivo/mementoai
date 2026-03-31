from app.services.ai.agent_tools import (
    search_semantic, filter_entries, get_entry, count_entries
)
from app.services.ai.agent_state import AgentState
from app.services.llm import provider_cache

from langchain_core.messages import SystemMessage
from langgraph.prebuilt import tools_condition
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

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

tools = [search_semantic, filter_entries, get_entry, count_entries]

def agent_node(state: AgentState) -> dict:
    llm = provider_cache.get_langchain_chat_provider()
    llm_with_tools = llm.bind_tools(tools)
    
    messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}

def build_agent_graph():
    tool_node = ToolNode(tools)
    
    graph = StateGraph(AgentState)
    
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    
    graph.set_entry_point("agent")
    
    graph.add_conditional_edges(
        "agent",
        tools_condition,
    )
    
    graph.add_edge("tools", "agent")
    
    return graph.compile(checkpointer=MemorySaver())