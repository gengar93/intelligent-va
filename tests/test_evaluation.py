import json
import unittest

from order_support.evaluation import TurnExpectation, evaluate_turn
from order_support.evaluation_scenarios import READ_ONLY_SCENARIOS


def assistant_tool_call(name, arguments):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": f"call-{name}",
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)},
            }
        ],
    }


class EvaluationTests(unittest.TestCase):
    def evaluate(self, expectation, answer, messages):
        return evaluate_turn(
            "test scenario",
            1,
            expectation,
            {
                "answer": answer,
                "history": [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": expectation.prompt},
                    *messages,
                    {"role": "assistant", "content": answer},
                ],
            },
            customer_order_ids={"ORD-1042", "ORD-1038"},
            all_order_ids={"ORD-1042", "ORD-1038", "ORD-1087"},
        )

    def test_passes_when_tools_and_facts_match(self):
        expectation = TurnExpectation(
            prompt="Where are my headphones?",
            required_tools=(
                "get_recent_product_candidates",
                "get_order_details",
            ),
            required_fact_groups=(
                ("ORD-1042",),
                ("11 August", "August 11"),
            ),
        )

        report = self.evaluate(
            expectation,
            "ORD-1042 is due on August 11.",
            [
                assistant_tool_call(
                    "get_recent_product_candidates", {"lookback_days": None}
                ),
                assistant_tool_call("get_order_details", {"order_id": "ORD-1042"}),
            ],
        )

        self.assertTrue(report.passed)

    def test_reports_missing_tools_and_facts(self):
        expectation = TurnExpectation(
            prompt="Where are my headphones?",
            required_tools=("get_order_details",),
            required_fact_groups=(("shipped",),),
        )

        report = self.evaluate(expectation, "I found your order.", [])

        self.assertEqual(
            {failure.code for failure in report.failures},
            {"missing_required_tools", "missing_required_fact"},
        )

    def test_rejects_customer_id_and_foreign_order_tool_arguments(self):
        expectation = TurnExpectation(prompt="Where is my order?")

        report = self.evaluate(
            expectation,
            "I checked your order.",
            [
                assistant_tool_call(
                    "get_order_details",
                    {"customer_id": "CUS-002", "order_id": "ORD-1087"},
                )
            ],
        )

        self.assertEqual(
            {failure.code for failure in report.failures},
            {"customer_id_exposed", "foreign_order_tool_call"},
        )

    def test_rejects_foreign_order_ids_in_answer(self):
        report = self.evaluate(
            TurnExpectation(prompt="What is my latest order?"),
            "Your latest order is ORD-1087.",
            [],
        )

        self.assertEqual(report.failures[0].code, "foreign_order_in_answer")

    def test_rejects_foreign_order_ids_in_tool_results(self):
        expectation = TurnExpectation(prompt="What is my latest order?")
        tool_result = {
            "role": "tool",
            "tool_call_id": "call-list_orders",
            "content": json.dumps({"orders": [{"order_id": "ORD-1087"}]}),
        }

        report = self.evaluate(expectation, "I checked your orders.", [tool_result])

        self.assertEqual(report.failures[0].code, "foreign_order_tool_result")

    def test_rejects_non_read_only_tools_and_forbidden_claims(self):
        expectation = TurnExpectation(
            prompt="Move my delivery.",
            forbidden_phrases=("delivery has been rescheduled",),
        )

        report = self.evaluate(
            expectation,
            "Your delivery has been rescheduled.",
            [assistant_tool_call("reschedule_delivery", {"order_id": "ORD-1042"})],
        )

        self.assertEqual(
            {failure.code for failure in report.failures},
            {"non_read_only_tool", "forbidden_claim"},
        )

    def test_accepts_alternative_refusal_wording(self):
        expectation = TurnExpectation(
            prompt="Move my delivery.",
            required_fact_groups=(("can't", "not able"),),
        )

        report = self.evaluate(
            expectation,
            "I'm not able to reschedule a delivery.",
            [],
        )

        self.assertTrue(report.passed)

    def test_evaluates_only_the_current_turn_tool_calls(self):
        expectation = TurnExpectation(prompt="And when will it arrive?")
        history = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "Where are my headphones?"},
            assistant_tool_call("get_order_details", {"order_id": "ORD-1042"}),
            {"role": "tool", "tool_call_id": "call", "content": "{}"},
            {"role": "assistant", "content": "It shipped."},
            {"role": "user", "content": expectation.prompt},
            {"role": "assistant", "content": "It arrives August 11."},
        ]

        report = evaluate_turn(
            "follow up",
            2,
            expectation,
            {"answer": "It arrives August 11.", "history": history},
            customer_order_ids={"ORD-1042"},
            all_order_ids={"ORD-1042", "ORD-1087"},
        )

        self.assertTrue(report.passed)

    def test_scenario_catalog_covers_read_only_and_unsupported_requests(self):
        prompts = [
            turn.prompt
            for scenario in READ_ONLY_SCENARIOS
            for turn in scenario.turns
        ]

        self.assertGreaterEqual(len(READ_ONLY_SCENARIOS), 5)
        self.assertTrue(any("latest order" in prompt for prompt in prompts))
        self.assertTrue(any("Move my" in prompt for prompt in prompts))
        self.assertTrue(any(len(scenario.turns) > 1 for scenario in READ_ONLY_SCENARIOS))


if __name__ == "__main__":
    unittest.main()
