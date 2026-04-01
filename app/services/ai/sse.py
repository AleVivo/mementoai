"""
Helper per la formattazione degli eventi SSE.

Centralizza il formato `data: {...}\\n\\n` usato da rag_service e agent_service.

API pubblica: factory function tipizzate (es. token_event, step_event).
I TypedDict interni garantiscono che il payload serializzato sia sempre
well-formed — il type checker rifiuta campi mancanti o extra.
"""

import json
from typing import Literal, Union
from typing_extensions import TypedDict


# ── Payload types (interni) ────────────────────────────────────────────────────

class _SessionPayload(TypedDict):
    type: Literal["session"]
    conversation_id: str

class _TokenPayload(TypedDict):
    type: Literal["token"]
    content: str

class _ReasoningPayload(TypedDict):
    type: Literal["reasoning"]
    content: str

class _ToolStartPayload(TypedDict):
    type: Literal["tool_start"]
    tool: str

class _StepPayload(TypedDict):
    type: Literal["step"]
    tool: str
    result: object

class _SourcesPayload(TypedDict):
    type: Literal["sources"]
    sources: list[dict]

class _DonePayload(TypedDict, total=False):
    type: Literal["done"]  # type: ignore[misc]
    steps: list[dict]
    model: str

class _ErrorPayload(TypedDict):
    type: Literal["error"]
    message: str


_SsePayload = Union[
    _SessionPayload, _TokenPayload, _ReasoningPayload, _ToolStartPayload,
    _StepPayload, _SourcesPayload, _DonePayload, _ErrorPayload,
]


def _sse(payload: _SsePayload) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"


# ── Public API — factory functions ─────────────────────────────────────────────

def session_event(conversation_id: str) -> str:
    return _sse(_SessionPayload(type="session", conversation_id=conversation_id))

def token_event(content: str) -> str:
    return _sse(_TokenPayload(type="token", content=content))

def reasoning_event(content: str) -> str:
    return _sse(_ReasoningPayload(type="reasoning", content=content))

def tool_start_event(tool: str) -> str:
    return _sse(_ToolStartPayload(type="tool_start", tool=tool))

def step_event(tool: str, result: object) -> str:
    return _sse(_StepPayload(type="step", tool=tool, result=result))

def sources_event(sources: list[dict]) -> str:
    return _sse(_SourcesPayload(type="sources", sources=sources))

def done_event(steps: list[dict] | None = None, model: str | None = None) -> str:
    payload = _DonePayload(type="done")
    if steps is not None:
        payload["steps"] = steps
    if model is not None:
        payload["model"] = model
    return _sse(payload)

def error_event(e: Exception) -> str:
    return _sse(_ErrorPayload(type="error", message=str(e)))


