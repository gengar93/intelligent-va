"""FastAPI application exposing order data and customer-support chat."""

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse

from order_support.config import OpenRouterSettings, load_model_catalog
from order_support.conversation import ConversationLoop
from order_support.invoice_pdf import render_invoice_pdf
from order_support.model_client import OpenRouterChatClient
from order_support.models import (
    ChatRequest,
    ChatResponse,
    ClosedInvoiceTicketRead,
    CustomerOrdersRead,
    CustomerRead,
    InvoiceGenerationRead,
    InvoiceTicketRead,
    ModelOptionsRead,
)
from order_support.repository import OrderRepository
from scripts.reset_database import build_database


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "order_support.db"


def _encode_stream_event(event):
    return json.dumps(event, ensure_ascii=False) + "\n"


def create_app(
    database_path: Path = DEFAULT_DATABASE_PATH,
    model_client=None,
    model_catalog=None,
):
    database_path = Path(database_path).resolve()
    if not database_path.is_file():
        build_database(database_path)

    model_catalog = model_catalog or load_model_catalog()
    repository = OrderRepository(database_path)
    conversation_loops = {}
    openrouter_settings = None
    conversations = {}
    conversation_lock = Lock()
    database_generation = 0

    def get_conversation_loop(model, route):
        nonlocal openrouter_settings
        key = (model.id, route.id)
        if key not in conversation_loops:
            client = model_client
            if client is None:
                if openrouter_settings is None:
                    openrouter_settings = OpenRouterSettings.from_env()
                client = OpenRouterChatClient(
                    openrouter_settings,
                    model.slug,
                    provider=route.provider,
                )
            conversation_loops[key] = ConversationLoop(client, repository)
        return conversation_loops[key]

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
        try:
            model, route = model_catalog.resolve(request.model_id, request.route_id)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return customer_id, message, model, route

    def get_session_history(customer_id, conversation_id, model_id, route_id):
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
        if session["model_id"] != model_id or session["route_id"] != route_id:
            raise HTTPException(
                status_code=409,
                detail="Conversation uses a different model configuration",
            )
        return session["history"]

    application = FastAPI(
        title="Order Support API",
        version="0.1.0",
        description="Customer and order data for the support demo.",
    )

    @application.post("/api/demo/reset")
    def reset_demo_database():
        nonlocal database_generation
        with conversation_lock:
            build_database(database_path)
            conversations.clear()
            database_generation += 1
        return {"status": "reset"}

    @application.get("/api/model-options", response_model=ModelOptionsRead)
    def get_model_options():
        return {
            "default_model": model_catalog.default_model,
            "models": [
                {
                    "id": model.id,
                    "label": model.label,
                    "default_route": model.default_route,
                    "routes": [
                        {"id": route.id, "label": route.label}
                        for route in model.routes
                    ],
                }
                for model in model_catalog.models
            ],
        }

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

    @application.get("/api/customers/{customer_id}/orders/{order_id}/invoice.pdf")
    def download_invoice_pdf(customer_id: str, order_id: str):
        invoice = repository.get_order_invoice(customer_id, order_id)
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        pdf_bytes = render_invoice_pdf(invoice)
        filename = f"{invoice['invoice_number']}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @application.get(
        "/api/customers/{customer_id}/tickets",
        response_model=list[InvoiceTicketRead],
    )
    def get_open_invoice_tickets(customer_id: str):
        result = repository.get_open_invoice_tickets(customer_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return result

    @application.get(
        "/api/customers/{customer_id}/tickets/closed",
        response_model=list[ClosedInvoiceTicketRead],
    )
    def get_closed_invoice_tickets(customer_id: str):
        result = repository.get_closed_invoice_tickets(customer_id)
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
        customer_id, message, model, route = validate_chat_request(request)

        with conversation_lock:
            history = get_session_history(
                customer_id,
                request.conversation_id,
                model.id,
                route.id,
            )
            conversation_id = request.conversation_id or str(uuid4())

            try:
                loop = get_conversation_loop(model, route)
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
                "model_id": model.id,
                "route_id": route.id,
                "history": result["history"],
            }
            return ChatResponse(
                conversation_id=conversation_id,
                answer=result["answer"],
            )

    @application.post("/api/chat/stream")
    def stream_chat(request: ChatRequest):
        nonlocal database_generation
        customer_id, message, model, route = validate_chat_request(request)
        with conversation_lock:
            get_session_history(
                customer_id,
                request.conversation_id,
                model.id,
                route.id,
            )
            turn_database_generation = database_generation
        conversation_id = request.conversation_id or str(uuid4())

        def generate_events():
            # Hold the lock only for shared-state access (session history read and
            # the result write) — never across the model stream itself. Otherwise an
            # aborted request keeps the lock during the slow upstream call and blocks
            # the customer's next message.
            with conversation_lock:
                history = get_session_history(
                    customer_id,
                    request.conversation_id,
                    model.id,
                    route.id,
                )
                try:
                    loop = get_conversation_loop(model, route)
                except ValueError:
                    loop = None
            if loop is None:
                yield _encode_stream_event(
                    {"type": "error", "message": "The assistant is not configured"}
                )
                return

            try:
                for event in loop.stream_turn(customer_id, message, history=history):
                    if event["type"] != "result":
                        yield _encode_stream_event(event)
                        continue

                    with conversation_lock:
                        if turn_database_generation == database_generation:
                            conversations[conversation_id] = {
                                "customer_id": customer_id,
                                "model_id": model.id,
                                "route_id": route.id,
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
