"""OpenRouter adapter using the OpenAI-compatible Chat Completions API."""

from typing import Protocol

from openai import OpenAI

from order_support.config import OpenRouterSettings


class ChatModelClient(Protocol):
    def complete(self, messages, tools):
        """Return one assistant message, including any requested tool calls."""


class OpenRouterChatClient:
    def __init__(self, settings: OpenRouterSettings, sdk_client=None):
        self._model = settings.model
        self._client = sdk_client or OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
        )

    def complete(self, messages, tools):
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=False,
        )
        if not completion.choices:
            raise RuntimeError("The model returned no completion choices")

        return completion.choices[0].message.model_dump(exclude_none=True)
