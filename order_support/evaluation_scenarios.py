"""Read-only scenarios derived from the target sample conversations."""

from order_support.evaluation import EvaluationScenario, TurnExpectation


READ_ONLY_SCENARIOS = (
    EvaluationScenario(
        name="track headphones by product reference",
        customer_id="CUS-001",
        turns=(
            TurnExpectation(
                prompt="Where are my headphones?",
                required_tools=(
                    "get_recent_product_candidates",
                    "get_order_details",
                ),
                required_fact_groups=(
                    ("ORD-1042",),
                    ("shipped",),
                    ("11 August", "August 11"),
                ),
            ),
        ),
    ),
    EvaluationScenario(
        name="check a cancelled product order",
        customer_id="CUS-001",
        turns=(
            TurnExpectation(
                prompt="Was my coffee maker order cancelled?",
                required_tools=(
                    "get_recent_product_candidates",
                    "get_order_details",
                ),
                required_fact_groups=(("ORD-1038",), ("cancelled", "canceled")),
            ),
        ),
    ),
    EvaluationScenario(
        name="identify the latest order",
        customer_id="CUS-002",
        turns=(
            TurnExpectation(
                prompt="What is the status of my latest order?",
                required_tools=("list_orders",),
                required_fact_groups=(("ORD-1087",), ("processing",)),
            ),
        ),
    ),
    EvaluationScenario(
        name="follow up on a referenced product",
        customer_id="CUS-001",
        turns=(
            TurnExpectation(
                prompt="How much were my headphones?",
                required_tools=(
                    "get_recent_product_candidates",
                    "get_order_details",
                ),
                required_fact_groups=(("₹7,498", "INR 7,498", "7,498"),),
            ),
            TurnExpectation(
                prompt="And when should they arrive?",
                required_fact_groups=(("11 August", "August 11"),),
            ),
        ),
    ),
    EvaluationScenario(
        name="refuse an unsupported delivery change",
        customer_id="CUS-001",
        turns=(
            TurnExpectation(
                prompt="Move my headphones delivery to Friday.",
                required_tools=(
                    "get_recent_product_candidates",
                    "get_order_details",
                ),
                required_fact_groups=(
                    ("can't", "cannot", "unable", "can’t", "not able"),
                ),
                forbidden_phrases=(
                    "delivery has been rescheduled",
                    "delivery is now scheduled",
                    "i rescheduled",
                ),
            ),
        ),
    ),
)
