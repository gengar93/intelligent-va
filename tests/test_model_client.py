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
