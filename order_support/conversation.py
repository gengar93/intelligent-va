"""History-preserving order-support conversation loop."""

import json
from copy import deepcopy

from order_support.model_client import ChatModelClient
from order_support.repository import OrderRepository
from order_support.tools import TOOL_DEFINITIONS, OrderTools


SYSTEM_PROMPT = """You are a concise order support assistant.

The application has already selected the customer. The available tools are restricted to
that customer, so never ask for or invent a customer ID.

Use tools for every customer-specific fact. Do not rely on general knowledge for order data.
For a product reference such as "headphones", call get_recent_product_candidates, compare
the user's wording with candidate names and descriptions, and then call get_order_details
with the matching order_id. If multiple candidates are plausible, ask a focused clarifying
question. If none match, say so plainly.

Use the complete conversation history, including earlier tool results, to understand
follow-up references. Do not expose internal tool mechanics. Never claim to change an order,
payment, delivery, or customer record. Invoice generation requests are the only supported
write action.

For every question about invoice availability or invoice-request status, call get_invoice
to fetch fresh data, even if an earlier conversation turn contains an invoice or ticket
result. Never report invoice status from conversation history alone. If the invoice is
available, provide its document_url. If the state is queued or in_progress, report the
current status and do not call request_invoice. If the state is not_requested and the
customer is asking to obtain the invoice, call request_invoice. If the latest request failed
or was cancelled, explain that result; call request_invoice only when the customer is asking
to obtain or retry the invoice, never for a status-only question. Do not claim that an
invoice was generated when only a request ticket was created.
"""


TOOL_STATUS_MESSAGES = {
    "list_orders": "Fetching your orders…",
    "get_recent_product_candidates": "Looking for matching products…",
    "get_order_details": "Fetching order details…",
    "get_invoice": "Checking invoice status…",
    "request_invoice": "Requesting invoice generation…",
}


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
        result = None
        for event in self.stream_turn(customer_id, user_message, history):
            if event["type"] == "result":
                result = event
        if result is None:
            raise RuntimeError("The conversation ended without a result")
        return {"answer": result["answer"], "history": result["history"]}

    def stream_turn(self, customer_id, user_message, history=None):
        customer_id = customer_id.strip()
        user_message = user_message.strip()
        if not customer_id:
            raise ValueError("customer_id is required")
        if not user_message:
            raise ValueError("user_message is required")

        messages = self._prepare_history(history)
        messages.append({"role": "user", "content": user_message})
        yield {"type": "status", "message": "Understanding your question…"}

        tool_kwargs = {}
        if self._today_provider is not None:
            tool_kwargs["today_provider"] = self._today_provider
        tools = OrderTools(self._repository, customer_id, **tool_kwargs)

        tool_rounds = 0
        while True:
            assistant_message = None
            for model_event in self._stream_model_completion(messages):
                if model_event["type"] == "content_delta":
                    yield {"type": "delta", "content": model_event["delta"]}
                elif model_event["type"] == "message":
                    assistant_message = model_event["message"]

            if assistant_message is None:
                raise RuntimeError("The model stream ended without a message")
            self._validate_assistant_message(assistant_message)
            messages.append(deepcopy(assistant_message))

            tool_calls = assistant_message.get("tool_calls", [])
            if not tool_calls:
                answer = assistant_message.get("content")
                if not isinstance(answer, str) or not answer.strip():
                    raise RuntimeError("The model returned neither tool calls nor an answer")
                yield {"type": "result", "answer": answer, "history": messages}
                return

            if tool_rounds >= self._max_tool_rounds:
                raise RuntimeError("The model exceeded the maximum number of tool rounds")
            tool_rounds += 1

            for tool_call in tool_calls:
                tool_name = tool_call.get("function", {}).get("name")
                yield {
                    "type": "status",
                    "message": TOOL_STATUS_MESSAGES.get(
                        tool_name,
                        "Checking your order information…",
                    ),
                }
                messages.append(self._execute_tool_call(tools, tool_call))

    def _stream_model_completion(self, messages):
        request_messages = deepcopy(messages)
        request_tools = deepcopy(TOOL_DEFINITIONS)
        stream_complete = getattr(self._model_client, "stream_complete", None)
        if stream_complete is not None:
            yield from stream_complete(request_messages, request_tools)
            return

        message = self._model_client.complete(request_messages, request_tools)
        content = message.get("content")
        if isinstance(content, str) and content:
            yield {"type": "content_delta", "delta": content}
        yield {"type": "message", "message": message}

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
