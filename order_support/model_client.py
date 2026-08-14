"""OpenRouter adapter using the OpenAI-compatible Chat Completions API."""

from typing import Protocol

from openai import OpenAI

from order_support.config import OpenRouterSettings


# Cap a single upstream request. OpenRouter can route to a slow/overloaded
# provider; without this the OpenAI SDK would wait up to its 600s default.
REQUEST_TIMEOUT_SECONDS = 30.0


class ChatModelClient(Protocol):
    def complete(self, messages, tools):
        """Return one assistant message, including any requested tool calls."""

    def stream_complete(self, messages, tools):
        """Yield content deltas followed by the complete assistant message."""


class OpenRouterChatClient:
    def __init__(self, settings: OpenRouterSettings, model, provider=None, sdk_client=None):
        self._model = model
        self._provider = dict(provider or {})
        self._client = sdk_client or OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def complete(self, messages, tools):
        request = {
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }
        if self._provider:
            request["extra_body"] = {"provider": self._provider}
        try:
            completion = self._client.chat.completions.create(**request)
        except Exception as error:
            raise RuntimeError("The model request failed") from error
        if not completion.choices:
            raise RuntimeError("The model returned no completion choices")

        return completion.choices[0].message.model_dump(exclude_none=True)

    def stream_complete(self, messages, tools):
        request = {
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "stream": True,
        }
        if self._provider:
            request["extra_body"] = {"provider": self._provider}
        try:
            stream = self._client.chat.completions.create(**request)
            content_parts = []
            reasoning_parts = []
            reasoning_details = []
            reasoning_detail_indexes = {}
            tool_calls = {}

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    content_parts.append(content)
                    yield {"type": "content_delta", "delta": content}

                reasoning = getattr(delta, "reasoning", None) or getattr(
                    delta,
                    "reasoning_content",
                    None,
                )
                if reasoning:
                    reasoning_parts.append(reasoning)

                for detail in getattr(delta, "reasoning_details", None) or []:
                    if hasattr(detail, "model_dump"):
                        dumped_detail = detail.model_dump(exclude_none=True)
                    elif isinstance(detail, dict):
                        dumped_detail = dict(detail)
                    else:
                        continue
                    detail_index = dumped_detail.get("index")
                    if not isinstance(detail_index, int):
                        reasoning_details.append(dumped_detail)
                        continue
                    existing_position = reasoning_detail_indexes.get(detail_index)
                    if existing_position is None:
                        reasoning_detail_indexes[detail_index] = len(reasoning_details)
                        reasoning_details.append(dumped_detail)
                        continue
                    existing = reasoning_details[existing_position]
                    for key, value in dumped_detail.items():
                        if (
                            key in {"data", "summary", "text"}
                            and isinstance(existing.get(key), str)
                            and isinstance(value, str)
                        ):
                            existing[key] += value
                        else:
                            existing[key] = value

                for tool_call in getattr(delta, "tool_calls", None) or []:
                    index = tool_call.index
                    assembled = tool_calls.setdefault(
                        index,
                        {
                            "id": None,
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        },
                    )
                    if tool_call.id:
                        assembled["id"] = tool_call.id
                    if tool_call.type:
                        assembled["type"] = tool_call.type
                    function = tool_call.function
                    if function is not None:
                        if function.name:
                            assembled["function"]["name"] += function.name
                        if function.arguments:
                            assembled["function"]["arguments"] += function.arguments
        except Exception as error:
            raise RuntimeError("The model request failed") from error

        message = {
            "role": "assistant",
            "content": "".join(content_parts) or None,
        }
        if reasoning_parts:
            message["reasoning"] = "".join(reasoning_parts)
        if reasoning_details:
            message["reasoning_details"] = reasoning_details
        if tool_calls:
            message["tool_calls"] = [tool_calls[index] for index in sorted(tool_calls)]
        yield {"type": "message", "message": message}
