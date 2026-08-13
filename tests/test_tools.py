import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from order_support.repository import OrderRepository
from order_support.tools import TOOL_DEFINITIONS, OrderTools
from scripts.reset_database import build_database


class OrderToolsTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "orders.db"
        build_database(self.database_path)
        self.repository = OrderRepository(self.database_path)
        self.tools = OrderTools(
            self.repository,
            "CUS-001",
            today_provider=lambda: date(2026, 8, 8),
            now_provider=lambda: datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc),
            id_provider=lambda prefix: f"{prefix}-TOOL-1",
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_tool_definitions_do_not_expose_customer_id(self):
        parameter_names = {
            parameter_name
            for definition in TOOL_DEFINITIONS
            for parameter_name in definition["function"]["parameters"]["properties"]
        }

        self.assertNotIn("customer_id", parameter_names)

    def test_lists_only_selected_customers_orders(self):
        result = self.tools.list_orders()

        self.assertEqual(
            [order["order_id"] for order in result["orders"]],
            ["ORD-1042", "ORD-1038"],
        )
        self.assertNotIn("delivery_address", result["orders"][0])

    def test_gets_customer_scoped_order_details(self):
        own_order = self.tools.get_order_details("ord-1042")
        another_customers_order = self.tools.get_order_details("ORD-1087")

        self.assertTrue(own_order["found"])
        self.assertEqual(own_order["order"]["order_id"], "ORD-1042")
        self.assertEqual(
            own_order["order"]["items"][0]["name"],
            "NoiseBeat H100 Headphones",
        )
        self.assertEqual(another_customers_order, {"found": False, "order": None})

    def test_lookback_days_filters_using_python_calculated_cutoff(self):
        four_days = self.tools.get_recent_product_candidates(4)
        unlimited = self.tools.get_recent_product_candidates(None)

        self.assertEqual(
            [candidate["order_id"] for candidate in four_days["candidates"]],
            ["ORD-1042"],
        )
        self.assertEqual(
            [candidate["order_id"] for candidate in unlimited["candidates"]],
            ["ORD-1042", "ORD-1038"],
        )

    def test_returns_zero_candidates_when_window_has_no_orders(self):
        result = self.tools.get_recent_product_candidates(0)

        self.assertEqual(result, {"candidates": []})

    def test_rejects_invalid_lookback_values(self):
        for invalid_value in (-1, 366, 2.5, "30", True):
            with self.subTest(invalid_value=invalid_value):
                with self.assertRaises(ValueError):
                    self.tools.get_recent_product_candidates(invalid_value)

    def test_candidates_are_customer_scoped_and_lean(self):
        result = self.tools.get_recent_product_candidates(None)

        self.assertEqual(
            {candidate["name"] for candidate in result["candidates"]},
            {"NoiseBeat H100 Headphones", "BrewPro Coffee Maker"},
        )
        self.assertEqual(
            set(result["candidates"][0]),
            {"order_id", "name", "description", "ordered_at"},
        )

    def test_preserves_duplicate_products_across_orders(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                INSERT INTO orders (
                    order_id, customer_id, status, placed_at,
                    estimated_delivery_date, delivered_at, currency,
                    delivery_address, payment_method_display
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "ORD-DUPLICATE",
                    "CUS-001",
                    "processing",
                    "2026-08-08T09:00:00+05:30",
                    "2026-08-12",
                    None,
                    "INR",
                    "22 Lakeview Apartments, Koramangala, Bengaluru 560034",
                    "Visa ending in 1842",
                ),
            )
            connection.execute(
                """
                INSERT INTO order_items (
                    order_item_id, order_id, product_id, quantity, unit_price_minor
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "ITEM-DUPLICATE",
                    "ORD-DUPLICATE",
                    "PROD-HEADPHONES",
                    1,
                    729800,
                ),
            )

        result = self.tools.get_recent_product_candidates(None)
        headphone_candidates = [
            candidate
            for candidate in result["candidates"]
            if candidate["name"] == "NoiseBeat H100 Headphones"
        ]

        self.assertEqual(len(headphone_candidates), 2)
        self.assertEqual(
            {candidate["order_id"] for candidate in headphone_candidates},
            {"ORD-1042", "ORD-DUPLICATE"},
        )

    def test_candidates_use_ten_orders_and_thirty_candidate_limits(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            for order_number in range(11):
                order_id = f"ORD-LIMIT-{order_number:02d}"
                connection.execute(
                    """
                    INSERT INTO orders (
                        order_id, customer_id, status, placed_at,
                        estimated_delivery_date, delivered_at, currency,
                        delivery_address, payment_method_display
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        "CUS-001",
                        "processing",
                        f"2026-08-08T{order_number + 1:02d}:00:00+05:30",
                        "2026-08-12",
                        None,
                        "INR",
                        "22 Lakeview Apartments, Koramangala, Bengaluru 560034",
                        "Visa ending in 1842",
                    ),
                )
                for item_number, product_id in enumerate(
                    ("PROD-HEADPHONES", "PROD-COFFEE", "PROD-BACKPACK"),
                    start=1,
                ):
                    connection.execute(
                        """
                        INSERT INTO order_items (
                            order_item_id, order_id, product_id,
                            quantity, unit_price_minor
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            f"ITEM-LIMIT-{order_number:02d}-{item_number}",
                            order_id,
                            product_id,
                            1,
                            10000,
                        ),
                    )

        result = self.tools.get_recent_product_candidates(0)
        candidate_order_ids = {
            candidate["order_id"] for candidate in result["candidates"]
        }

        self.assertEqual(len(result["candidates"]), 30)
        self.assertFalse(
            any(
                order_id == "ORD-LIMIT-00"
                for order_id in candidate_order_ids
            )
        )

    def test_execute_validates_arguments_and_unknown_tools(self):
        result = self.tools.execute(
            "get_recent_product_candidates",
            {"lookback_days": 4},
        )

        self.assertEqual(result["candidates"][0]["order_id"], "ORD-1042")
        with self.assertRaises(ValueError):
            self.tools.execute("list_orders", {"customer_id": "CUS-002"})
        with self.assertRaises(ValueError):
            self.tools.execute("unknown_tool", {})

    def test_get_invoice_returns_available_and_current_ticket_states(self):
        available = self.tools.get_invoice("ORD-1042")
        not_requested = self.tools.get_invoice("ORD-1038")

        self.assertEqual(available["state"], "available")
        self.assertEqual(
            available["invoice"]["document_url"],
            "/mock-invoices/INV-2026-00481.pdf",
        )
        self.assertEqual(not_requested["state"], "not_requested")

    def test_request_invoice_creates_one_ticket_and_returns_it_on_repeat(self):
        tools = OrderTools(
            self.repository,
            "CUS-002",
            now_provider=lambda: datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc),
            id_provider=lambda prefix: f"{prefix}-TOOL-1",
        )
        first = tools.request_invoice("ORD-1095")
        second = tools.request_invoice("ORD-1095")

        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["ticket"], second["ticket"])
        self.assertEqual(first["ticket"]["ticket_id"], "TKT-TOOL-1")

    def test_request_invoice_rejects_cancelled_order_without_active_ticket(self):
        result = self.tools.request_invoice("ORD-1038")

        self.assertFalse(result["created"])
        self.assertEqual(result["state"], "not_eligible")
        self.assertEqual(result["reason"], "order_cancelled")

    def test_invoice_tools_are_customer_scoped(self):
        invoice = self.tools.get_invoice("ORD-1087")
        request = self.tools.request_invoice("ORD-1087")

        self.assertFalse(invoice["order_found"])
        self.assertFalse(request["order_found"])
        self.assertFalse(request["created"])


if __name__ == "__main__":
    unittest.main()
