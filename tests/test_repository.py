import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from order_support.repository import OrderRepository
from scripts.reset_database import build_database


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "orders.db"
        build_database(self.database_path)
        self.repository = OrderRepository(self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_lists_customers_alphabetically(self):
        customers = self.repository.list_customers()

        self.assertEqual(
            [customer["name"] for customer in customers],
            ["Aarav Sharma", "Kabir Khan", "Meera Iyer"],
        )

    def test_returns_complete_customer_orders(self):
        result = self.repository.get_customer_orders("CUS-002")

        self.assertEqual(result["customer"]["name"], "Meera Iyer")
        self.assertEqual(
            [order["order_id"] for order in result["orders"]],
            ["ORD-1087", "ORD-1095"],
        )

        latest_order = result["orders"][0]
        self.assertEqual(latest_order["total_minor"], 339800)
        self.assertEqual(
            [item["product_name"] for item in latest_order["items"]],
            ["UrbanTrail Backpack", "SteelSip Bottle"],
        )

    def test_returns_none_for_unknown_customer(self):
        self.assertIsNone(self.repository.get_customer_orders("CUS-999"))

    def test_database_connection_is_read_only(self):
        with self.repository._connect() as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM customers")

    def test_returns_customer_scoped_invoice_with_snapshot_items(self):
        invoice = self.repository.get_order_invoice("CUS-001", "ord-1042")
        another_customers_invoice = self.repository.get_order_invoice(
            "CUS-002", "ORD-1042"
        )

        self.assertEqual(invoice["invoice_number"], "INV-2026-00481")
        self.assertEqual(invoice["billing_name"], "Aarav Sharma")
        self.assertEqual(invoice["total_minor"], 749800)
        self.assertEqual(
            invoice["document_url"],
            "/mock-invoices/INV-2026-00481.pdf",
        )
        self.assertEqual(
            invoice["items"][0]["description"],
            "NoiseBeat H100 Headphones",
        )
        self.assertIsNone(another_customers_invoice)

    def test_returns_latest_customer_scoped_invoice_ticket(self):
        ticket = self.repository.get_latest_invoice_ticket("CUS-002", "ord-1087")
        another_customers_ticket = self.repository.get_latest_invoice_ticket(
            "CUS-001", "ORD-1087"
        )

        self.assertEqual(ticket["ticket_id"], "TKT-7002")
        self.assertEqual(ticket["status"], "in_progress")
        self.assertIsNone(another_customers_ticket)

    def test_returns_unified_invoice_states(self):
        available = self.repository.get_invoice_state("CUS-001", "ORD-1042")
        in_progress = self.repository.get_invoice_state("CUS-002", "ORD-1087")
        failed = self.repository.get_invoice_state("CUS-003", "ORD-1064")
        not_requested = self.repository.get_invoice_state("CUS-001", "ORD-1038")
        foreign = self.repository.get_invoice_state("CUS-001", "ORD-1087")

        self.assertEqual(available["state"], "available")
        self.assertEqual(
            available["invoice"]["document_url"],
            "/mock-invoices/INV-2026-00481.pdf",
        )
        self.assertEqual(in_progress["state"], "in_progress")
        self.assertEqual(in_progress["ticket"]["ticket_id"], "TKT-7002")
        self.assertEqual(failed["state"], "failed")
        self.assertEqual(not_requested["state"], "not_requested")
        self.assertEqual(
            foreign,
            {"order_found": False, "state": "order_not_found"},
        )

    def request_invoice(self, suffix, customer_id="CUS-001", order_id="ORD-1038"):
        return self.repository.request_invoice(
            customer_id,
            order_id,
            ticket_id=f"TKT-REQUEST-{suffix}",
            ticket_status_history_id=f"TSH-REQUEST-{suffix}",
            requested_at=f"2026-08-13T10:00:0{suffix}+00:00",
        )

    def test_invoice_request_is_idempotent(self):
        first = self.request_invoice("1")
        second = self.request_invoice("2")

        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["ticket"]["ticket_id"], "TKT-REQUEST-1")
        self.assertEqual(second["ticket"]["ticket_id"], "TKT-REQUEST-1")

        with sqlite3.connect(self.database_path) as connection:
            ticket_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM tickets
                WHERE order_id = 'ORD-1038'
                  AND ticket_type = 'invoice_generation'
                """
            ).fetchone()[0]
            history_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM ticket_status_history
                WHERE ticket_id = 'TKT-REQUEST-1'
                """
            ).fetchone()[0]

        self.assertEqual(ticket_count, 1)
        self.assertEqual(history_count, 1)

    def test_invoice_request_is_idempotent_under_concurrency(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(self.request_invoice, ("3", "4")))

        self.assertEqual(sum(result["created"] for result in results), 1)
        self.assertEqual(
            len({result["ticket"]["ticket_id"] for result in results}),
            1,
        )

    def test_invoice_request_returns_existing_invoice_without_writing(self):
        result = self.request_invoice("5", order_id="ORD-1042")

        self.assertFalse(result["created"])
        self.assertEqual(result["state"], "available")
        self.assertEqual(result["invoice"]["invoice_number"], "INV-2026-00481")

    def test_invoice_request_retries_after_failed_ticket(self):
        result = self.request_invoice(
            "6",
            customer_id="CUS-003",
            order_id="ORD-1064",
        )

        self.assertTrue(result["created"])
        self.assertEqual(result["state"], "queued")
        self.assertEqual(result["ticket"]["ticket_id"], "TKT-REQUEST-6")

    def test_invoice_request_does_not_write_for_another_customers_order(self):
        result = self.request_invoice("7", order_id="ORD-1087")

        self.assertEqual(
            result,
            {
                "order_found": False,
                "state": "order_not_found",
                "created": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
