"""OpenRouter adapter using the OpenAI-compatible Chat Completions API."""

from typing import Protocol

from openai import OpenAI

from order_support.config import OpenRouterSettings


class ChatModelClient(Protocol):
    def complete(self, messages, tools):
        """Return one assistant message, including any requested tool calls."""

    def stream_complete(self, messages, tools):
        """Yield content deltas followed by the complete assistant message."""


class OpenRouterChatClient:
    def __init__(self, settings: OpenRouterSettings, sdk_client=None):
        self._model = settings.model
        self._client = sdk_client or OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
        )

    def complete(self, messages, tools):
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                parallel_tool_calls=False,
            )
        except Exception as error:
            raise RuntimeError("The model request failed") from error
        if not completion.choices:
            raise RuntimeError("The model returned no completion choices")

        return completion.choices[0].message.model_dump(exclude_none=True)

    def stream_complete(self, messages, tools):
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                parallel_tool_calls=False,
                stream=True,
            )
            content_parts = []
            tool_calls = {}

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    content_parts.append(content)
                    yield {"type": "content_delta", "delta": content}

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
        if tool_calls:
            message["tool_calls"] = [tool_calls[index] for index in sorted(tool_calls)]
        yield {"type": "message", "message": message}
