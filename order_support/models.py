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
    invoice_status: Literal[
        "not_requested", "queued", "in_progress", "available", "failed", "cancelled"
    ]
    items: list[OrderItemRead]


class CustomerOrdersRead(BaseModel):
    customer: CustomerRead
    orders: list[OrderRead]


class InvoiceTicketRead(BaseModel):
    ticket_id: str
    order_id: str
    status: Literal["queued", "in_progress"]
    created_at: datetime
    updated_at: datetime
    order_status: Literal["processing", "shipped", "delivered", "cancelled"]
    currency: str
    item_count: int
    total_minor: int


class GeneratedInvoiceRead(BaseModel):
    invoice_id: str
    invoice_number: str
    order_id: str
    issued_at: datetime
    document_url: str


class InvoiceGenerationRead(BaseModel):
    state: Literal["available"]
    created: bool
    invoice: GeneratedInvoiceRead


class ChatRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
