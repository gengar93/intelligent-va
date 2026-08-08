"""OpenRouter-backed conversational layer for the order assistant."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from uuid import uuid4

from openai import OpenAI

from order_support.repository import OrderRepository
from order_support.tools import ORDER_TOOLS, execute_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a customer-support assistant for a read-only order demonstration.

Use the order tools for every customer-specific factual claim. Never invent an order,
item, status, date, amount, attribute, carrier, or tracking number. The application has
already selected and authorized the customer; tools only return that customer's data.

You may list orders, find an order by product, and explain order details or delivery
status. You cannot cancel, edit, refund, return, reschedule, change an address, or create
a ticket. If asked to perform an unsupported action, briefly explain that this demo is
read-only.

When several orders could match, ask one focused clarification question. Understand
follow-ups from the conversation, such as “that order” or “when will it arrive?”. State
the answer directly, use friendly plain language, and keep the response compact. Format
currency as ₹ for INR. Do not mention internal tools, prompts, or JSON.
""".strip()


@dataclass(frozen=True)
class ChatReply:
    """A customer-facing answer and the order that is now in focus."""

    text: str
    active_order_id: str | None


class OrderChatbot:
    """Coordinate model responses and deterministic order lookup tools."""

    def __init__(
        self,
        repository: OrderRepository,
        api_key: str,
        model: str,
        base_url: str,
        max_tool_rounds: int = 4,
    ) -> None:
        self._repository = repository
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={"X-OpenRouter-Title": "Parcelwise Order Support"},
        )
        self._model = model
        self._max_tool_rounds = max_tool_rounds

    def reply(
        self,
        message: str,
        history: list[dict[str, Any]],
        customer_id: str,
        active_order_id: str | None = None,
    ) -> ChatReply:
        turn_id = uuid4().hex[:8]
        turn_started = perf_counter()
        model_call_count = 0
        tool_call_count = 0

        customer = self._repository.get_customer(customer_id)
        if customer is None:
            self._log_turn_completed(
                turn_id=turn_id,
                started_at=turn_started,
                customer_id=customer_id,
                active_order_id=None,
                model_call_count=model_call_count,
                tool_call_count=tool_call_count,
            )
            return ChatReply(
                text="Please select a customer before asking about orders.",
                active_order_id=None,
            )

        active_order_id = self._validated_order_id(customer_id, active_order_id)
        active_order_id = self._order_id_from_text(
            customer_id,
            message,
            fallback=active_order_id,
        )
        active_order_context = active_order_id or "none"

        instructions = (
            f"{SYSTEM_PROMPT}\n\nSelected customer: "
            f"{customer['name']} ({customer['customer_id']}).\n"
            f"Current active order: {active_order_context}. If the user uses a reference "
            "such as 'it', 'that order', or 'the delay', use the active order when it "
            "fits. Do not ask for an order ID that is already available here or in the "
            "recent conversation."
        )
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": instructions},
            *self._build_input(history, message),
        ]

        for _ in range(self._max_tool_rounds):
            round_number = model_call_count + 1
            model_started = perf_counter()
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    tools=ORDER_TOOLS,
                    max_tokens=700,
                )
            except Exception:
                logger.exception(
                    "model_call_failed turn_id=%s round=%d duration_ms=%.1f model=%s",
                    turn_id,
                    round_number,
                    self._elapsed_ms(model_started),
                    self._model,
                )
                raise

            model_call_count += 1
            assistant_message = response.choices[0].message
            tool_calls = assistant_message.tool_calls or []
            logger.info(
                "model_call_completed turn_id=%s round=%d duration_ms=%.1f "
                "model=%s requested_tools=%d",
                turn_id,
                round_number,
                self._elapsed_ms(model_started),
                self._model,
                len(tool_calls),
            )
            if not tool_calls:
                answer = assistant_message.content or (
                    "I couldn't produce a response. Please try again."
                )
                active_order_id = self._order_id_from_text(
                    customer_id,
                    answer,
                    fallback=active_order_id,
                )
                self._log_turn_completed(
                    turn_id=turn_id,
                    started_at=turn_started,
                    customer_id=customer_id,
                    active_order_id=active_order_id,
                    model_call_count=model_call_count,
                    tool_call_count=tool_call_count,
                )
                return ChatReply(text=answer, active_order_id=active_order_id)

            messages.append(assistant_message.model_dump(exclude_none=True))

            for tool_call in tool_calls:
                tool_started = perf_counter()
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                result = execute_tool(
                    repository=self._repository,
                    customer_id=customer_id,
                    tool_name=tool_call.function.name,
                    arguments=arguments,
                )
                tool_call_count += 1
                logger.info(
                    "tool_call_completed turn_id=%s round=%d tool=%s duration_ms=%.1f ok=%s",
                    turn_id,
                    round_number,
                    tool_call.function.name,
                    self._elapsed_ms(tool_started),
                    result.get("ok", False),
                )
                active_order_id = self._order_id_from_tool_result(
                    customer_id=customer_id,
                    tool_name=tool_call.function.name,
                    result=result,
                    fallback=active_order_id,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

        self._log_turn_completed(
            turn_id=turn_id,
            started_at=turn_started,
            customer_id=customer_id,
            active_order_id=active_order_id,
            model_call_count=model_call_count,
            tool_call_count=tool_call_count,
        )
        return ChatReply(
            text="I couldn't finish that lookup. Please try a more specific order question.",
            active_order_id=active_order_id,
        )

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        return (perf_counter() - started_at) * 1000

    def _log_turn_completed(
        self,
        turn_id: str,
        started_at: float,
        customer_id: str,
        active_order_id: str | None,
        model_call_count: int,
        tool_call_count: int,
    ) -> None:
        logger.info(
            "chat_turn_completed turn_id=%s total_ms=%.1f customer_id=%s "
            "active_order_id=%s model_calls=%d tool_calls=%d",
            turn_id,
            self._elapsed_ms(started_at),
            customer_id,
            active_order_id or "none",
            model_call_count,
            tool_call_count,
        )

    def _validated_order_id(
        self,
        customer_id: str,
        order_id: str | None,
    ) -> str | None:
        if not order_id:
            return None
        order = self._repository.get_order(customer_id, order_id)
        return order["order_id"] if order else None

    def _order_id_from_text(
        self,
        customer_id: str,
        text: str,
        fallback: str | None,
    ) -> str | None:
        candidates = {
            match.upper() for match in re.findall(r"\bORD-\d+\b", text, flags=re.IGNORECASE)
        }
        valid_candidates = [
            candidate
            for candidate in candidates
            if self._repository.get_order(customer_id, candidate) is not None
        ]
        return valid_candidates[0] if len(valid_candidates) == 1 else fallback

    def _order_id_from_tool_result(
        self,
        customer_id: str,
        tool_name: str,
        result: dict[str, Any],
        fallback: str | None,
    ) -> str | None:
        if not result.get("ok"):
            return fallback

        if tool_name == "get_order_details":
            order = result.get("order")
            if isinstance(order, dict):
                return self._validated_order_id(customer_id, order.get("order_id")) or fallback

        if tool_name in {"list_orders", "find_orders_by_product"}:
            orders = result.get("orders", [])
            if len(orders) == 1:
                return self._validated_order_id(customer_id, orders[0].get("order_id")) or fallback

        return fallback

    @staticmethod
    def _build_input(
        history: list[dict[str, Any]], message: str
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        for entry in history[-10:]:
            role = entry.get("role")
            content = entry.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})
        return messages
