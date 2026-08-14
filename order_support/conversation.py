"""History-preserving order-support conversation loop."""

import json
import re
import time
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
invoice was generated when only a request ticket was created. If request_invoice returns
state not_eligible with reason order_cancelled, explain that a new invoice request cannot be
created because the order is cancelled.

Before each tool call, first write one short sentence in plain, customer-friendly words
saying what you are about to check and why (for example: "Let me find the order with your
backpack."). Never mention internal tool or function names in visible text.

End the final reply of every turn — the message that answers the customer, never a message
that only precedes tool calls — with a fenced code block matching this pattern exactly:

```json
{"card_order_ids": [], "follow_ups": []}
```

Set card_order_ids to the IDs of any orders (for example "ORD-1042") whose specific details
your reply discusses, so the app can show them as order cards; leave it empty when no single
order is the subject. Set follow_ups to 3 or 4 short questions, written in the customer's
voice, that this customer would plausibly ask next. The block is machine-read and removed
before your reply is shown, so the text before it must stand alone as a complete answer.
"""


TOOL_STATUS_MESSAGES = {
    "list_orders": "Fetching your orders…",
    "get_recent_product_candidates": "Looking for matching products…",
    "get_order_details": "Fetching order details…",
    "get_invoice": "Checking invoice status…",
    "request_invoice": "Requesting invoice generation…",
}

DEFAULT_FOLLOW_UPS = [
    "Where is my recent order?",
    "Can I get an invoice for my order?",
    "What did I order recently?",
]

MAX_CARDS = 3
MAX_FOLLOW_UPS = 4

_METADATA_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```\s*$", re.DOTALL)


def _split_answer_metadata(content):
    """Split a final reply into visible text and the trailing machine-read block."""
    match = _METADATA_BLOCK.search(content)
    if match is None:
        return content.strip(), None

    visible = content[: match.start()].strip()
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError:
        return visible, None
    return visible, metadata if isinstance(metadata, dict) else None


class _FenceSuppressor:
    """Filter streamed deltas so a trailing fenced block is never shown live."""

    _MARKER = "```"

    def __init__(self):
        self._pending = ""
        self._suppressed = False

    def feed(self, delta):
        if self._suppressed:
            return ""
        text = self._pending + delta
        index = text.find(self._MARKER)
        if index != -1:
            self._suppressed = True
            self._pending = ""
            return text[:index]

        for length in (2, 1):
            if text.endswith(self._MARKER[:length]):
                self._pending = text[-length:]
                return text[:-length]
        self._pending = ""
        return text

    def flush(self):
        if self._suppressed:
            return ""
        pending, self._pending = self._pending, ""
        return pending


def _parse_tool_arguments(tool_call):
    raw_arguments = tool_call.get("function", {}).get("arguments", "{}")
    try:
        arguments = json.loads(raw_arguments or "{}")
    except (TypeError, json.JSONDecodeError):
        return {"_raw": raw_arguments}
    return arguments if isinstance(arguments, dict) else {"_raw": raw_arguments}


def _select_follow_ups(metadata, cards):
    if metadata is not None and isinstance(metadata.get("follow_ups"), list):
        cleaned = [
            suggestion.strip()
            for suggestion in metadata["follow_ups"]
            if isinstance(suggestion, str) and suggestion.strip()
        ]
        if cleaned:
            return cleaned[:MAX_FOLLOW_UPS]

    suggestions = []
    for order in cards:
        order_id = order["order_id"]
        if order["status"] in {"processing", "shipped"}:
            suggestions.append(f"When will {order_id} arrive?")
        if order["invoice_status"] == "available":
            suggestions.append(f"Can I download the invoice for {order_id}?")
        elif order["invoice_status"] == "not_requested" and order["status"] != "cancelled":
            suggestions.append(f"Can I get an invoice for {order_id}?")
    return suggestions[:MAX_FOLLOW_UPS] if suggestions else list(DEFAULT_FOLLOW_UPS)


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
        fallback_card_ids = []
        while True:
            assistant_message = None
            suppressor = _FenceSuppressor()
            for model_event in self._stream_model_completion(messages):
                if model_event["type"] == "content_delta":
                    visible = suppressor.feed(model_event["delta"])
                    if visible:
                        yield {"type": "delta", "content": visible}
                elif model_event["type"] == "message":
                    assistant_message = model_event["message"]
            held_back = suppressor.flush()
            if held_back:
                yield {"type": "delta", "content": held_back}

            if assistant_message is None:
                raise RuntimeError("The model stream ended without a message")
            self._validate_assistant_message(assistant_message)
            messages.append(deepcopy(assistant_message))

            tool_calls = assistant_message.get("tool_calls", [])
            raw_content = assistant_message.get("content")
            if not tool_calls:
                if not isinstance(raw_content, str) or not raw_content.strip():
                    raise RuntimeError("The model returned neither tool calls nor an answer")
                answer, metadata = _split_answer_metadata(raw_content)
                if not answer:
                    raise RuntimeError("The model returned neither tool calls nor an answer")
                yield {"type": "segment", "kind": "answer"}
                cards = self._hydrate_cards(customer_id, metadata, fallback_card_ids)
                yield {"type": "cards", "orders": cards}
                yield {
                    "type": "follow_ups",
                    "suggestions": _select_follow_ups(metadata, cards),
                }
                yield {"type": "result", "answer": answer, "history": messages}
                return

            if isinstance(raw_content, str) and raw_content.strip():
                yield {"type": "segment", "kind": "reasoning"}

            if tool_rounds >= self._max_tool_rounds:
                raise RuntimeError("The model exceeded the maximum number of tool rounds")
            tool_rounds += 1

            for tool_call in tool_calls:
                tool_call_id = tool_call.get("id") or "invalid-tool-call"
                tool_name = tool_call.get("function", {}).get("name")
                yield {
                    "type": "tool_call",
                    "id": tool_call_id,
                    "name": tool_name,
                    "arguments": _parse_tool_arguments(tool_call),
                }
                yield {
                    "type": "status",
                    "message": TOOL_STATUS_MESSAGES.get(
                        tool_name,
                        "Checking your order information…",
                    ),
                }
                started_at = time.monotonic()
                tool_message = self._execute_tool_call(tools, tool_call)
                elapsed_ms = int((time.monotonic() - started_at) * 1000)
                messages.append(tool_message)

                try:
                    result_value = json.loads(tool_message["content"])
                except json.JSONDecodeError:
                    result_value = tool_message["content"]
                self._track_fallback_card(fallback_card_ids, tool_name, result_value)
                yield {
                    "type": "tool_result",
                    "id": tool_call_id,
                    "name": tool_name,
                    "result": result_value,
                    "elapsed_ms": elapsed_ms,
                }

    def _hydrate_cards(self, customer_id, metadata, fallback_card_ids):
        """Resolve requested card order IDs into full, database-backed order payloads."""
        order_ids = None
        if metadata is not None and isinstance(metadata.get("card_order_ids"), list):
            order_ids = [
                order_id
                for order_id in metadata["card_order_ids"]
                if isinstance(order_id, str) and order_id.strip()
            ]
        if order_ids is None:
            order_ids = fallback_card_ids

        seen = set()
        orders = []
        for order_id in order_ids:
            key = order_id.strip().casefold()
            if key in seen:
                continue
            seen.add(key)
            order = self._repository.get_order_details(customer_id, order_id)
            if order is not None:
                orders.append(order)
            if len(orders) >= MAX_CARDS:
                break
        return orders

    @staticmethod
    def _track_fallback_card(fallback_card_ids, tool_name, result_value):
        if tool_name != "get_order_details" or not isinstance(result_value, dict):
            return
        order = result_value.get("order")
        if result_value.get("found") and isinstance(order, dict):
            order_id = order.get("order_id")
            if isinstance(order_id, str) and order_id:
                fallback_card_ids.append(order_id)

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
