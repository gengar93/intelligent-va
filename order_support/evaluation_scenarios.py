"""Read-only scenarios derived from the target sample conversations."""

from order_support.evaluation import EvaluationScenario, TurnExpectation


READ_ONLY_SCENARIOS = (
    EvaluationScenario(
        name="track headset by product reference",
        customer_id="CUS-001",
        turns=(
            TurnExpectation(
                prompt="Where is my headset?",
                required_tools=(
                    "get_recent_product_candidates",
                    "get_order_details",
                ),
                required_fact_groups=(
                    ("ORD-1042",),
                    ("shipped",),
                    ("21 August", "August 21"),
                ),
            ),
        ),
    ),
    EvaluationScenario(
        name="check a cancelled monitor order",
        customer_id="CUS-001",
        turns=(
            TurnExpectation(
                prompt="Was my monitor order cancelled?",
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
                prompt="How much was my headset?",
                required_tools=(
                    "get_recent_product_candidates",
                    "get_order_details",
                ),
                required_fact_groups=(("$129.99", "USD 129.99", "129.99"),),
            ),
            TurnExpectation(
                prompt="And when should they arrive?",
                required_fact_groups=(("21 August", "August 21"),),
            ),
        ),
    ),
    EvaluationScenario(
        name="refuse an unsupported delivery change",
        customer_id="CUS-001",
        turns=(
            TurnExpectation(
                prompt="Move my headset delivery to Monday.",
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
    EvaluationScenario(
        name="decline an unrelated question without order lookups",
        customer_id="CUS-001",
        turns=(
            TurnExpectation(
                prompt="How do I bake a chocolate cake?",
                forbidden_tools=(
                    "list_orders",
                    "get_order_details",
                    "get_recent_product_candidates",
                    "get_invoice",
                    "request_invoice",
                ),
                required_fact_groups=(("orders", "order"), ("invoices", "invoice")),
                forbidden_phrases=(
                    "preheat the oven",
                    "cups of flour",
                    "cake recipe",
                ),
            ),
        ),
    ),
    EvaluationScenario(
        name="answer a focused payment-method question",
        customer_id="CUS-001",
        turns=(
            TurnExpectation(
                prompt="What payment method did I use for my headset?",
                required_tools=(
                    "get_recent_product_candidates",
                    "get_order_details",
                ),
                required_fact_groups=(("Visa ending in 1842", "Visa", "1842"),),
            ),
        ),
    ),
)
