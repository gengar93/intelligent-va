"""History-preserving read-only conversation loop."""

import json
from copy import deepcopy

from order_support.model_client import ChatModelClient
from order_support.repository import OrderRepository
from order_support.tools import TOOL_DEFINITIONS, OrderTools


SYSTEM_PROMPT = """You are a concise, read-only order support assistant.

The application has already selected the customer. The available tools are restricted to
that customer, so never ask for or invent a customer ID.

Use tools for every customer-specific fact. Do not rely on general knowledge for order data.
For a product reference such as "headphones", call get_recent_product_candidates, compare
the user's wording with candidate names and descriptions, and then call get_order_details
with the matching order_id. If multiple candidates are plausible, ask a focused clarifying
question. If none match, say so plainly.

Use the complete conversation history, including earlier tool results, to understand
follow-up references. Do not expose internal tool mechanics. Never claim to change an order,
payment, delivery, or customer record.
"""


class ConversationLoop:
    def __init__(
        self,
        model_client: ChatModelClient,
        repository: OrderRepository,
        *,
        max_tool_rounds=5,
        today_provider=None,
    ):
        if max_tool_rounds < 1:
            raise ValueError("max_tool_rounds must be at least 1")
        self._model_client = model_client
        self._repository = repository
        self._max_tool_rounds = max_tool_rounds
        self._today_provider = today_provider

    def run_turn(self, customer_id, user_message, history=None):
        customer_id = customer_id.strip()
        user_message = user_message.strip()
        if not customer_id:
            raise ValueError("customer_id is required")
        if not user_message:
            raise ValueError("user_message is required")

        messages = self._prepare_history(history)
        messages.append({"role": "user", "content": user_message})

        tool_kwargs = {}
        if self._today_provider is not None:
            tool_kwargs["today_provider"] = self._today_provider
        tools = OrderTools(self._repository, customer_id, **tool_kwargs)

        tool_rounds = 0
        while True:
            assistant_message = self._model_client.complete(
                deepcopy(messages),
                deepcopy(TOOL_DEFINITIONS),
            )
            self._validate_assistant_message(assistant_message)
            messages.append(deepcopy(assistant_message))

            tool_calls = assistant_message.get("tool_calls", [])
            if not tool_calls:
                answer = assistant_message.get("content")
                if not isinstance(answer, str) or not answer.strip():
                    raise RuntimeError("The model returned neither tool calls nor an answer")
                return {"answer": answer, "history": messages}

            if tool_rounds >= self._max_tool_rounds:
                raise RuntimeError("The model exceeded the maximum number of tool rounds")
            tool_rounds += 1

            for tool_call in tool_calls:
                messages.append(self._execute_tool_call(tools, tool_call))

    @staticmethod
    def _prepare_history(history):
        if history is None:
            return [{"role": "system", "content": SYSTEM_PROMPT}]

        messages = deepcopy(history)
        if not messages or messages[0].get("role") != "system":
            raise ValueError("history must begin with a system message")

        allowed_roles = {"system", "user", "assistant", "tool"}
        if any(message.get("role") not in allowed_roles for message in messages):
            raise ValueError("history contains an unsupported message role")
        return messages

    @staticmethod
    def _validate_assistant_message(message):
        if not isinstance(message, dict) or message.get("role") != "assistant":
            raise RuntimeError("The model client must return an assistant message")
        if "tool_calls" in message and not isinstance(message["tool_calls"], list):
            raise RuntimeError("assistant tool_calls must be a list")

    @staticmethod
    def _execute_tool_call(tools, tool_call):
        tool_call_id = tool_call.get("id")
        function = tool_call.get("function", {})
        tool_name = function.get("name")

        try:
            if not tool_call_id or not tool_name:
                raise ValueError("Tool call must include an ID and function name")
            arguments = json.loads(function.get("arguments", "{}"))
            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must be a JSON object")
            result = tools.execute(tool_name, arguments)
            content = json.dumps(result, ensure_ascii=False)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            content = json.dumps({"error": str(error)}, ensure_ascii=False)

        return {
            "role": "tool",
            "tool_call_id": tool_call_id or "invalid-tool-call",
            "content": content,
        }
