"""Customer-scoped tools for order support."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from order_support.repository import OrderRepository


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_orders",
            "description": "List the selected customer's orders, newest first.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Get complete details for one of the selected customer's orders.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order identifier, such as ORD-1042.",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_product_candidates",
            "description": (
                "Return recent purchased-product candidates for the selected customer. "
                "The caller compares names and descriptions with the user's reference, "
                "then uses the matching order_id with get_order_details."
            ),
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "lookback_days": {
                        "anyOf": [
                            {"type": "integer", "minimum": 0, "maximum": 365},
                            {"type": "null"},
                        ],
                        "description": (
                            "Rolling calendar-day window from today; null means no date filter."
                        ),
                    }
                },
                "required": ["lookback_days"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_invoice",
            "description": (
                "Fetch the selected customer's current invoice state for an order. "
                "Use this for every invoice availability or status question, even if "
                "an earlier conversation turn contains invoice or ticket information."
            ),
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order identifier, such as ORD-1042.",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_invoice",
            "description": (
                "Idempotently request invoice generation for one of the selected "
                "customer's orders. Use only when the customer asks to obtain or retry "
                "an unavailable invoice; do not use for a status-only question."
            ),
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order identifier, such as ORD-1042.",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
]


def _utc_now():
    return datetime.now(timezone.utc)


def _new_identifier(prefix):
    return f"{prefix}-{uuid4().hex.upper()}"


class OrderTools:
    """Expose scoped support operations without model-visible customer arguments."""

    def __init__(
        self,
        repository: OrderRepository,
        customer_id: str,
        today_provider=date.today,
        now_provider=_utc_now,
        id_provider=_new_identifier,
    ):
        self._repository = repository
        self._customer_id = customer_id
        self._today_provider = today_provider
        self._now_provider = now_provider
        self._id_provider = id_provider

    def list_orders(self):
        customer_orders = self._repository.get_customer_orders(self._customer_id)
        if customer_orders is None:
            return {"orders": []}

        return {
            "orders": [
                {
                    "order_id": order["order_id"],
                    "status": order["status"],
                    "placed_at": order["placed_at"],
                    "estimated_delivery_date": order["estimated_delivery_date"],
                    "delivered_at": order["delivered_at"],
                    "currency": order["currency"],
                    "total_minor": order["total_minor"],
                    "items": [
                        {
                            "name": item["product_name"],
                            "quantity": item["quantity"],
                        }
                        for item in order["items"]
                    ],
                }
                for order in customer_orders["orders"]
            ]
        }

    def get_order_details(self, order_id):
        order = self._repository.get_order_details(self._customer_id, order_id)
        if order is None:
            return {"found": False, "order": None}

        public_order = {
            key: value
            for key, value in order.items()
            if key not in {"items"}
        }
        public_order["items"] = [
            {
                "sku": item["sku"],
                "name": item["product_name"],
                "description": item["description"],
                "quantity": item["quantity"],
                "unit_price_minor": item["unit_price_minor"],
                "line_total_minor": item["line_total_minor"],
            }
            for item in order["items"]
        ]
        return {"found": True, "order": public_order}

    def get_recent_product_candidates(self, lookback_days):
        self._validate_lookback_days(lookback_days)
        cutoff_date = (
            None
            if lookback_days is None
            else self._today_provider() - timedelta(days=lookback_days)
        )
        candidates = self._repository.get_recent_product_candidates(
            self._customer_id,
            cutoff_date,
        )
        return {"candidates": candidates}

    def get_invoice(self, order_id):
        return self._repository.get_invoice_state(self._customer_id, order_id)

    def request_invoice(self, order_id):
        requested_at = self._now_provider().isoformat()
        return self._repository.request_invoice(
            self._customer_id,
            order_id,
            ticket_id=self._id_provider("TKT"),
            ticket_status_history_id=self._id_provider("TSH"),
            requested_at=requested_at,
        )

    def execute(self, tool_name, arguments):
        if tool_name == "list_orders":
            if arguments:
                raise ValueError("list_orders does not accept arguments")
            return self.list_orders()
        if tool_name == "get_order_details":
            if set(arguments) != {"order_id"}:
                raise ValueError("get_order_details requires only order_id")
            return self.get_order_details(arguments["order_id"])
        if tool_name == "get_recent_product_candidates":
            if set(arguments) != {"lookback_days"}:
                raise ValueError(
                    "get_recent_product_candidates requires only lookback_days"
                )
            return self.get_recent_product_candidates(arguments["lookback_days"])
        if tool_name == "get_invoice":
            if set(arguments) != {"order_id"}:
                raise ValueError("get_invoice requires only order_id")
            return self.get_invoice(arguments["order_id"])
        if tool_name == "request_invoice":
            if set(arguments) != {"order_id"}:
                raise ValueError("request_invoice requires only order_id")
            return self.request_invoice(arguments["order_id"])
        raise ValueError(f"Unknown tool: {tool_name}")

    @staticmethod
    def _validate_lookback_days(lookback_days):
        if lookback_days is None:
            return
        if isinstance(lookback_days, bool) or not isinstance(lookback_days, int):
            raise ValueError("lookback_days must be an integer from 0 to 365, or null")
        if not 0 <= lookback_days <= 365:
            raise ValueError("lookback_days must be an integer from 0 to 365, or null")
