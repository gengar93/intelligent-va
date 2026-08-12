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

    def get_order_details(self, customer_id, order_id):
        customer_orders = self.get_customer_orders(customer_id)
        if customer_orders is None:
            return None

        return next(
            (
                order
                for order in customer_orders["orders"]
                if order["order_id"].casefold() == order_id.strip().casefold()
            ),
            None,
        )

    def get_order_invoice(self, customer_id, order_id):
        with self._connect() as connection:
            invoice_row = connection.execute(
                """
                SELECT
                    i.invoice_id,
                    i.invoice_number,
                    i.order_id,
                    i.generation_ticket_id,
                    i.issued_at,
                    i.billing_name,
                    i.billing_address,
                    i.currency,
                    i.subtotal_minor,
                    i.tax_minor,
                    i.total_minor,
                    i.document_url
                FROM invoices AS i
                JOIN orders AS o ON o.order_id = i.order_id
                WHERE o.customer_id = ? AND lower(i.order_id) = lower(?)
                """,
                (customer_id, order_id.strip()),
            ).fetchone()

            if invoice_row is None:
                return None

            item_rows = connection.execute(
                """
                SELECT
                    invoice_item_id,
                    source_order_item_id,
                    description,
                    quantity,
                    unit_price_minor,
                    tax_minor,
                    line_total_minor
                FROM invoice_items
                WHERE invoice_id = ?
                ORDER BY invoice_item_id
                """,
                (invoice_row["invoice_id"],),
            ).fetchall()

        invoice = dict(invoice_row)
        invoice["items"] = [dict(row) for row in item_rows]
        return invoice

    def get_latest_invoice_ticket(self, customer_id, order_id):
        with self._connect() as connection:
            ticket_row = connection.execute(
                """
                SELECT
                    t.ticket_id,
                    t.ticket_type,
                    t.order_id,
                    t.status,
                    t.created_at,
                    t.updated_at,
                    t.completed_at,
                    t.failure_reason
                FROM tickets AS t
                JOIN orders AS o ON o.order_id = t.order_id
                WHERE o.customer_id = ?
                  AND lower(t.order_id) = lower(?)
                  AND t.ticket_type = 'invoice_generation'
                ORDER BY t.created_at DESC
                LIMIT 1
                """,
                (customer_id, order_id.strip()),
            ).fetchone()

        return None if ticket_row is None else dict(ticket_row)

    def get_recent_product_candidates(self, customer_id, cutoff_date):
        cutoff_value = cutoff_date.isoformat() if cutoff_date is not None else None

        with self._connect() as connection:
            rows = connection.execute(
                """
                WITH eligible_orders AS (
                    SELECT order_id, placed_at
                    FROM orders
                    WHERE customer_id = ?
                      AND (
                          ? IS NULL
                          OR substr(placed_at, 1, 10) >= ?
                      )
                    ORDER BY placed_at DESC
                    LIMIT 10
                )
                SELECT
                    eligible_orders.order_id,
                    p.name,
                    p.description,
                    eligible_orders.placed_at AS ordered_at
                FROM eligible_orders
                JOIN order_items AS oi ON oi.order_id = eligible_orders.order_id
                JOIN products AS p ON p.product_id = oi.product_id
                ORDER BY eligible_orders.placed_at DESC, oi.order_item_id
                LIMIT 30
                """,
                (customer_id, cutoff_value, cutoff_value),
            ).fetchall()

        return [dict(row) for row in rows]
