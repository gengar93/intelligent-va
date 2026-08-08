from pathlib import Path

from order_support.repository import OrderRepository

DATA_PATH = Path(__file__).parents[1] / "data" / "orders.json"


def test_lists_customers_and_scopes_orders() -> None:
    repository = OrderRepository(DATA_PATH)

    assert len(repository.list_customers()) == 3
    orders = repository.list_orders("CUS-001")
    assert [order["order_id"] for order in orders] == ["ORD-1042", "ORD-1038", "ORD-1029"]


def test_get_order_rejects_another_customers_order() -> None:
    repository = OrderRepository(DATA_PATH)

    assert repository.get_order("CUS-001", "ORD-1107") is None
    assert repository.get_order("CUS-002", "ord-1107")["status"] == "processing"


def test_finds_orders_by_product_and_attribute() -> None:
    repository = OrderRepository(DATA_PATH)

    headphones = repository.find_orders_by_product("CUS-001", "black headphones")
    shoes = repository.find_orders_by_product("CUS-002", "UK 6")

    assert [order["order_id"] for order in headphones] == ["ORD-1042"]
    assert [order["order_id"] for order in shoes] == ["ORD-1107"]


def test_returns_no_matches_for_empty_product_query() -> None:
    repository = OrderRepository(DATA_PATH)

    assert repository.find_orders_by_product("CUS-001", "  ") == []
