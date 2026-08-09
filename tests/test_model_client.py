import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from order_support.config import OpenRouterSettings
from order_support.model_client import OpenRouterChatClient


class ModelClientTests(unittest.TestCase):
    def test_sends_history_and_tools_to_openrouter_compatible_client(self):
        assistant_message = Mock()
        assistant_message.model_dump.return_value = {
            "role": "assistant",
            "content": "Done",
        }
        sdk_client = Mock()
        sdk_client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=assistant_message)]
        )
        client = OpenRouterChatClient(
            OpenRouterSettings(
                api_key="test-key",
                model="test/model",
                base_url="https://example.test/v1",
            ),
            sdk_client=sdk_client,
        )
        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"type": "function", "function": {"name": "test_tool"}}]

        result = client.complete(messages, tools)

        self.assertEqual(result, {"role": "assistant", "content": "Done"})
        sdk_client.chat.completions.create.assert_called_once_with(
            model="test/model",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=False,
        )

    def test_streams_text_and_reassembles_the_assistant_message(self):
        sdk_client = Mock()
        sdk_client.chat.completions.create.return_value = iter(
            [
                SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(content="Your ", tool_calls=None)
                        )
                    ]
                ),
                SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(content="order shipped.", tool_calls=None)
                        )
                    ]
                ),
            ]
        )
        client = OpenRouterChatClient(
            OpenRouterSettings(
                api_key="test-key",
                model="test/model",
                base_url="https://example.test/v1",
            ),
            sdk_client=sdk_client,
        )

        events = list(client.stream_complete([], []))

        self.assertEqual(
            events,
            [
                {"type": "content_delta", "delta": "Your "},
                {"type": "content_delta", "delta": "order shipped."},
                {
                    "type": "message",
                    "message": {
                        "role": "assistant",
                        "content": "Your order shipped.",
                    },
                },
            ],
        )
        sdk_client.chat.completions.create.assert_called_once_with(
            model="test/model",
            messages=[],
            tools=[],
            tool_choice="auto",
            parallel_tool_calls=False,
            stream=True,
        )

    def test_reassembles_streamed_tool_call_deltas(self):
        def tool_delta(call_id, name, arguments):
            return SimpleNamespace(
                index=0,
                id=call_id,
                type="function" if call_id else None,
                function=SimpleNamespace(name=name, arguments=arguments),
            )

        sdk_client = Mock()
        sdk_client.chat.completions.create.return_value = iter(
            [
                SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(
                                content=None,
                                tool_calls=[tool_delta("call-1", "get_order", '{"order')],
                            )
                        )
                    ]
                ),
                SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(
                                content=None,
                                tool_calls=[tool_delta(None, None, '_id":"ORD-1"}')],
                            )
                        )
                    ]
                ),
            ]
        )
        client = OpenRouterChatClient(
            OpenRouterSettings(
                api_key="test-key",
                model="test/model",
                base_url="https://example.test/v1",
            ),
            sdk_client=sdk_client,
        )

        events = list(client.stream_complete([], []))

        self.assertEqual(
            events[-1]["message"]["tool_calls"],
            [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "get_order",
                        "arguments": '{"order_id":"ORD-1"}',
                    },
                }
            ],
        )

    def test_translates_sdk_errors_to_runtime_errors(self):
        sdk_client = Mock()
        sdk_client.chat.completions.create.side_effect = Exception("provider details")
        client = OpenRouterChatClient(
            OpenRouterSettings(
                api_key="test-key",
                model="test/model",
                base_url="https://example.test/v1",
            ),
            sdk_client=sdk_client,
        )

        with self.assertRaisesRegex(RuntimeError, "model request failed"):
            client.complete([], [])


if __name__ == "__main__":
    unittest.main()
