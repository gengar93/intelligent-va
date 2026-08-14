from copy import deepcopy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from order_support.api import create_app
from scripts.reset_database import build_database


class FakeModelClient:
    def __init__(self):
        self.responses = []
        self.requests = []

    def complete(self, messages, tools):
        self.requests.append({"messages": deepcopy(messages), "tools": deepcopy(tools)})
        if not self.responses:
            raise RuntimeError("No fake response configured")
        return deepcopy(self.responses.pop(0))


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "orders.db"
        build_database(self.database_path)
        self.model_client = FakeModelClient()
        self.client = TestClient(create_app(self.database_path, self.model_client))

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
        self.assertEqual(body["orders"][0]["invoice_status"], "available")
        self.assertEqual(body["orders"][1]["invoice_status"], "not_requested")

    def test_lists_open_invoice_tickets_for_customer(self):
        response = self.client.get("/api/customers/CUS-002/tickets")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["ticket_id"], "TKT-7002")
        self.assertEqual(response.json()[0]["item_count"], 2)

    def test_downloads_invoice_pdf_for_customer_owned_order(self):
        response = self.client.get("/api/customers/CUS-001/orders/ORD-1042/invoice.pdf")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertEqual(
            response.headers["content-disposition"],
            'attachment; filename="INV-2026-00481.pdf"',
        )
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertGreater(len(response.content), 1000)

    def test_invoice_pdf_absent_or_foreign_returns_404(self):
        no_invoice = self.client.get("/api/customers/CUS-001/orders/ORD-1038/invoice.pdf")
        foreign = self.client.get("/api/customers/CUS-002/orders/ORD-1042/invoice.pdf")
        unknown_order = self.client.get("/api/customers/CUS-001/orders/ORD-9999/invoice.pdf")

        self.assertEqual(no_invoice.status_code, 404)
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(unknown_order.status_code, 404)

    def test_generated_invoice_becomes_downloadable(self):
        before = self.client.get("/api/customers/CUS-002/orders/ORD-1087/invoice.pdf")
        self.client.post("/api/customers/CUS-002/tickets/TKT-7002/generate-invoice")
        after = self.client.get("/api/customers/CUS-002/orders/ORD-1087/invoice.pdf")

        self.assertEqual(before.status_code, 404)
        self.assertEqual(after.status_code, 200)
        self.assertTrue(after.content.startswith(b"%PDF-"))

    def test_lists_closed_invoice_tickets_with_outcome_details(self):
        completed = self.client.get("/api/customers/CUS-001/tickets/closed")
        failed = self.client.get("/api/customers/CUS-003/tickets/closed")
        none_closed = self.client.get("/api/customers/CUS-002/tickets/closed")
        unknown = self.client.get("/api/customers/CUS-999/tickets/closed")

        self.assertEqual(completed.status_code, 200)
        completed_ticket = completed.json()[0]
        self.assertEqual(completed_ticket["ticket_id"], "TKT-7001")
        self.assertEqual(completed_ticket["status"], "completed")
        self.assertEqual(completed_ticket["invoice_number"], "INV-2026-00481")
        self.assertEqual(
            completed_ticket["document_url"],
            "/api/customers/CUS-001/orders/ORD-1042/invoice.pdf",
        )
        self.assertEqual(completed_ticket["total_minor"], 749800)

        failed_ticket = failed.json()[0]
        self.assertEqual(failed_ticket["ticket_id"], "TKT-7003")
        self.assertEqual(failed_ticket["status"], "failed")
        self.assertEqual(
            failed_ticket["failure_reason"],
            "Billing address could not be validated",
        )
        self.assertIsNone(failed_ticket["invoice_number"])

        self.assertEqual(none_closed.json(), [])
        self.assertEqual(unknown.status_code, 404)

    def test_generated_invoice_ticket_moves_to_closed_list(self):
        self.client.post("/api/customers/CUS-002/tickets/TKT-7002/generate-invoice")

        closed = self.client.get("/api/customers/CUS-002/tickets/closed")

        self.assertEqual(
            [ticket["ticket_id"] for ticket in closed.json()],
            ["TKT-7002"],
        )
        self.assertEqual(closed.json()[0]["status"], "completed")
        self.assertIsNotNone(closed.json()[0]["invoice_number"])

    def test_generates_invoice_and_refresh_endpoints_reflect_completion(self):
        response = self.client.post(
            "/api/customers/CUS-002/tickets/TKT-7002/generate-invoice"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["created"])
        self.assertEqual(response.json()["state"], "available")
        self.assertEqual(response.json()["invoice"]["order_id"], "ORD-1087")

        tickets = self.client.get("/api/customers/CUS-002/tickets")
        orders = self.client.get("/api/customers/CUS-002/orders")
        generated_order = next(
            order for order in orders.json()["orders"] if order["order_id"] == "ORD-1087"
        )
        self.assertEqual(tickets.json(), [])
        self.assertEqual(generated_order["invoice_status"], "available")

    def test_rejects_foreign_and_closed_invoice_tickets(self):
        foreign = self.client.post(
            "/api/customers/CUS-001/tickets/TKT-7002/generate-invoice"
        )
        closed = self.client.post(
            "/api/customers/CUS-003/tickets/TKT-7003/generate-invoice"
        )

        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(closed.status_code, 409)

    def test_customer_response_does_not_include_other_customers_orders(self):
        response = self.client.get("/api/customers/CUS-001/orders")

        order_ids = {order["order_id"] for order in response.json()["orders"]}
        self.assertNotIn("ORD-1087", order_ids)
        self.assertNotIn("ORD-1064", order_ids)

    def test_returns_not_found_for_unknown_customer(self):
        response = self.client.get("/api/customers/CUS-999/orders")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Customer not found"})

    def test_starts_and_continues_a_customer_conversation(self):
        self.model_client.responses = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-orders",
                        "type": "function",
                        "function": {
                            "name": "list_orders",
                            "arguments": json.dumps({}),
                        },
                    }
                ],
            },
            {"role": "assistant", "content": "Your order is shipped."},
            {"role": "assistant", "content": "It should arrive on 11 August."},
        ]

        first_response = self.client.post(
            "/api/chat",
            json={"customer_id": "CUS-001", "message": "Where is my order?"},
        )
        conversation_id = first_response.json()["conversation_id"]
        second_response = self.client.post(
            "/api/chat",
            json={
                "customer_id": "CUS-001",
                "message": "When will it arrive?",
                "conversation_id": conversation_id,
            },
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(
            first_response.json(),
            {
                "conversation_id": conversation_id,
                "answer": "Your order is shipped.",
            },
        )
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.json()["conversation_id"], conversation_id)
        second_request_messages = self.model_client.requests[2]["messages"]
        self.assertEqual(
            [message["role"] for message in second_request_messages],
            ["system", "user", "assistant", "tool", "assistant", "user"],
        )
        self.assertEqual(second_request_messages[3]["tool_call_id"], "call-orders")

    def test_does_not_return_internal_history_to_the_browser(self):
        self.model_client.responses = [
            {"role": "assistant", "content": "You have two orders."}
        ]

        response = self.client.post(
            "/api/chat",
            json={"customer_id": "CUS-001", "message": "List my orders"},
        )

        self.assertEqual(set(response.json()), {"conversation_id", "answer"})

    def test_streams_real_activity_and_a_lean_result(self):
        self.model_client.responses = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-orders",
                        "type": "function",
                        "function": {
                            "name": "list_orders",
                            "arguments": json.dumps({}),
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": (
                    "Your newest order is shipped.\n\n"
                    "```json\n"
                    '{"card_order_ids": ["ORD-1042"],'
                    ' "follow_ups": ["When will it arrive?"]}\n'
                    "```"
                ),
            },
        ]

        response = self.client.post(
            "/api/chat/stream",
            json={"customer_id": "CUS-001", "message": "Where is my latest order?"},
        )
        events = [json.loads(line) for line in response.text.splitlines()]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("application/x-ndjson"))
        self.assertEqual(
            [event["type"] for event in events],
            [
                "status",
                "tool_call",
                "status",
                "tool_result",
                "delta",
                "segment",
                "cards",
                "follow_ups",
                "result",
            ],
        )
        self.assertEqual(
            [event["message"] for event in events if event["type"] == "status"],
            [
                "Understanding your question…",
                "Fetching your orders…",
            ],
        )

        tool_call = next(event for event in events if event["type"] == "tool_call")
        self.assertEqual(tool_call["id"], "call-orders")
        self.assertEqual(tool_call["name"], "list_orders")
        self.assertEqual(tool_call["arguments"], {})

        tool_result = next(event for event in events if event["type"] == "tool_result")
        self.assertEqual(tool_result["id"], "call-orders")
        self.assertEqual(tool_result["name"], "list_orders")
        self.assertEqual(len(tool_result["result"]["orders"]), 2)
        self.assertGreaterEqual(tool_result["elapsed_ms"], 0)

        streamed_text = "".join(
            event["content"] for event in events if event["type"] == "delta"
        )
        self.assertEqual(streamed_text.strip(), "Your newest order is shipped.")
        self.assertNotIn("```", streamed_text)

        segment = next(event for event in events if event["type"] == "segment")
        self.assertEqual(segment["kind"], "answer")

        cards = next(event for event in events if event["type"] == "cards")
        self.assertEqual([order["order_id"] for order in cards["orders"]], ["ORD-1042"])
        self.assertEqual(
            cards["orders"][0]["items"][0]["image_url"],
            "/products/headphones.svg",
        )

        follow_ups = next(event for event in events if event["type"] == "follow_ups")
        self.assertEqual(follow_ups["suggestions"], ["When will it arrive?"])

        self.assertEqual(
            set(events[-1]),
            {"type", "conversation_id", "answer"},
        )
        self.assertEqual(events[-1]["answer"], "Your newest order is shipped.")

    def test_rejects_using_a_conversation_for_another_customer(self):
        self.model_client.responses = [
            {"role": "assistant", "content": "First response"}
        ]
        first_response = self.client.post(
            "/api/chat",
            json={"customer_id": "CUS-001", "message": "Hello"},
        )

        response = self.client.post(
            "/api/chat",
            json={
                "customer_id": "CUS-002",
                "message": "Continue",
                "conversation_id": first_response.json()["conversation_id"],
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {"detail": "Conversation belongs to a different customer"},
        )
        self.assertEqual(len(self.model_client.requests), 1)

    def test_returns_not_found_for_unknown_conversation(self):
        response = self.client.post(
            "/api/chat",
            json={
                "customer_id": "CUS-001",
                "message": "Continue",
                "conversation_id": "missing",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Conversation not found"})

    def test_rejects_blank_chat_input_before_calling_model(self):
        response = self.client.post(
            "/api/chat",
            json={"customer_id": "CUS-001", "message": "   "},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.model_client.requests, [])

    def test_returns_generic_error_when_assistant_fails(self):
        response = self.client.post(
            "/api/chat",
            json={"customer_id": "CUS-001", "message": "Where is my order?"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {"detail": "The assistant could not complete the request"},
        )

    def test_returns_generic_error_when_assistant_is_not_configured(self):
        unconfigured_client = TestClient(create_app(self.database_path))

        with patch(
            "order_support.api.OpenRouterSettings.from_env",
            side_effect=ValueError("sensitive configuration detail"),
        ):
            response = unconfigured_client.post(
                "/api/chat",
                json={"customer_id": "CUS-001", "message": "Where is my order?"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "The assistant is not configured"})


if __name__ == "__main__":
    unittest.main()
