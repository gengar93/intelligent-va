import sqlite3
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
