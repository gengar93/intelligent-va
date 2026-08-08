"""Read-only queries for customer and order data."""

import sqlite3
from pathlib import Path


class OrderRepository:
    def __init__(self, database_path: Path):
        self._database_path = Path(database_path).resolve()

    def _connect(self):
        if not self._database_path.is_file():
            raise FileNotFoundError(f"Database does not exist: {self._database_path}")

        connection = sqlite3.connect(
            f"file:{self._database_path}?mode=ro",
            uri=True,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def list_customers(self):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT customer_id, name, email
                FROM customers
                ORDER BY name
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def get_customer_orders(self, customer_id):
        with self._connect() as connection:
            customer_row = connection.execute(
                """
                SELECT customer_id, name, email
                FROM customers
                WHERE customer_id = ?
                """,
                (customer_id,),
            ).fetchone()

            if customer_row is None:
                return None

            order_rows = connection.execute(
                """
                SELECT
                    o.order_id,
                    o.status,
                    o.placed_at,
                    o.estimated_delivery_date,
                    o.delivered_at,
                    o.currency,
                    o.delivery_address,
                    o.payment_method_display,
                    COALESCE(SUM(oi.quantity * oi.unit_price_minor), 0) AS total_minor
                FROM orders AS o
                LEFT JOIN order_items AS oi ON oi.order_id = o.order_id
                WHERE o.customer_id = ?
                GROUP BY o.order_id
                ORDER BY o.placed_at DESC
                """,
                (customer_id,),
            ).fetchall()

            item_rows = connection.execute(
                """
                SELECT
                    oi.order_id,
                    oi.order_item_id,
                    p.product_id,
                    p.sku,
                    p.name AS product_name,
                    p.description,
                    oi.quantity,
                    oi.unit_price_minor,
                    oi.quantity * oi.unit_price_minor AS line_total_minor
                FROM order_items AS oi
                JOIN orders AS o ON o.order_id = oi.order_id
                JOIN products AS p ON p.product_id = oi.product_id
                WHERE o.customer_id = ?
                ORDER BY oi.order_id, oi.order_item_id
                """,
                (customer_id,),
            ).fetchall()

        items_by_order = {row["order_id"]: [] for row in order_rows}
        for item_row in item_rows:
            item = dict(item_row)
            order_id = item.pop("order_id")
            items_by_order[order_id].append(item)

        orders = []
        for order_row in order_rows:
            order = dict(order_row)
            order["items"] = items_by_order[order["order_id"]]
            orders.append(order)

        return {"customer": dict(customer_row), "orders": orders}
