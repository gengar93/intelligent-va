"""FastAPI application exposing order data and customer-support chat."""

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from order_support.config import OpenRouterSettings
from order_support.conversation import ConversationLoop
from order_support.model_client import OpenRouterChatClient
from order_support.models import (
    ChatRequest,
    ChatResponse,
    CustomerOrdersRead,
    CustomerRead,
    InvoiceGenerationRead,
    InvoiceTicketRead,
)
from order_support.repository import OrderRepository


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "order_support.db"


def _encode_stream_event(event):
    return json.dumps(event, ensure_ascii=False) + "\n"


def create_app(database_path: Path = DEFAULT_DATABASE_PATH, model_client=None):
    repository = OrderRepository(database_path)
    conversation_loop = None
    conversations = {}
    conversation_lock = Lock()

    def get_conversation_loop():
        nonlocal conversation_loop
        if conversation_loop is None:
            client = model_client
            if client is None:
                client = OpenRouterChatClient(OpenRouterSettings.from_env())
            conversation_loop = ConversationLoop(client, repository)
        return conversation_loop

    def validate_chat_request(request):
        customer_id = request.customer_id.strip()
        message = request.message.strip()
        if not customer_id or not message:
            raise HTTPException(
                status_code=422,
                detail="customer_id and message must not be blank",
            )
        if repository.get_customer_orders(customer_id) is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer_id, message

    def get_session_history(customer_id, conversation_id):
        if conversation_id is None:
            return None
        session = conversations.get(conversation_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if session["customer_id"] != customer_id:
            raise HTTPException(
                status_code=409,
                detail="Conversation belongs to a different customer",
            )
        return session["history"]

    application = FastAPI(
        title="Order Support API",
        version="0.1.0",
        description="Customer and order data for the support demo.",
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

    @application.get(
        "/api/customers/{customer_id}/tickets",
        response_model=list[InvoiceTicketRead],
    )
    def get_open_invoice_tickets(customer_id: str):
        result = repository.get_open_invoice_tickets(customer_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return result

    @application.post(
        "/api/customers/{customer_id}/tickets/{ticket_id}/generate-invoice",
        response_model=InvoiceGenerationRead,
    )
    def generate_invoice(customer_id: str, ticket_id: str):
        generated_at = datetime.now(ZoneInfo("Asia/Kolkata"))
        unique_suffix = uuid4().hex.upper()
        result = repository.generate_invoice_for_ticket(
            customer_id,
            ticket_id,
            invoice_id=f"INV-{unique_suffix}",
            invoice_number=f"INV-{generated_at.year}-{unique_suffix[:8]}",
            in_progress_history_id=f"TSH-{uuid4().hex.upper()}",
            completed_history_id=f"TSH-{uuid4().hex.upper()}",
            generated_at=generated_at.isoformat(timespec="seconds"),
            invoice_item_id_provider=lambda: f"INI-{uuid4().hex.upper()}",
        )
        if result["state"] == "ticket_not_found":
            raise HTTPException(status_code=404, detail="Ticket not found")
        if result["state"] == "ticket_not_open":
            raise HTTPException(status_code=409, detail="Ticket is not open")
        return result

    @application.post("/api/chat", response_model=ChatResponse)
    def chat(request: ChatRequest):
        customer_id, message = validate_chat_request(request)

        with conversation_lock:
            history = get_session_history(customer_id, request.conversation_id)
            conversation_id = request.conversation_id or str(uuid4())

            try:
                loop = get_conversation_loop()
            except ValueError as error:
                raise HTTPException(
                    status_code=503,
                    detail="The assistant is not configured",
                ) from error

            try:
                result = loop.run_turn(
                    customer_id,
                    message,
                    history=history,
                )
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
            except RuntimeError as error:
                raise HTTPException(
                    status_code=502,
                    detail="The assistant could not complete the request",
                ) from error

            conversations[conversation_id] = {
                "customer_id": customer_id,
                "history": result["history"],
            }
            return ChatResponse(
                conversation_id=conversation_id,
                answer=result["answer"],
            )

    @application.post("/api/chat/stream")
    def stream_chat(request: ChatRequest):
        customer_id, message = validate_chat_request(request)
        with conversation_lock:
            get_session_history(customer_id, request.conversation_id)
        conversation_id = request.conversation_id or str(uuid4())

        def generate_events():
            with conversation_lock:
                history = get_session_history(customer_id, request.conversation_id)
                try:
                    loop = get_conversation_loop()
                except ValueError:
                    yield _encode_stream_event(
                        {"type": "error", "message": "The assistant is not configured"}
                    )
                    return

                try:
                    for event in loop.stream_turn(customer_id, message, history=history):
                        if event["type"] == "status":
                            yield _encode_stream_event(
                                {"type": "status", "message": event["message"]}
                            )
                            continue

                        if event["type"] == "delta":
                            yield _encode_stream_event(
                                {"type": "delta", "content": event["content"]}
                            )
                            continue

                        conversations[conversation_id] = {
                            "customer_id": customer_id,
                            "history": event["history"],
                        }
                        yield _encode_stream_event(
                            {
                                "type": "result",
                                "conversation_id": conversation_id,
                                "answer": event["answer"],
                            }
                        )
                except (TypeError, ValueError, RuntimeError):
                    yield _encode_stream_event(
                        {
                            "type": "error",
                            "message": "The assistant could not complete the request",
                        }
                    )

        return StreamingResponse(
            generate_events(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-store"},
        )

    return application


app = create_app()
