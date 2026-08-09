"""Run the deterministic read-only evaluation scenarios against the configured model."""

import argparse
import json

from order_support.config import OpenRouterSettings
from order_support.conversation import ConversationLoop
from order_support.evaluation import evaluate_turn
from order_support.evaluation_scenarios import READ_ONLY_SCENARIOS
from order_support.model_client import OpenRouterChatClient
from order_support.repository import OrderRepository
from scripts.reset_database import DEFAULT_DATABASE_PATH


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        help="Run only scenarios whose name contains this case-insensitive text.",
    )
    arguments = parser.parse_args()
    repository = OrderRepository(DEFAULT_DATABASE_PATH)
    settings = OpenRouterSettings.from_env()
    loop = ConversationLoop(OpenRouterChatClient(settings), repository)
    customer_order_ids = {
        customer["customer_id"]: {
            order["order_id"]
            for order in repository.get_customer_orders(customer["customer_id"])["orders"]
        }
        for customer in repository.list_customers()
    }
    all_order_ids = set().union(*customer_order_ids.values())
    reports = []

    scenarios = READ_ONLY_SCENARIOS
    if arguments.scenario:
        query = arguments.scenario.casefold()
        scenarios = tuple(
            scenario for scenario in scenarios if query in scenario.name.casefold()
        )
        if not scenarios:
            parser.error(f"No scenario name contains {arguments.scenario!r}")

    for scenario in scenarios:
        history = None
        for turn_number, expectation in enumerate(scenario.turns, start=1):
            try:
                result = loop.run_turn(
                    scenario.customer_id,
                    expectation.prompt,
                    history=history,
                )
            except (RuntimeError, ValueError) as error:
                reports.append(
                    {
                        "scenario": scenario.name,
                        "turn": turn_number,
                        "passed": False,
                        "failures": [
                            {
                                "code": "run_failed",
                                "message": str(error),
                            }
                        ],
                    }
                )
                break
            history = result["history"]
            report = evaluate_turn(
                scenario.name,
                turn_number,
                expectation,
                result,
                customer_order_ids=customer_order_ids[scenario.customer_id],
                all_order_ids=all_order_ids,
            )
            reports.append(
                {
                    "scenario": report.scenario,
                    "turn": report.turn,
                    "answer": result["answer"],
                    "passed": report.passed,
                    "failures": [failure.__dict__ for failure in report.failures],
                }
            )

    output = {"model": settings.model, "reports": reports}
    print(json.dumps(output, indent=2, ensure_ascii=False))
    raise SystemExit(0 if all(report["passed"] for report in reports) else 1)


if __name__ == "__main__":
    main()
