import json
import logging
from typing import Optional, AsyncGenerator

import litellm

from app.services.llm.base import EmbeddingProvider, ToolChatProvider

logger = logging.getLogger(__name__)

litellm.suppress_debug_info = True

class LiteLLMEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str, api_base: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.model = model
        self.api_base = api_base
        self.api_key = api_key

    async def embed(self, text: str) -> list[float]:
        logger.info(f"[litellm] embed — model: {self.model}, text length: {len(text)}")

        kwargs: dict = {"model": self.model, "input": text}
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.api_key:
            kwargs["api_key"] = self.api_key

        response = await litellm.aembedding(**kwargs)

        embedding = response.data[0]["embedding"]
        logger.info(f"[litellm] embed — vector dims: {len(embedding)}")
        return embedding

class LiteLLMChatProvider(ToolChatProvider):
    def __init__(self, model: str, api_base: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.model = model
        self.api_base = api_base
        self.api_key = api_key

    def _base_kwargs(self) -> dict:
        """Parametri comuni a tutte le chiamate LiteLLM."""
        kwargs: dict = {"model": self.model}
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.api_key:
            kwargs["api_key"] = self.api_key
        return kwargs

    async def stream_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        full_messages = self._build_messages(messages, system_prompt)

        response = await litellm.acompletion(
            **self._base_kwargs(),
            messages=full_messages,
            stream=True
        )

        async for chunk in response: # type: ignore[assignment]
            token = chunk.choices[0].delta.content
            if token:
                yield token

    async def stream_chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        full_messages = self._build_messages(messages, system_prompt)

        tool_call_buffer: dict[int,dict] = {}
        has_tool_calls = False

        response = await litellm.acompletion(
            **self._base_kwargs(),
            messages=full_messages,
            tools=tools,
            stream=True
        )

        async for chunk in response: # type: ignore[assignment]
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            # Token di testo (reasoning intermedio o risposta finale)
            if delta.content:
                yield {"type": "token", "content": delta.content}

            # Frammenti di tool_call — accumula finché non sono completi
            if delta.tool_calls:
                has_tool_calls = True
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_call_buffer:
                        tool_call_buffer[idx] = {
                            "id": tc_delta.id or f"call_{idx}",
                            "name": "",
                            "args_str": "",
                        }
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_call_buffer[idx]["name"] += tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_call_buffer[idx]["args_str"] += tc_delta.function.arguments

            if finish_reason in ("stop", "tool_calls", "length"):
                break

        # Emetti le tool_calls complete dopo la fine dello stream
        for tc in tool_call_buffer.values():
            try:
                args = json.loads(tc["args_str"]) if tc["args_str"] else {}
            except json.JSONDecodeError:
                args = {"_raw": tc["args_str"]}
                logger.warning(f"[litellm] tool_call args non parsabili: {tc['args_str']}")

            yield {
                "type": "tool_call",
                "name": tc["name"],
                "args": args,
                "id": tc["id"],
            }

        yield {"type": "done", "has_tool_calls": has_tool_calls}

    def build_assistant_message(self, content: str, tool_calls: list[dict]) -> dict:
        return {
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": tc["id"] or f"call_{tc['name']}",
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["args"], ensure_ascii=False),
                    },
                }
                for tc in tool_calls
            ],
        }

    def build_tool_message(self, tool_call: dict, result) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tc_id if (tc_id := tool_call.get("id")) else f"call_{tool_call['name']}",
            "content": json.dumps(result, ensure_ascii=False, default=str),
        }

    @staticmethod
    def _build_messages(messages: list[dict], system_prompt: Optional[str]) -> list[dict]:
        if system_prompt:
            return [{"role": "system", "content": system_prompt}, *messages]
        return messages