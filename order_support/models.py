"""Response models defining the public API contract."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class CustomerRead(BaseModel):
    customer_id: str
    name: str
    email: str


class OrderItemRead(BaseModel):
    order_item_id: str
    product_id: str
    sku: str
    product_name: str
    description: str | None
    quantity: int
    unit_price_minor: int
    line_total_minor: int


class OrderRead(BaseModel):
    order_id: str
    status: Literal["processing", "shipped", "delivered", "cancelled"]
    placed_at: datetime
    estimated_delivery_date: date | None
    delivered_at: datetime | None
    currency: str
    delivery_address: str
    payment_method_display: str
    total_minor: int
    items: list[OrderItemRead]


class CustomerOrdersRead(BaseModel):
    customer: CustomerRead
    orders: list[OrderRead]


class ChatRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
