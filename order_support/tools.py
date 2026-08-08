"""Tool definitions and safe dispatch for order lookups."""

from __future__ import annotations

from typing import Any

from order_support.repository import OrderRepository

ORDER_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_orders",
            "description": (
                "List every order belonging to the customer selected in the application, "
                "newest first. Use this for recent, latest, active, or general order questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": (
                "Get full items, attributes, total, shipment status, tracking, and delivery "
                "information for one order belonging to the selected customer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order identifier, for example ORD-1042.",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_orders_by_product",
            "description": (
                "Find the selected customer's orders containing a product described by name, "
                "category, color, size, or another stored product attribute."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_query": {
                        "type": "string",
                        "description": (
                            "A short product description, such as 'black headphones'."
                        ),
                    }
                },
                "required": ["product_query"],
                "additionalProperties": False,
            },
        },
    },
]


def execute_tool(
    repository: OrderRepository,
    customer_id: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Execute a named tool while always enforcing the UI-selected customer."""

    if tool_name == "list_orders":
        return {"ok": True, "orders": repository.list_orders(customer_id)}

    if tool_name == "get_order_details":
        order = repository.get_order(customer_id, arguments.get("order_id", ""))
        if order is None:
            return {
                "ok": False,
                "error": "No matching order belongs to the selected customer.",
            }
        return {"ok": True, "order": order}

    if tool_name == "find_orders_by_product":
        orders = repository.find_orders_by_product(
            customer_id, arguments.get("product_query", "")
        )
        return {"ok": True, "orders": orders}

    return {"ok": False, "error": f"Unknown tool: {tool_name}"}
