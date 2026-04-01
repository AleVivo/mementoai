---
applyTo: "app/services/ai/**/*.py, app/services/retrieval/**/*.py, app/services/ingestion/**/*.py"
---

# AI Pipeline — LlamaIndex / LangGraph / LiteLLM Rules

## Provider Abstraction — Always Use the Cache

**Never instantiate LLM or embedding clients directly.** All AI calls go through the provider cache:

```python
# Good — reads the runtime-configured provider
from services.llm.provider_cache import get_langchain_chat_provider, get_embedding_provider

llm = get_langchain_chat_provider()
embed = get_embedding_provider()

# Bad — hardcodes a provider, breaks admin console switching
import ollama
ollama.chat(model="qwen2.5:7b", messages=[...])
```

The admin console can switch providers at runtime (Ollama → OpenAI → Groq) without restart. Code that bypasses the cache breaks this guarantee.

## LlamaIndex Settings

LlamaIndex global `Settings` are configured once by `config_handlers.py` at startup:
- `Settings.llm` → current `LiteLLMChatProvider`
- `Settings.embed_model` → current `LiteLLMEmbeddingProvider`

Within the AI pipeline, reference `Settings.llm` and `Settings.embed_model` — don't import the provider cache again inside LlamaIndex components.

## Chunking Hierarchy

Three-level hierarchy (do not change sizes without updating this comment):
```
Root   ~2048 tokens  — full section context
Middle  ~512 tokens  — paragraph-level
Leaf    ~128 tokens  — sentence-level (only leaves are embedded)
```

`AutoMergingRetriever` promotes sibling leaf nodes to their parent when ≥ threshold siblings match. This gives the LLM more context without bloating every embedding.

## SSE Streaming Pattern

The `@observe` decorator from Langfuse does not support `AsyncGenerator`. Always separate logic from transport:

```python
# Good — separates logic (observable) from transport (SSE generator)
async def _execute_rag(question: str, project_ids: list[str]) -> AsyncStreamingResponse:
    # ... LlamaIndex query engine call
    return response  # observable with @observe or start_as_current_observation

async def stream_rag(question: str, project_ids: list[str]) -> AsyncGenerator:
    response = await _execute_rag(question, project_ids)
    async for token in response.async_response_gen():
        yield f'data: {{"type":"token","content":"{token}"}}\n\n'
    yield 'data: {"type":"done"}\n\n'

# Bad — mixes logic and streaming, breaks Langfuse tracing
async def stream_rag(question: str) -> AsyncGenerator:
    with start_as_current_observation() as obs:
        async for token in engine.aquery_stream(question):  # can't observe a generator
            yield token
```

## LangGraph Agent Pattern

Agent state uses `TypedDict` with `add_messages` reducer:

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    project_ids: list[str]
    conversation_id: str
```

`project_ids` is injected via `InjectedState` into agent tools — never pass it as a tool argument from the LLM. This keeps project scoping invisible to the model and prevents prompt injection attacks.

Always compile the graph with `MemorySaver` for conversation persistence:
```python
graph = StateGraph(AgentState).compile(checkpointer=MemorySaver())
```

Use `thread_id = conversation_id` as the config key for `astream()`.

## Fallback Behavior

AI pipeline failures must degrade gracefully, never crash the endpoint:
- If embedding fails → return 503 with `{"detail": "Embedding service unavailable"}`.
- If LLM generation fails mid-stream → send `data: {"type":"error","message":"..."}` SSE event then close stream.
- If `$vectorSearch` returns 0 results → send an honest "no relevant entries found" response, not a hallucinated answer.

## Agent Tools

Agent tools are defined with `@tool` decorator and use `InjectedState` for project scoping:

```python
@tool
def search_semantic(query: str, project_ids: Annotated[list[str], InjectedState("project_ids")]) -> list[dict]:
    """Search the knowledge base semantically. Use when the question is about project content."""
    ...
```

Tool docstrings are the LLM's only guide on when to call the tool. Write them as instructions to the model, not as Python documentation.
