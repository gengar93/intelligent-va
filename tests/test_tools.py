from pathlib import Path

from order_support.repository import OrderRepository
from order_support.tools import execute_tool

DATA_PATH = Path(__file__).parents[1] / "data" / "orders.json"


def test_tool_dispatch_enforces_selected_customer() -> None:
    repository = OrderRepository(DATA_PATH)

    result = execute_tool(
        repository,
        customer_id="CUS-001",
        tool_name="get_order_details",
        arguments={"order_id": "ORD-1107"},
    )

    assert result == {
        "ok": False,
        "error": "No matching order belongs to the selected customer.",
    }


def test_unknown_tool_returns_structured_error() -> None:
    repository = OrderRepository(DATA_PATH)

    result = execute_tool(repository, "CUS-001", "delete_order", {})

    assert result == {"ok": False, "error": "Unknown tool: delete_order"}
