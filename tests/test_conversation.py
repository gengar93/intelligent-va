import json
import tempfile
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path

from order_support.conversation import SYSTEM_PROMPT, ConversationLoop
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


class FakeStreamingModelClient:
    def __init__(self, turns):
        self.turns = list(turns)

    def complete(self, messages, tools):
        raise AssertionError("complete should not be used when streaming is available")

    def stream_complete(self, messages, tools):
        if not self.turns:
            raise AssertionError("Fake streaming model has no turn remaining")
        turn = self.turns.pop(0)
        for chunk in turn["chunks"]:
            yield {"type": "content_delta", "delta": chunk}
        yield {"type": "message", "message": deepcopy(turn["message"])}


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

    def test_invoice_status_follow_up_fetches_fresh_data(self):
        loop, client = self.make_loop(
            [
                tool_call_message(
                    "call-invoice",
                    "get_invoice",
                    {"order_id": "ORD-1087"},
                ),
                {
                    "role": "assistant",
                    "content": "Your invoice request is still in progress.",
                },
            ]
        )

        result = loop.run_turn(
            "CUS-002",
            "Is my invoice ready now?",
            history=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Please get my invoice for ORD-1087."},
                {"role": "assistant", "content": "It was being generated."},
            ],
        )

        self.assertEqual(client.requests[0]["messages"][-1]["content"], "Is my invoice ready now?")
        tool_result = json.loads(result["history"][-2]["content"])
        self.assertEqual(tool_result["state"], "in_progress")
        self.assertEqual(
            result["answer"],
            "Your invoice request is still in progress.",
        )

    def test_invoice_request_tool_reports_created_ticket(self):
        loop, _ = self.make_loop(
            [
                tool_call_message(
                    "call-get-invoice",
                    "get_invoice",
                    {"order_id": "ORD-1095"},
                ),
                tool_call_message(
                    "call-request-invoice",
                    "request_invoice",
                    {"order_id": "ORD-1095"},
                ),
                {
                    "role": "assistant",
                    "content": "I created an invoice request. It is queued.",
                },
            ]
        )

        result = loop.run_turn("CUS-002", "Please get my invoice for ORD-1095.")

        request_result = json.loads(result["history"][-2]["content"])
        self.assertTrue(request_result["created"])
        self.assertEqual(request_result["state"], "queued")

    def test_system_prompt_requires_fresh_invoice_status(self):
        self.assertIn("call get_invoice", SYSTEM_PROMPT)
        self.assertIn("Never report invoice status from conversation history", SYSTEM_PROMPT)
        self.assertIn("reason order_cancelled", SYSTEM_PROMPT)

    def test_system_prompt_requires_narration_and_metadata_block(self):
        self.assertIn("one short sentence", SYSTEM_PROMPT)
        self.assertIn("card_order_ids", SYSTEM_PROMPT)
        self.assertIn("follow_ups", SYSTEM_PROMPT)

    def test_streaming_classifies_segments_and_hides_metadata_block(self):
        answer_content = (
            "All good.\n\n"
            "```json\n"
            '{"card_order_ids": ["ORD-1042"], "follow_ups": ["A?", "B?"]}\n'
            "```"
        )
        client = FakeStreamingModelClient(
            [
                {
                    "chunks": ["Let me check", " your orders."],
                    "message": {
                        "role": "assistant",
                        "content": "Let me check your orders.",
                        "tool_calls": [
                            {
                                "id": "call-details",
                                "type": "function",
                                "function": {
                                    "name": "get_order_details",
                                    "arguments": json.dumps({"order_id": "ORD-1042"}),
                                },
                            }
                        ],
                    },
                },
                {
                    # The fence is split across chunks to exercise suppression.
                    "chunks": ["All good.\n\n`", "``json\n{\"card_order_ids\":",
                               ' ["ORD-1042"], "follow_ups": ["A?", "B?"]}\n```'],
                    "message": {"role": "assistant", "content": answer_content},
                },
            ]
        )
        loop = ConversationLoop(client, self.repository)

        events = list(loop.stream_turn("CUS-001", "Where are my headphones?"))

        streamed_text = "".join(
            event["content"] for event in events if event["type"] == "delta"
        )
        self.assertNotIn("`", streamed_text)
        self.assertIn("Let me check your orders.", streamed_text)

        segment_kinds = [
            event["kind"] for event in events if event["type"] == "segment"
        ]
        self.assertEqual(segment_kinds, ["reasoning", "answer"])

        tool_call = next(event for event in events if event["type"] == "tool_call")
        self.assertEqual(tool_call["name"], "get_order_details")
        self.assertEqual(tool_call["arguments"], {"order_id": "ORD-1042"})

        tool_result = next(event for event in events if event["type"] == "tool_result")
        self.assertTrue(tool_result["result"]["found"])
        self.assertGreaterEqual(tool_result["elapsed_ms"], 0)

        cards = next(event for event in events if event["type"] == "cards")
        self.assertEqual(
            [order["order_id"] for order in cards["orders"]],
            ["ORD-1042"],
        )
        self.assertEqual(
            cards["orders"][0]["items"][0]["image_url"],
            "/products/headphones.svg",
        )

        follow_ups = next(event for event in events if event["type"] == "follow_ups")
        self.assertEqual(follow_ups["suggestions"], ["A?", "B?"])

        result = events[-1]
        self.assertEqual(result["answer"], "All good.")
        self.assertEqual(result["history"][-1]["content"], answer_content)

    def test_missing_metadata_falls_back_to_touched_orders(self):
        loop, _ = self.make_loop(
            [
                tool_call_message(
                    "call-details",
                    "get_order_details",
                    {"order_id": "ORD-1042"},
                ),
                {"role": "assistant", "content": "Here is your order."},
            ]
        )

        events = list(loop.stream_turn("CUS-001", "Show my headphones order"))

        cards = next(event for event in events if event["type"] == "cards")
        self.assertEqual(
            [order["order_id"] for order in cards["orders"]],
            ["ORD-1042"],
        )
        follow_ups = next(event for event in events if event["type"] == "follow_ups")
        self.assertEqual(
            follow_ups["suggestions"],
            [
                "When will ORD-1042 arrive?",
                "Can I download the invoice for ORD-1042?",
            ],
        )
        self.assertEqual(events[-1]["answer"], "Here is your order.")

    def test_explicit_empty_card_list_suppresses_fallback_cards(self):
        loop, _ = self.make_loop(
            [
                tool_call_message(
                    "call-details",
                    "get_order_details",
                    {"order_id": "ORD-1042"},
                ),
                {
                    "role": "assistant",
                    "content": (
                        "You have two orders.\n\n"
                        "```json\n"
                        '{"card_order_ids": [], "follow_ups": ["Tell me more?"]}\n'
                        "```"
                    ),
                },
            ]
        )

        events = list(loop.stream_turn("CUS-001", "How many orders do I have?"))

        cards = next(event for event in events if event["type"] == "cards")
        self.assertEqual(cards["orders"], [])
        follow_ups = next(event for event in events if event["type"] == "follow_ups")
        self.assertEqual(follow_ups["suggestions"], ["Tell me more?"])
        self.assertEqual(events[-1]["answer"], "You have two orders.")


if __name__ == "__main__":
    unittest.main()
