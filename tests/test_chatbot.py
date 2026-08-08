import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from order_support.chatbot import OrderChatbot
from order_support.repository import OrderRepository

DATA_PATH = Path(__file__).parents[1] / "data" / "orders.json"


class FakeMessage:
    def __init__(self, content: str | None, tool_calls: list[Any] | None = None) -> None:
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none: bool = True) -> dict[str, Any]:
        del exclude_none
        tool_call = self.tool_calls[0]
        return {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
            ],
        }


class FakeCompletions:
    def __init__(self, messages: list[FakeMessage]) -> None:
        self._messages = iter(messages)
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> Any:
        self.requests.append(request)
        return SimpleNamespace(choices=[SimpleNamespace(message=next(self._messages))])


class FakeClient:
    def __init__(self, completions: FakeCompletions) -> None:
        self.chat = SimpleNamespace(completions=completions)


def test_build_input_keeps_recent_text_messages() -> None:
    history = [
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "Show my orders"},
        {"role": "assistant", "content": {"path": "ignored.txt"}},
    ]

    messages = OrderChatbot._build_input(history, "Where is the latest one?")

    assert messages == [
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "Show my orders"},
        {"role": "user", "content": "Where is the latest one?"},
    ]


def test_reply_sends_tool_result_back_with_full_local_history(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="order_support.chatbot")
    repository = OrderRepository(DATA_PATH)
    tool_call = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="list_orders", arguments="{}"),
    )
    completions = FakeCompletions(
        [
            FakeMessage(content=None, tool_calls=[tool_call]),
            FakeMessage(content="Your latest order is ORD-1042.", tool_calls=[]),
        ]
    )
    chatbot = OrderChatbot(
        repository=repository,
        api_key="test-key",
        model="openai/gpt-5.4-mini",
        base_url="https://openrouter.ai/api/v1",
    )
    chatbot._client = FakeClient(completions)

    reply = chatbot.reply("What is my latest order?", [], "CUS-001")

    assert reply.text == "Your latest order is ORD-1042."
    assert reply.active_order_id == "ORD-1042"
    assert len(completions.requests) == 2
    second_request_messages = completions.requests[1]["messages"]
    assert [message["role"] for message in second_request_messages] == [
        "system",
        "user",
        "assistant",
        "tool",
    ]
    assert second_request_messages[-1]["tool_call_id"] == "call-1"
    assert "ORD-1042" in second_request_messages[-1]["content"]
    log_messages = [record.getMessage() for record in caplog.records]
    assert sum("model_call_completed" in message for message in log_messages) == 2
    assert any("tool_call_completed" in message for message in log_messages)
    assert any(
        "chat_turn_completed" in message and "model_calls=2 tool_calls=1" in message
        for message in log_messages
    )


def test_active_order_is_injected_for_a_follow_up() -> None:
    repository = OrderRepository(DATA_PATH)
    completions = FakeCompletions(
        [FakeMessage(content="Weather disruption caused the delay.", tool_calls=[])]
    )
    chatbot = OrderChatbot(
        repository=repository,
        api_key="test-key",
        model="openai/gpt-5.6-luna",
        base_url="https://openrouter.ai/api/v1",
    )
    chatbot._client = FakeClient(completions)

    reply = chatbot.reply(
        "What caused the delay?",
        [],
        "CUS-002",
        active_order_id="ORD-1098",
    )

    system_message = completions.requests[0]["messages"][0]["content"]
    assert "Current active order: ORD-1098" in system_message
    assert reply.active_order_id == "ORD-1098"


def test_active_order_cannot_cross_customer_boundary() -> None:
    repository = OrderRepository(DATA_PATH)
    completions = FakeCompletions([FakeMessage(content="Which order?", tool_calls=[])])
    chatbot = OrderChatbot(
        repository=repository,
        api_key="test-key",
        model="openai/gpt-5.6-luna",
        base_url="https://openrouter.ai/api/v1",
    )
    chatbot._client = FakeClient(completions)

    reply = chatbot.reply(
        "What caused the delay?",
        [],
        "CUS-001",
        active_order_id="ORD-1098",
    )

    system_message = completions.requests[0]["messages"][0]["content"]
    assert "Current active order: none" in system_message
    assert reply.active_order_id is None
