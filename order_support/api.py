"""FastAPI application exposing read-only order data."""

from pathlib import Path

from fastapi import FastAPI, HTTPException

from order_support.models import CustomerOrdersRead, CustomerRead
from order_support.repository import OrderRepository


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "order_support.db"


def create_app(database_path: Path = DEFAULT_DATABASE_PATH):
    repository = OrderRepository(database_path)
    application = FastAPI(
        title="Order Support API",
        version="0.1.0",
        description="Read-only customer and order data for the support demo.",
    )

    @application.get("/api/customers", response_model=list[CustomerRead])
    def list_customers():
        return repository.list_customers()

    @application.get(
        "/api/customers/{customer_id}/orders",
        response_model=CustomerOrdersRead,
    )
    def get_customer_orders(customer_id: str):
        result = repository.get_customer_orders(customer_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return result

    return application


app = create_app()
