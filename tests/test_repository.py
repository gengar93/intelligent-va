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
            [
                "Aarav Sharma",
                "Emily Carter",
                "Ethan Brooks",
                "Marcus Johnson",
                "Sofia Rodriguez",
            ],
        )

    def test_returns_complete_customer_orders(self):
        result = self.repository.get_customer_orders("CUS-002")

        self.assertEqual(result["customer"]["name"], "Emily Carter")
        self.assertEqual(
            [order["order_id"] for order in result["orders"]],
            ["ORD-1087", "ORD-1114", "ORD-1095", "ORD-1124"],
        )

        latest_order = result["orders"][0]
        self.assertEqual(latest_order["total_minor"], 20998)
        self.assertEqual(latest_order["invoice_status"], "in_progress")
        self.assertEqual(result["orders"][1]["invoice_status"], "queued")
        self.assertEqual(result["orders"][2]["invoice_status"], "available")
        self.assertEqual(result["orders"][3]["invoice_status"], "not_requested")
        self.assertEqual(
            [item["product_name"] for item in latest_order["items"]],
            ["NovaDock 12-in-1 USB-C Dock", "NovaHub 7-port USB-C Hub"],
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
        self.assertEqual(invoice["total_minor"], 12999)
        self.assertEqual(
            invoice["document_url"],
            "/api/customers/CUS-001/orders/ORD-1042/invoice.pdf",
        )
        self.assertEqual(
            invoice["items"][0]["description"],
            "Nova H100 Wireless Headset",
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

    def test_lists_only_customer_scoped_open_invoice_tickets(self):
        tickets = self.repository.get_open_invoice_tickets("CUS-002")

        self.assertEqual(
            [ticket["ticket_id"] for ticket in tickets],
            ["TKT-7002", "TKT-7005"],
        )
        self.assertEqual(tickets[0]["order_id"], "ORD-1087")
        self.assertEqual(tickets[0]["item_count"], 2)
        self.assertEqual(tickets[0]["total_minor"], 20998)
        self.assertEqual(self.repository.get_open_invoice_tickets("CUS-001"), [])
        self.assertIsNone(self.repository.get_open_invoice_tickets("CUS-999"))

    def test_returns_unified_invoice_states(self):
        available = self.repository.get_invoice_state("CUS-001", "ORD-1042")
        in_progress = self.repository.get_invoice_state("CUS-002", "ORD-1087")
        failed = self.repository.get_invoice_state("CUS-003", "ORD-1064")
        not_requested = self.repository.get_invoice_state("CUS-001", "ORD-1038")
        foreign = self.repository.get_invoice_state("CUS-001", "ORD-1087")

        self.assertEqual(available["state"], "available")
        self.assertEqual(
            available["invoice"]["document_url"],
            "/api/customers/CUS-001/orders/ORD-1042/invoice.pdf",
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

    def generate_invoice(self, customer_id, ticket_id, suffix="TEST"):
        item_ids = iter([f"INI-{suffix}-1", f"INI-{suffix}-2"])
        return self.repository.generate_invoice_for_ticket(
            customer_id,
            ticket_id,
            invoice_id=f"INV-{suffix}",
            invoice_number=f"INV-2026-{suffix}",
            in_progress_history_id=f"TSH-{suffix}-PROGRESS",
            completed_history_id=f"TSH-{suffix}-COMPLETE",
            generated_at="2026-08-18T15:30:00-05:00",
            invoice_item_id_provider=lambda: next(item_ids),
        )

    def test_generates_invoice_snapshot_and_completes_in_progress_ticket(self):
        result = self.generate_invoice("CUS-002", "TKT-7002")

        self.assertEqual(result["state"], "available")
        self.assertTrue(result["created"])
        self.assertEqual(result["invoice"]["order_id"], "ORD-1087")
        self.assertEqual(
            result["invoice"]["document_url"],
            "/api/customers/CUS-002/orders/ORD-1087/invoice.pdf",
        )
        self.assertEqual(
            [ticket["ticket_id"] for ticket in self.repository.get_open_invoice_tickets("CUS-002")],
            ["TKT-7005"],
        )

        invoice = self.repository.get_order_invoice("CUS-002", "ORD-1087")
        self.assertEqual(invoice["billing_name"], "Emily Carter")
        self.assertEqual(invoice["billing_address"], "2634 N Orchard St, Chicago, IL 60614")
        self.assertEqual(invoice["subtotal_minor"], 20998)
        self.assertEqual(invoice["tax_minor"], 0)
        self.assertEqual(invoice["total_minor"], 20998)
        self.assertEqual(len(invoice["items"]), 2)

        with sqlite3.connect(self.database_path) as connection:
            ticket = connection.execute(
                "SELECT status, completed_at FROM tickets WHERE ticket_id = 'TKT-7002'"
            ).fetchone()
            latest_history = connection.execute(
                """
                SELECT from_status, to_status, note
                FROM ticket_status_history
                WHERE ticket_id = 'TKT-7002'
                ORDER BY changed_at DESC, ticket_status_history_id DESC
                LIMIT 1
                """
            ).fetchone()

        self.assertEqual(ticket, ("completed", "2026-08-18T15:30:00-05:00"))
        self.assertEqual(latest_history[0:2], ("in_progress", "completed"))
        self.assertIn("INV-2026-TEST", latest_history[2])

    def test_generating_queued_ticket_records_both_transitions(self):
        request = self.request_invoice(
            "Q",
            customer_id="CUS-001",
            order_id="ORD-1121",
        )

        result = self.generate_invoice("CUS-001", request["ticket"]["ticket_id"], "QUEUED")

        self.assertTrue(result["created"])
        with sqlite3.connect(self.database_path) as connection:
            transitions = connection.execute(
                """
                SELECT from_status, to_status
                FROM ticket_status_history
                WHERE ticket_id = 'TKT-REQUEST-Q'
                ORDER BY rowid
                """
            ).fetchall()
        self.assertEqual(
            transitions,
            [(None, "queued"), ("queued", "in_progress"), ("in_progress", "completed")],
        )

    def test_invoice_generation_is_customer_scoped_and_requires_open_ticket(self):
        foreign = self.generate_invoice("CUS-001", "TKT-7002", "FOREIGN")
        closed = self.generate_invoice("CUS-003", "TKT-7003", "CLOSED")

        self.assertEqual(foreign, {"state": "ticket_not_found"})
        self.assertEqual(
            closed,
            {"state": "ticket_not_open", "ticket_status": "failed"},
        )

    def test_invoice_request_is_idempotent(self):
        first = self.request_invoice("1", order_id="ORD-1121", customer_id="CUS-001")
        second = self.request_invoice("2", order_id="ORD-1121", customer_id="CUS-001")

        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["ticket"]["ticket_id"], "TKT-REQUEST-1")
        self.assertEqual(second["ticket"]["ticket_id"], "TKT-REQUEST-1")

        with sqlite3.connect(self.database_path) as connection:
            ticket_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM tickets
                WHERE order_id = 'ORD-1121'
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
            futures = [
                executor.submit(
                    self.request_invoice,
                    suffix,
                    "CUS-001",
                    "ORD-1121",
                )
                for suffix in ("3", "4")
            ]
            results = [future.result() for future in futures]

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

    def test_invoice_request_rejects_cancelled_order_without_active_ticket(self):
        result = self.request_invoice("8")

        self.assertEqual(
            result,
            {
                "order_found": True,
                "order_id": "ORD-1038",
                "state": "not_eligible",
                "reason": "order_cancelled",
                "invoice": None,
                "ticket": None,
                "created": False,
            },
        )

        with sqlite3.connect(self.database_path) as connection:
            ticket_count = connection.execute(
                "SELECT COUNT(*) FROM tickets WHERE order_id = 'ORD-1038'"
            ).fetchone()[0]

        self.assertEqual(ticket_count, 0)

    def test_cancelled_order_returns_existing_active_ticket(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                INSERT INTO tickets (
                    ticket_id, ticket_type, order_id, status,
                    created_at, updated_at, completed_at, failure_reason
                ) VALUES (?, 'invoice_generation', ?, 'in_progress', ?, ?, NULL, NULL)
                """,
                (
                    "TKT-CANCELLED-ACTIVE",
                    "ORD-1038",
                    "2026-08-12T09:00:00+00:00",
                    "2026-08-12T09:01:00+00:00",
                ),
            )

        result = self.request_invoice("9")

        self.assertFalse(result["created"])
        self.assertEqual(result["state"], "in_progress")
        self.assertEqual(result["ticket"]["ticket_id"], "TKT-CANCELLED-ACTIVE")

    def test_cancelled_order_with_failed_ticket_does_not_create_retry(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                INSERT INTO tickets (
                    ticket_id, ticket_type, order_id, status,
                    created_at, updated_at, completed_at, failure_reason
                ) VALUES (?, 'invoice_generation', ?, 'failed', ?, ?, NULL, ?)
                """,
                (
                    "TKT-CANCELLED-FAILED",
                    "ORD-1038",
                    "2026-08-12T09:00:00+00:00",
                    "2026-08-12T09:01:00+00:00",
                    "Earlier generation failed",
                ),
            )

        result = self.request_invoice("A")

        self.assertFalse(result["created"])
        self.assertEqual(result["state"], "not_eligible")
        self.assertEqual(result["reason"], "order_cancelled")
        self.assertEqual(result["ticket"]["ticket_id"], "TKT-CANCELLED-FAILED")

        with sqlite3.connect(self.database_path) as connection:
            ticket_count = connection.execute(
                "SELECT COUNT(*) FROM tickets WHERE order_id = 'ORD-1038'"
            ).fetchone()[0]

        self.assertEqual(ticket_count, 1)

    def test_cancelled_order_returns_existing_invoice(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                INSERT INTO tickets (
                    ticket_id, ticket_type, order_id, status,
                    created_at, updated_at, completed_at, failure_reason
                ) VALUES (?, 'invoice_generation', ?, 'completed', ?, ?, ?, NULL)
                """,
                (
                    "TKT-CANCELLED-COMPLETE",
                    "ORD-1038",
                    "2026-08-01T09:00:00+00:00",
                    "2026-08-01T09:02:00+00:00",
                    "2026-08-01T09:02:00+00:00",
                ),
            )
            connection.execute(
                """
                INSERT INTO invoices (
                    invoice_id, invoice_number, order_id, generation_ticket_id,
                    issued_at, billing_name, billing_address, currency,
                    subtotal_minor, tax_minor, total_minor, document_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "INV-CANCELLED",
                    "INV-2026-CANCELLED",
                    "ORD-1038",
                    "TKT-CANCELLED-COMPLETE",
                    "2026-08-01T09:02:00+00:00",
                    "Aarav Sharma",
                    "418 W 22nd St, New York, NY 10011",
                    "USD",
                    32999,
                    0,
                    32999,
                    "/mock-invoices/INV-2026-CANCELLED.pdf",
                ),
            )

        result = self.request_invoice("0")

        self.assertFalse(result["created"])
        self.assertEqual(result["state"], "available")
        self.assertEqual(result["invoice"]["invoice_number"], "INV-2026-CANCELLED")


if __name__ == "__main__":
    unittest.main()
