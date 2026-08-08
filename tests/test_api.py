import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from order_support.api import create_app
from scripts.reset_database import build_database


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "orders.db"
        build_database(self.database_path)
        self.client = TestClient(create_app(self.database_path))

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_lists_customers(self):
        response = self.client.get("/api/customers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        self.assertEqual(response.json()[0]["customer_id"], "CUS-001")

    def test_returns_customer_orders_and_items(self):
        response = self.client.get("/api/customers/CUS-001/orders")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["customer"]["name"], "Aarav Sharma")
        self.assertEqual(
            [order["order_id"] for order in body["orders"]],
            ["ORD-1042", "ORD-1038"],
        )
        self.assertEqual(
            body["orders"][0]["items"][0]["product_name"],
            "NoiseBeat H100 Headphones",
        )

    def test_customer_response_does_not_include_other_customers_orders(self):
        response = self.client.get("/api/customers/CUS-001/orders")

        order_ids = {order["order_id"] for order in response.json()["orders"]}
        self.assertNotIn("ORD-1087", order_ids)
        self.assertNotIn("ORD-1064", order_ids)

    def test_returns_not_found_for_unknown_customer(self):
        response = self.client.get("/api/customers/CUS-999/orders")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Customer not found"})


if __name__ == "__main__":
    unittest.main()
