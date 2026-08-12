import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.reset_database import build_database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "orders.db"
        build_database(self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def test_seed_data_loads_and_has_valid_foreign_keys(self):
        with self.connect() as connection:
            customer_count = connection.execute(
                "SELECT COUNT(*) FROM customers"
            ).fetchone()[0]
            order_count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            ticket_count = connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            invoice_count = connection.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()

        self.assertEqual(customer_count, 3)
        self.assertEqual(order_count, 5)
        self.assertEqual(ticket_count, 3)
        self.assertEqual(invoice_count, 1)
        self.assertEqual(violations, [])

    def test_seed_data_covers_invoice_ticket_lifecycle_cases(self):
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT t.status, i.invoice_number, i.document_url
                FROM tickets AS t
                LEFT JOIN invoices AS i ON i.generation_ticket_id = t.ticket_id
                ORDER BY t.ticket_id
                """
            ).fetchall()

        self.assertEqual(
            [(row["status"], row["invoice_number"]) for row in rows],
            [
                ("completed", "INV-2026-00481"),
                ("in_progress", None),
                ("failed", None),
            ],
        )
        self.assertEqual(
            rows[0]["document_url"],
            "/mock-invoices/INV-2026-00481.pdf",
        )

    def test_prevents_two_active_invoice_tickets_for_one_order(self):
        with self.connect() as connection, self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO tickets (
                    ticket_id, ticket_type, order_id, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "TKT-DUPLICATE",
                    "invoice_generation",
                    "ORD-1087",
                    "queued",
                    "2026-08-11T11:16:00+05:30",
                    "2026-08-11T11:16:00+05:30",
                ),
            )

    def test_rejects_invoice_total_that_does_not_balance(self):
        with self.connect() as connection, self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO invoices (
                    invoice_id, invoice_number, order_id, generation_ticket_id,
                    issued_at, billing_name, billing_address, currency,
                    subtotal_minor, tax_minor, total_minor, document_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "INV-INVALID",
                    "INV-2026-INVALID",
                    "ORD-1064",
                    "TKT-7003",
                    "2026-08-11T12:22:00+05:30",
                    "Kabir Khan",
                    "51 Crescent Residency, Bandra West, Mumbai 400050",
                    "INR",
                    10000,
                    1800,
                    10000,
                    "/mock-invoices/INV-2026-INVALID.pdf",
                ),
            )

    def test_invoice_requires_completed_generation_ticket_for_same_order(self):
        with self.connect() as connection, self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO invoices (
                    invoice_id, invoice_number, order_id, generation_ticket_id,
                    issued_at, billing_name, billing_address, currency,
                    subtotal_minor, tax_minor, total_minor, document_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "INV-PREMATURE",
                    "INV-2026-PREMATURE",
                    "ORD-1087",
                    "TKT-7002",
                    "2026-08-11T11:16:00+05:30",
                    "Meera Iyer",
                    "8 Palm Grove, Adyar, Chennai 600020",
                    "INR",
                    339800,
                    0,
                    339800,
                    "/mock-invoices/INV-2026-PREMATURE.pdf",
                ),
            )

    def test_reads_order_details_and_items(self):
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    o.status,
                    o.estimated_delivery_date,
                    o.delivery_address,
                    o.payment_method_display,
                    p.name AS product_name,
                    oi.quantity,
                    oi.unit_price_minor
                FROM orders AS o
                JOIN order_items AS oi ON oi.order_id = o.order_id
                JOIN products AS p ON p.product_id = oi.product_id
                WHERE o.customer_id = ? AND o.order_id = ?
                """,
                ("CUS-001", "ORD-1042"),
            ).fetchall()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "shipped")
        self.assertEqual(rows[0]["estimated_delivery_date"], "2026-08-11")
        self.assertEqual(
            rows[0]["delivery_address"],
            "22 Lakeview Apartments, Koramangala, Bengaluru 560034",
        )
        self.assertEqual(rows[0]["payment_method_display"], "Visa ending in 1842")
        self.assertEqual(rows[0]["product_name"], "NoiseBeat H100 Headphones")
        self.assertEqual(rows[0]["quantity"], 1)
        self.assertEqual(rows[0]["unit_price_minor"], 749800)

    def test_customer_scope_does_not_return_another_customers_order(self):
        with self.connect() as connection:
            order = connection.execute(
                """
                SELECT order_id
                FROM orders
                WHERE customer_id = ? AND order_id = ?
                """,
                ("CUS-001", "ORD-1087"),
            ).fetchone()

        self.assertIsNone(order)

    def test_calculates_order_total_from_items(self):
        with self.connect() as connection:
            total_minor = connection.execute(
                """
                SELECT SUM(quantity * unit_price_minor)
                FROM order_items
                WHERE order_id = ?
                """,
                ("ORD-1087",),
            ).fetchone()[0]

        self.assertEqual(total_minor, 339800)

    def test_rejects_zero_quantity(self):
        with self.connect() as connection, self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO order_items (
                    order_item_id, order_id, product_id, quantity, unit_price_minor
                ) VALUES (?, ?, ?, ?, ?)
                """,
                ("INVALID-QUANTITY", "ORD-1042", "PROD-HEADPHONES", 0, 749800),
            )

    def test_rejects_negative_price(self):
        with self.connect() as connection, self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO order_items (
                    order_item_id, order_id, product_id, quantity, unit_price_minor
                ) VALUES (?, ?, ?, ?, ?)
                """,
                ("INVALID-PRICE", "ORD-1042", "PROD-HEADPHONES", 1, -1),
            )


if __name__ == "__main__":
    unittest.main()
