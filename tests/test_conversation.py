import json
import tempfile
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path

from order_support.conversation import ConversationLoop
from order_support.repository import OrderRepository
from scripts.reset_database import build_database


def tool_call_message(call_id, name, arguments):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments),
                },
            }
        ],
    }


class FakeModelClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def complete(self, messages, tools):
        self.requests.append({"messages": deepcopy(messages), "tools": deepcopy(tools)})
        if not self.responses:
            raise AssertionError("Fake model has no response remaining")
        return deepcopy(self.responses.pop(0))


class ConversationLoopTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "orders.db"
        build_database(self.database_path)
        self.repository = OrderRepository(self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def make_loop(self, responses, max_tool_rounds=5):
        client = FakeModelClient(responses)
        loop = ConversationLoop(
            client,
            self.repository,
            max_tool_rounds=max_tool_rounds,
            today_provider=lambda: date(2026, 8, 8),
        )
        return loop, client

    def test_preserves_system_user_assistant_and_tool_messages(self):
        loop, client = self.make_loop(
            [
                tool_call_message(
                    "call-candidates",
                    "get_recent_product_candidates",
                    {"lookback_days": 7},
                ),
                tool_call_message(
                    "call-details",
                    "get_order_details",
                    {"order_id": "ORD-1042"},
                ),
                {
                    "role": "assistant",
                    "content": "The headphones cost ₹7,498.",
                },
            ]
        )

        result = loop.run_turn(
            "CUS-001",
            "How much were the headphones I bought last week?",
        )

        self.assertEqual(result["answer"], "The headphones cost ₹7,498.")
        self.assertEqual(
            [message["role"] for message in result["history"]],
            ["system", "user", "assistant", "tool", "assistant", "tool", "assistant"],
        )
        candidate_result = json.loads(result["history"][3]["content"])
        self.assertEqual(candidate_result["candidates"][0]["order_id"], "ORD-1042")
        self.assertNotIn("candidate_id", candidate_result["candidates"][0])
        self.assertEqual(result["history"][3]["tool_call_id"], "call-candidates")
        self.assertEqual(result["history"][5]["tool_call_id"], "call-details")
        self.assertEqual(len(client.requests), 3)

    def test_streams_statuses_for_actual_tool_activity(self):
        loop, _ = self.make_loop(
            [
                tool_call_message(
                    "call-candidates",
                    "get_recent_product_candidates",
                    {"lookback_days": 7},
                ),
                tool_call_message(
                    "call-details",
                    "get_order_details",
                    {"order_id": "ORD-1042"},
                ),
                {"role": "assistant", "content": "They cost ₹7,498."},
            ]
        )

        events = list(loop.stream_turn("CUS-001", "How much were my headphones?"))

        self.assertEqual(
            [event.get("message") for event in events if event["type"] == "status"],
            [
                "Understanding your question…",
                "Looking for matching products…",
                "Fetching order details…",
            ],
        )
        self.assertEqual(events[-1]["type"], "result")
        self.assertEqual(events[-1]["answer"], "They cost ₹7,498.")
        self.assertEqual(
            [event["content"] for event in events if event["type"] == "delta"],
            ["They cost ₹7,498."],
        )

    def test_follow_up_receives_complete_previous_history(self):
        first_loop, _ = self.make_loop(
            [
                tool_call_message(
                    "call-details",
                    "get_order_details",
                    {"order_id": "ORD-1042"},
                ),
                {"role": "assistant", "content": "They cost ₹7,498."},
            ]
        )
        first_turn = first_loop.run_turn("CUS-001", "How much were my headphones?")
        original_history = deepcopy(first_turn["history"])

        follow_up_loop, client = self.make_loop(
            [
                {"role": "assistant", "content": "They should arrive on 11 August 2026."}
            ]
        )
        second_turn = follow_up_loop.run_turn(
            "CUS-001",
            "When will they arrive?",
            history=first_turn["history"],
        )

        sent_history = client.requests[0]["messages"]
        self.assertEqual(first_turn["history"], original_history)
        self.assertEqual(sent_history[:-1], original_history)
        self.assertEqual(sent_history[-1], {"role": "user", "content": "When will they arrive?"})
        self.assertIn("ORD-1042", sent_history[3]["content"])
        self.assertEqual(
            second_turn["answer"],
            "They should arrive on 11 August 2026.",
        )

    def test_tool_execution_remains_customer_scoped(self):
        loop, _ = self.make_loop(
            [
                tool_call_message(
                    "call-other-order",
                    "get_order_details",
                    {"order_id": "ORD-1087"},
                ),
                {"role": "assistant", "content": "I could not find that order."},
            ]
        )

        result = loop.run_turn("CUS-001", "Tell me about ORD-1087")

        tool_result = json.loads(result["history"][3]["content"])
        self.assertEqual(tool_result, {"found": False, "order": None})

    def test_tool_errors_are_returned_to_model_as_tool_messages(self):
        loop, _ = self.make_loop(
            [
                tool_call_message(
                    "call-invalid",
                    "get_recent_product_candidates",
                    {"lookback_days": 500},
                ),
                {"role": "assistant", "content": "I could not complete that lookup."},
            ]
        )

        result = loop.run_turn("CUS-001", "Find my recent item")

        tool_result = json.loads(result["history"][3]["content"])
        self.assertIn("error", tool_result)
        self.assertIn("0 to 365", tool_result["error"])

    def test_stops_when_model_exceeds_tool_round_limit(self):
        loop, _ = self.make_loop(
            [
                tool_call_message("call-1", "list_orders", {}),
                tool_call_message("call-2", "list_orders", {}),
            ],
            max_tool_rounds=1,
        )

        with self.assertRaisesRegex(RuntimeError, "maximum number of tool rounds"):
            loop.run_turn("CUS-001", "Show my orders")

    def test_rejects_history_without_system_message(self):
        loop, _ = self.make_loop([])

        with self.assertRaisesRegex(ValueError, "system message"):
            loop.run_turn(
                "CUS-001",
                "Hello",
                history=[{"role": "user", "content": "Earlier message"}],
            )


if __name__ == "__main__":
    unittest.main()
