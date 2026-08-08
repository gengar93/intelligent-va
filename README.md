# Parcelwise Order Support POC

A small, read-only order-support chatbot built with Python, Gradio, and OpenRouter. It
uses fictional customer and order data.

## What it can do

- List a selected customer's recent orders.
- Find an order by product name or product attribute.
- Explain order contents, quantities, totals, status, tracking, and delivery dates.
- Understand follow-up questions using recent chat history.
- Preserve the currently discussed order in explicit per-session state.
- Keep all lookups scoped to the customer selected in the UI.

The demo deliberately does not change orders or handle payments, refunds, cancellations,
returns, address changes, or rescheduling.

## Setup

The repository uses [uv](https://docs.astral.sh/uv/) and Python 3.12.

1. Put your OpenRouter API key in `.env`:

   ```dotenv
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

2. Install the locked dependencies:

   ```bash
   uv sync
   ```

3. Start the app:

   ```bash
   uv run python app.py
   ```

4. Open the local URL printed in the terminal, normally `http://127.0.0.1:7860`.

The default model is configured in `.env`. You may change `OPENROUTER_MODEL` to another
[OpenRouter model that supports tool calling](https://openrouter.ai/models?supported_parameters=tools)
without editing the Python source.

## Useful demo paths

Start as **Aarav Sharma**:

1. “Show my recent orders.”
2. “Which one contains the headphones?”
3. “When will that arrive?”
4. “What color are they?”

Start as **Meera Iyer**:

1. “What is delayed?”
2. “What else is in that order?”
3. “What is the revised delivery date?”

Start as **Kabir Khan**:

1. “What is arriving today?”
2. “How many items are in it?”
3. “What storage size did I choose?”

## Quality checks

```bash
uv run pytest
uv run ruff check .
```

Tests cover the local repository, customer isolation, product search, and tool dispatch.
They do not call OpenRouter.

## Timing logs

The terminal records the duration of every model request, local tool call, and complete
chat turn. Start the app normally and watch the terminal while submitting questions:

```text
model_call_completed turn_id=3f18a1c2 round=1 duration_ms=1820.4 model=openai/gpt-5.6-luna requested_tools=1
tool_call_completed turn_id=3f18a1c2 round=1 tool=get_order_details duration_ms=0.1 ok=True
model_call_completed turn_id=3f18a1c2 round=2 duration_ms=1475.2 model=openai/gpt-5.6-luna requested_tools=0
chat_turn_completed turn_id=3f18a1c2 total_ms=3296.4 customer_id=CUS-002 active_order_id=ORD-1098 model_calls=2 tool_calls=1
```

Messages and credentials are not written to these logs. The shared `turn_id` makes it
possible to group all activity produced by one submitted question.

## Project layout

```text
.
├── app.py                    # Gradio UI
├── data/orders.json          # Fictional customers and orders
├── order_support/
│   ├── chatbot.py            # OpenRouter client and tool-calling loop
│   ├── config.py             # Environment configuration
│   ├── repository.py         # Read-only JSON queries
│   └── tools.py              # Tool schemas and safe dispatch
├── tests/                    # Offline tests
├── .env                      # Local secret; ignored by Git
├── .env.example              # Shareable configuration template
└── pyproject.toml            # uv project and dependencies
```
