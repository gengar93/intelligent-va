"""Gradio entry point for the order support chatbot POC."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import gradio as gr
from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError

from order_support.chatbot import OrderChatbot
from order_support.config import Settings
from order_support.repository import OrderRepository

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "orders.json"

CSS = """
.gradio-container { max-width: 1120px !important; }
.app-shell { margin: 1rem auto; }
.eyebrow { color: #5b6b63; font-size: 0.78rem; font-weight: 700; letter-spacing: .12em; }
.subtitle { color: #5f6b65; max-width: 720px; margin-top: -0.4rem; }
.customer-card { border: 1px solid #dfe7e2; border-radius: 14px; padding: 12px 14px; }
footer { display: none !important; }
"""


def configure_logging() -> None:
    """Show application timing logs without enabling verbose dependency logs."""

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("order_support").setLevel(logging.INFO)


def build_app() -> gr.Blocks:
    settings = Settings.from_env()
    repository = OrderRepository(DATA_PATH)
    customers = repository.list_customers()
    customer_choices = [
        (f"{customer['name']} · {customer['customer_id']}", customer["customer_id"])
        for customer in customers
    ]

    chatbot: OrderChatbot | None = None
    if settings.openrouter_api_key:
        chatbot = OrderChatbot(
            repository=repository,
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
        )

    def respond(
        message: str,
        history: list[dict[str, Any]],
        customer_id: str,
        active_order_id: str | None,
    ) -> tuple[str, str | None]:
        if chatbot is None:
            return (
                "The API key has not been configured yet. Add `OPENROUTER_API_KEY` to `.env`, "
                "restart the app, and try again.",
                active_order_id,
            )

        try:
            reply = chatbot.reply(message, history, customer_id, active_order_id)
            return reply.text, reply.active_order_id
        except AuthenticationError:
            return (
                "The API key was rejected. Check `OPENROUTER_API_KEY` in `.env` and restart.",
                active_order_id,
            )
        except RateLimitError:
            return (
                "The model is temporarily rate-limited. Please wait a moment and try again.",
                active_order_id,
            )
        except APIConnectionError:
            return (
                "I couldn't reach the model service. Check your connection and try again.",
                active_order_id,
            )
        except APIError as error:
            return f"The model service returned an error: {error.message}", active_order_id

    with gr.Blocks(title="Parcelwise · Order Support") as demo:
        with gr.Column(elem_classes="app-shell"):
            gr.HTML('<div class="eyebrow">PARCELWISE SUPPORT</div>')
            gr.Markdown("# Your orders, without the runaround")
            gr.Markdown(
                "Ask about recent orders, products, quantities, tracking, or delivery dates. "
                "This demo is read-only and uses fictional customer data.",
                elem_classes="subtitle",
            )

            with gr.Row():
                with gr.Column(scale=1, min_width=260, elem_classes="customer-card"):
                    gr.Markdown("### Demo customer")
                    customer_selector = gr.Dropdown(
                        choices=customer_choices,
                        value=customer_choices[0][1],
                        label="Continue as",
                        info="Changing customer starts a fresh conversation.",
                    )
                    gr.Markdown(
                        "**Try asking**\n\n"
                        "- What are my recent orders?\n"
                        "- Where are my headphones?\n"
                        "- What was in my latest order?"
                    )
                    gr.Markdown(f"Model: `{settings.openrouter_model}` via OpenRouter")

                with gr.Column(scale=3, min_width=520):
                    active_order_state = gr.State(value=None)
                    chat_panel = gr.Chatbot(
                        value=[
                            {
                                "role": "assistant",
                                "content": (
                                    "Hi! I can help you look up orders, items, tracking, "
                                    "and delivery dates. What would you like to know?"
                                ),
                            }
                        ],
                        height=520,
                        placeholder="Select a demo customer and ask about their orders.",
                    )
                    gr.ChatInterface(
                        fn=respond,
                        chatbot=chat_panel,
                        additional_inputs=[customer_selector, active_order_state],
                        additional_outputs=[active_order_state],
                        textbox=gr.Textbox(
                            placeholder="Ask about an order…",
                            container=False,
                            autofocus=True,
                        ),
                    )

            customer_selector.change(
                fn=lambda: ([], None),
                outputs=[chat_panel, active_order_state],
            )

    return demo


if __name__ == "__main__":
    configure_logging()
    build_app().launch(css=CSS)
