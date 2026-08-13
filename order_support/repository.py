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
                    COALESCE(SUM(oi.quantity * oi.unit_price_minor), 0) AS total_minor,
                    CASE
                        WHEN EXISTS (
                            SELECT 1 FROM invoices AS i WHERE i.order_id = o.order_id
                        ) THEN 'available'
                        ELSE COALESCE(
                            (
                                SELECT t.status
                                FROM tickets AS t
                                WHERE t.order_id = o.order_id
                                  AND t.ticket_type = 'invoice_generation'
                                ORDER BY t.created_at DESC, t.ticket_id DESC
                                LIMIT 1
                            ),
                            'not_requested'
                        )
                    END AS invoice_status
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

    def get_open_invoice_tickets(self, customer_id):
        with self._connect() as connection:
            customer_exists = connection.execute(
                "SELECT 1 FROM customers WHERE customer_id = ?",
                (customer_id,),
            ).fetchone()
            if customer_exists is None:
                return None

            rows = connection.execute(
                """
                SELECT
                    t.ticket_id,
                    t.order_id,
                    t.status,
                    t.created_at,
                    t.updated_at,
                    o.status AS order_status,
                    o.currency,
                    COALESCE(SUM(oi.quantity), 0) AS item_count,
                    COALESCE(SUM(oi.quantity * oi.unit_price_minor), 0) AS total_minor
                FROM tickets AS t
                JOIN orders AS o ON o.order_id = t.order_id
                LEFT JOIN order_items AS oi ON oi.order_id = o.order_id
                WHERE o.customer_id = ?
                  AND t.ticket_type = 'invoice_generation'
                  AND t.status IN ('queued', 'in_progress')
                GROUP BY t.ticket_id
                ORDER BY t.created_at ASC, t.ticket_id ASC
                """,
                (customer_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def generate_invoice_for_ticket(
        self,
        customer_id,
        ticket_id,
        *,
        invoice_id,
        invoice_number,
        in_progress_history_id,
        completed_history_id,
        generated_at,
        invoice_item_id_provider,
    ):
        """Atomically snapshot an order into an invoice and complete its open ticket."""
        with self._connect_writable() as connection:
            connection.execute("BEGIN IMMEDIATE")
            ticket_row = connection.execute(
                """
                SELECT
                    t.ticket_id,
                    t.order_id,
                    t.status,
                    o.currency,
                    o.delivery_address,
                    c.name AS billing_name
                FROM tickets AS t
                JOIN orders AS o ON o.order_id = t.order_id
                JOIN customers AS c ON c.customer_id = o.customer_id
                WHERE c.customer_id = ?
                  AND lower(t.ticket_id) = lower(?)
                  AND t.ticket_type = 'invoice_generation'
                """,
                (customer_id, ticket_id.strip()),
            ).fetchone()
            if ticket_row is None:
                return {"state": "ticket_not_found"}

            existing_invoice = connection.execute(
                """
                SELECT invoice_id, invoice_number, order_id, issued_at, document_url
                FROM invoices
                WHERE generation_ticket_id = ?
                """,
                (ticket_row["ticket_id"],),
            ).fetchone()
            if existing_invoice is not None:
                return {
                    "state": "available",
                    "created": False,
                    "invoice": dict(existing_invoice),
                }

            if ticket_row["status"] not in {"queued", "in_progress"}:
                return {
                    "state": "ticket_not_open",
                    "ticket_status": ticket_row["status"],
                }

            item_rows = connection.execute(
                """
                SELECT
                    oi.order_item_id,
                    p.name AS description,
                    oi.quantity,
                    oi.unit_price_minor
                FROM order_items AS oi
                JOIN products AS p ON p.product_id = oi.product_id
                WHERE oi.order_id = ?
                ORDER BY oi.order_item_id
                """,
                (ticket_row["order_id"],),
            ).fetchall()
            subtotal_minor = sum(
                row["quantity"] * row["unit_price_minor"] for row in item_rows
            )

            previous_status = ticket_row["status"]
            if previous_status == "queued":
                connection.execute(
                    """
                    UPDATE tickets
                    SET status = 'in_progress', updated_at = ?
                    WHERE ticket_id = ?
                    """,
                    (generated_at, ticket_row["ticket_id"]),
                )
                connection.execute(
                    """
                    INSERT INTO ticket_status_history (
                        ticket_status_history_id, ticket_id, from_status,
                        to_status, changed_at, note
                    ) VALUES (?, ?, 'queued', 'in_progress', ?, 'Generator claimed ticket')
                    """,
                    (in_progress_history_id, ticket_row["ticket_id"], generated_at),
                )
                previous_status = "in_progress"

            connection.execute(
                """
                UPDATE tickets
                SET status = 'completed', updated_at = ?, completed_at = ?
                WHERE ticket_id = ?
                """,
                (generated_at, generated_at, ticket_row["ticket_id"]),
            )
            connection.execute(
                """
                INSERT INTO ticket_status_history (
                    ticket_status_history_id, ticket_id, from_status,
                    to_status, changed_at, note
                ) VALUES (?, ?, ?, 'completed', ?, ?)
                """,
                (
                    completed_history_id,
                    ticket_row["ticket_id"],
                    previous_status,
                    generated_at,
                    f"Invoice {invoice_number} issued",
                ),
            )

            document_url = f"/mock-invoices/{invoice_number}.pdf"
            connection.execute(
                """
                INSERT INTO invoices (
                    invoice_id, invoice_number, order_id, generation_ticket_id,
                    issued_at, billing_name, billing_address, currency,
                    subtotal_minor, tax_minor, total_minor, document_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    invoice_id,
                    invoice_number,
                    ticket_row["order_id"],
                    ticket_row["ticket_id"],
                    generated_at,
                    ticket_row["billing_name"],
                    ticket_row["delivery_address"],
                    ticket_row["currency"],
                    subtotal_minor,
                    subtotal_minor,
                    document_url,
                ),
            )
            connection.executemany(
                """
                INSERT INTO invoice_items (
                    invoice_item_id, invoice_id, source_order_item_id,
                    description, quantity, unit_price_minor, tax_minor,
                    line_total_minor
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                """,
                [
                    (
                        invoice_item_id_provider(),
                        invoice_id,
                        row["order_item_id"],
                        row["description"],
                        row["quantity"],
                        row["unit_price_minor"],
                        row["quantity"] * row["unit_price_minor"],
                    )
                    for row in item_rows
                ],
            )

            return {
                "state": "available",
                "created": True,
                "invoice": {
                    "invoice_id": invoice_id,
                    "invoice_number": invoice_number,
                    "order_id": ticket_row["order_id"],
                    "issued_at": generated_at,
                    "document_url": document_url,
                },
            }

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
                SELECT order_id, status
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
                SELECT order_id, status
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

            if order_row["status"] == "cancelled":
                return {
                    "order_found": True,
                    "order_id": canonical_order_id,
                    "state": "not_eligible",
                    "reason": "order_cancelled",
                    "invoice": None,
                    "ticket": current_state["ticket"],
                    "created": False,
                }

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
