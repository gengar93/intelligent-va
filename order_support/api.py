"""FastAPI application exposing read-only order data and chat."""

from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from order_support.config import OpenRouterSettings
from order_support.conversation import ConversationLoop
from order_support.model_client import OpenRouterChatClient
from order_support.models import (
    ChatRequest,
    ChatResponse,
    CustomerOrdersRead,
    CustomerRead,
)
from order_support.repository import OrderRepository


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "order_support.db"


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

    @application.post("/api/chat", response_model=ChatResponse)
    def chat(request: ChatRequest):
        customer_id = request.customer_id.strip()
        message = request.message.strip()
        if not customer_id or not message:
            raise HTTPException(
                status_code=422,
                detail="customer_id and message must not be blank",
            )
        if repository.get_customer_orders(customer_id) is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        with conversation_lock:
            conversation_id = request.conversation_id
            history = None
            if conversation_id is not None:
                session = conversations.get(conversation_id)
                if session is None:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                if session["customer_id"] != customer_id:
                    raise HTTPException(
                        status_code=409,
                        detail="Conversation belongs to a different customer",
                    )
                history = session["history"]
            else:
                conversation_id = str(uuid4())

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

    return application


app = create_app()
