"""Customer-scoped order reads and narrowly scoped invoice-request writes."""

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

    def _connect_writable(self):
        if not self._database_path.is_file():
            raise FileNotFoundError(f"Database does not exist: {self._database_path}")

        connection = sqlite3.connect(self._database_path, timeout=5)
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

    def get_invoice_state(self, customer_id, order_id):
        normalized_order_id = order_id.strip()
        with self._connect() as connection:
            order_row = connection.execute(
                """
                SELECT order_id
                FROM orders
                WHERE customer_id = ? AND lower(order_id) = lower(?)
                """,
                (customer_id, normalized_order_id),
            ).fetchone()

            if order_row is None:
                return {"order_found": False, "state": "order_not_found"}

            return self._get_invoice_state_for_order(
                connection,
                order_row["order_id"],
            )

    def request_invoice(
        self,
        customer_id,
        order_id,
        *,
        ticket_id,
        ticket_status_history_id,
        requested_at,
    ):
        """Create at most one active invoice request for a customer-owned order."""
        normalized_order_id = order_id.strip()
        with self._connect_writable() as connection:
            connection.execute("BEGIN IMMEDIATE")
            order_row = connection.execute(
                """
                SELECT order_id
                FROM orders
                WHERE customer_id = ? AND lower(order_id) = lower(?)
                """,
                (customer_id, normalized_order_id),
            ).fetchone()

            if order_row is None:
                return {
                    "order_found": False,
                    "state": "order_not_found",
                    "created": False,
                }

            canonical_order_id = order_row["order_id"]
            current_state = self._get_invoice_state_for_order(
                connection,
                canonical_order_id,
            )
            if current_state["state"] in {"available", "queued", "in_progress"}:
                current_state["created"] = False
                return current_state

            connection.execute(
                """
                INSERT INTO tickets (
                    ticket_id,
                    ticket_type,
                    order_id,
                    status,
                    created_at,
                    updated_at,
                    completed_at,
                    failure_reason
                ) VALUES (?, 'invoice_generation', ?, 'queued', ?, ?, NULL, NULL)
                """,
                (ticket_id, canonical_order_id, requested_at, requested_at),
            )
            connection.execute(
                """
                INSERT INTO ticket_status_history (
                    ticket_status_history_id,
                    ticket_id,
                    from_status,
                    to_status,
                    changed_at,
                    note
                ) VALUES (?, ?, NULL, 'queued', ?, 'Customer requested invoice')
                """,
                (ticket_status_history_id, ticket_id, requested_at),
            )

            return {
                "order_found": True,
                "order_id": canonical_order_id,
                "state": "queued",
                "invoice": None,
                "ticket": {
                    "ticket_id": ticket_id,
                    "status": "queued",
                    "created_at": requested_at,
                    "updated_at": requested_at,
                    "completed_at": None,
                    "failure_reason": None,
                },
                "created": True,
            }

    @staticmethod
    def _get_invoice_state_for_order(connection, order_id):
        invoice_row = connection.execute(
            """
            SELECT
                invoice_id,
                invoice_number,
                order_id,
                issued_at,
                currency,
                subtotal_minor,
                tax_minor,
                total_minor,
                document_url
            FROM invoices
            WHERE order_id = ?
            """,
            (order_id,),
        ).fetchone()
        if invoice_row is not None:
            return {
                "order_found": True,
                "order_id": order_id,
                "state": "available",
                "invoice": dict(invoice_row),
                "ticket": None,
            }

        ticket_row = connection.execute(
            """
            SELECT
                ticket_id,
                status,
                created_at,
                updated_at,
                completed_at,
                failure_reason
            FROM tickets
            WHERE order_id = ? AND ticket_type = 'invoice_generation'
            ORDER BY created_at DESC, ticket_id DESC
            LIMIT 1
            """,
            (order_id,),
        ).fetchone()
        if ticket_row is None:
            return {
                "order_found": True,
                "order_id": order_id,
                "state": "not_requested",
                "invoice": None,
                "ticket": None,
            }

        return {
            "order_found": True,
            "order_id": order_id,
            "state": ticket_row["status"],
            "invoice": None,
            "ticket": dict(ticket_row),
        }

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
