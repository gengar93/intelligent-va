"""Read-only access to the mock customer and order data."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class OrderRepository:
    """Load and query a small JSON-backed order catalogue."""

    def __init__(self, data_path: Path) -> None:
        self._data_path = data_path
        self._data = self._load_data()

    def _load_data(self) -> dict[str, Any]:
        with self._data_path.open(encoding="utf-8") as data_file:
            data = json.load(data_file)

        if "customers" not in data or "orders" not in data:
            raise ValueError("Order data must contain 'customers' and 'orders' lists.")
        return data

    def list_customers(self) -> list[dict[str, Any]]:
        return deepcopy(self._data["customers"])

    def get_customer(self, customer_id: str) -> dict[str, Any] | None:
        customer = next(
            (
                customer
                for customer in self._data["customers"]
                if customer["customer_id"] == customer_id
            ),
            None,
        )
        return deepcopy(customer)

    def list_orders(self, customer_id: str) -> list[dict[str, Any]]:
        orders = [
            self._order_summary(order)
            for order in self._data["orders"]
            if order["customer_id"] == customer_id
        ]
        return sorted(orders, key=lambda order: order["placed_at"], reverse=True)

    def get_order(self, customer_id: str, order_id: str) -> dict[str, Any] | None:
        normalized_order_id = order_id.strip().casefold()
        order = next(
            (
                order
                for order in self._data["orders"]
                if order["customer_id"] == customer_id
                and order["order_id"].casefold() == normalized_order_id
            ),
            None,
        )
        return deepcopy(order)

    def find_orders_by_product(
        self, customer_id: str, product_query: str
    ) -> list[dict[str, Any]]:
        terms = product_query.strip().casefold().split()
        if not terms:
            return []

        matching_orders = []
        for order in self._data["orders"]:
            if order["customer_id"] != customer_id:
                continue

            matching_items = []
            for item in order["items"]:
                searchable_text = " ".join(
                    [
                        item["product_name"],
                        item.get("category", ""),
                        *[str(value) for value in item.get("attributes", {}).values()],
                    ]
                ).casefold()
                if all(term in searchable_text for term in terms):
                    matching_items.append(deepcopy(item))

            if matching_items:
                summary = self._order_summary(order)
                summary["matching_items"] = matching_items
                matching_orders.append(summary)

        return sorted(matching_orders, key=lambda order: order["placed_at"], reverse=True)

    @staticmethod
    def _order_summary(order: dict[str, Any]) -> dict[str, Any]:
        return {
            "order_id": order["order_id"],
            "placed_at": order["placed_at"],
            "status": order["status"],
            "estimated_delivery": order.get("estimated_delivery"),
            "delivered_at": order.get("delivered_at"),
            "total": order["total"],
            "currency": order["currency"],
            "items": [
                {
                    "product_name": item["product_name"],
                    "quantity": item["quantity"],
                }
                for item in order["items"]
            ],
        }
