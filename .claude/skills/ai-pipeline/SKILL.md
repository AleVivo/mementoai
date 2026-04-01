---
name: ai-pipeline
description: Pattern AI pipeline per app/services/ai/, retrieval/, ingestion/ — provider cache, SSE, LlamaIndex, agent tools
type: project
---

# AI Pipeline Patterns — MementoAI

Si attiva automaticamente quando lavori su file in `app/services/ai/`, `app/services/retrieval/`,
o `app/services/ingestion/`.

## Provider cache — regola assoluta

Mai istanziare LLM o embedding model direttamente. Sempre via @app/services/llm/provider_cache.py:

```python
# CORRETTO
from app.services.llm.provider_cache import get_llm, get_embed_model

llm = get_llm()
embed_model = get_embed_model()

# SBAGLIATO — non hardcodare provider o model name
from litellm import completion          # NO
from llama_index.llms.ollama import Ollama  # NO
llm = Ollama(model="qwen2.5:7b")       # NO
```

Il provider è configurato a runtime dall'admin console. `provider_cache.py` risponde agli
eventi di config change via `app/handlers/config_handlers.py`.

## SSE separation pattern

`@observe` di Langfuse non supporta `AsyncGenerator`. Pattern obbligatorio in tutti i service AI:

```python
# STRUTTURA OBBLIGATORIA
@observe(name="rag_query")              # decorabile — non è un generator
async def _execute_rag(self, request: ChatRequest) -> str:
    # logica AI: retrieve, rerank, LLM call
    return full_response

async def stream_rag(self, request: ChatRequest) -> AsyncGenerator[str, None]:
    # wrappa _execute_rag come SSE — non decorare con @observe
    result = await self._execute_rag(request)
    for chunk in self._format_as_sse(result):
        yield chunk
```

Formattazione SSE centralizzata in @app/services/ai/sse.py.
File canonico: @app/services/ai/rag_service.py

## LlamaIndex chunking gerarchico

Pipeline in @app/services/ingestion/pipeline.py:

```
HierarchicalNodeParser
  2048 token  ← parent level 1
    512 token ← parent level 2
      128 token ← LEAF — embeddati e salvati in MongoDB
```

- Solo i **leaf node** (128 token) vengono embeddati e salvati in `chunks` collection
- **`AutoMergingRetriever`** (in @app/services/retrieval/retriever.py) recupera leaf nodes
  e promuove automaticamente al parent se un numero sufficiente di leaf dello stesso parent
  è rilevante — fornisce contesto più ampio senza over-retrieve

**Non modificare le soglie 2048/512/128 senza misurare l'impatto sul recall.**

## InjectedState per project_ids negli agent tool

I tool dell'agent non ricevono `project_ids` come argomento LLM (sarebbe esponibile nel prompt).
Viene iniettato via `InjectedState` di LangGraph:

```python
# CORRETTO — in app/services/ai/agent_tools.py
async def search_knowledge_base(
    query: str,
    state: Annotated[AgentState, InjectedState]  # project_ids qui
) -> str:
    project_ids = state["project_ids"]  # non passato dall'LLM

# SBAGLIATO
async def search_knowledge_base(query: str, project_ids: list[str]) -> str:
    ...  # project_ids sarebbe visibile al LLM come argomento
```

File canonici: @app/services/ai/agent_state.py | @app/services/ai/agent_tools.py | @app/services/ai/agent_graph.py

## Langfuse tracing

- Wrappa le funzioni AI (non AsyncGenerator) con `@observe(name="...")`
- Setup in @app/observability/langfuse_integration.py
- Trace esistenti: `rag_query`, `agent_run`, `retrieval`
- Non aggiungere `@observe` su `stream_*` — rompe lo streaming

## Fallback su errori AI

Se il LLM provider fallisce:
1. Log `warning` con dettaglio errore
2. Ritorna messaggio user-friendly via SSE: `data: {"type": "error", "content": "..."}`
3. Non propagare l'eccezione raw al client
