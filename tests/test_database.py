import sqlite3
from pathlib import Path

from scripts.reset_database import reset_database


def connect_seeded_database(tmp_path: Path) -> sqlite3.Connection:
    database_path = tmp_path / "orders.db"
    reset_database(database_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def test_seed_data_is_referentially_valid(tmp_path: Path) -> None:
    with connect_seeded_database(tmp_path) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 5
        assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 7


def test_split_order_maps_each_item_to_its_shipment(tmp_path: Path) -> None:
    with connect_seeded_database(tmp_path) as connection:
        rows = connection.execute(
            """
            SELECT p.name, s.status, a.label
            FROM shipments AS s
            JOIN shipment_items AS si USING (shipment_id)
            JOIN order_items AS oi USING (order_item_id)
            JOIN products AS p USING (product_id)
            JOIN addresses AS a ON a.address_id = s.delivery_address_id
            WHERE s.order_id = 'ORD-1103'
            ORDER BY p.name
            """
        ).fetchall()

    assert [tuple(row) for row in rows] == [
        ('PaperNest A5 Notebook Set', 'preparing', 'office'),
        ('ReadLite Desk Lamp', 'in_transit', 'home'),
    ]


def test_cancellation_and_refund_have_independent_states(tmp_path: Path) -> None:
    with connect_seeded_database(tmp_path) as connection:
        awaiting_refund = connection.execute(
            """
            SELECT c.status AS cancellation_status, r.status AS refund_status
            FROM cancellations AS c
            LEFT JOIN refunds AS r USING (cancellation_id)
            WHERE c.cancellation_id = 'CAN-5521'
            """
        ).fetchone()
        initiated_refund = connection.execute(
            """
            SELECT c.status AS cancellation_status, r.status AS refund_status
            FROM cancellations AS c
            JOIN refunds AS r USING (cancellation_id)
            WHERE c.cancellation_id = 'CAN-5408'
            """
        ).fetchone()

    assert tuple(awaiting_refund) == ('awaiting_approval', None)
    assert tuple(initiated_refund) == ('completed', 'initiated')


def test_money_is_stored_in_minor_units(tmp_path: Path) -> None:
    with connect_seeded_database(tmp_path) as connection:
        order = connection.execute(
            "SELECT total_minor FROM orders WHERE order_id = 'ORD-1042'"
        ).fetchone()
        refund = connection.execute(
            "SELECT amount_minor FROM refunds WHERE refund_id = 'REF-1038'"
        ).fetchone()

    assert order["total_minor"] == 749_800
    assert refund["amount_minor"] == 429_900
