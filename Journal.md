# Project Journal

Last updated: 9 August 2026

## Goal

Build an order-support chatbot incrementally. The first version is intentionally read-only:
a customer can ask about their orders, items, prices, status, and delivery details. The
conversations in `sample_conversations/` describe the longer-term experience, including
actions such as cancellations, returns, address changes, and support tickets.

## Working approach

- Discuss and approve each milestone before implementation.
- Prefer small, testable increments over building the complete chatbot at once.
- Keep customer-specific facts in structured data rather than asking the language model to
  invent or remember them.
- Keep access customer-scoped so one customer cannot retrieve another customer's orders.
- Commit completed milestones after confirmation.

## Current architecture

```text
React dashboard
      |
      | HTTP requests
      v
FastAPI read API
      |
      v
Python repository
      |
      v
Local SQLite database

Read-only chatbot tools
      |
      +-----> Python repository

Conversation loop
      |-----> OpenRouter model
      |
      +-----> Read-only chatbot tools
```

The generated SQLite database and installed dependencies are local artifacts. The schema,
seed data, Python lockfile, and frontend lockfile are committed as their reproducible sources.

## Decisions made

### Initial data model

The first model contains four tables:

- `customers`
- `products`
- `orders`
- `order_items`

Delivery currently belongs to the complete order, so this model does not yet represent split
shipments. This is an intentional first-version limitation.

The order stores `delivery_address` as a historical snapshot and
`payment_method_display` as a safe description such as `Visa ending in 1842`. Complete card
details are never stored. Item prices are stored on `order_items` because a product's current
price may change after purchase. Monetary values use integer minor units to avoid
floating-point errors.

### Technology

- SQLite for the local database because it requires no database server.
- Python 3.12 managed with `uv`.
- FastAPI for the read-only HTTP API.
- OpenRouter through the OpenAI-compatible Python SDK for model requests.
- React, TypeScript, and Vite for the dashboard.
- `react-markdown` with a restricted element set for assistant formatting.
- `pnpm` for frontend dependencies.

## Completed milestones

### 1. Clean restart

The earlier proof of concept was preserved on `codex/archive-initial-poc`. Active development
continues on `codex/clean-restart`, retaining the target sample conversations.

Commit: `55bd3a8 Start clean from sample conversations`

### 2. Data model and sample data

Added the four-table SQLite schema, fictional seed data, a repeatable database reset script,
and database tests. The sample data covers processing, shipped, delivered, and cancelled
orders, including multi-item and multi-quantity examples.

Commit: `855ca24 Add initial read-only order data model`

### 3. Python environment

Configured Python 3.12, the local virtual environment, dependencies, and lockfile through
`uv`.

Commit: `7b01ff6 Configure UV environment with Python 3.12`

### 4. Read-only API

Added customer-scoped repository queries and two endpoints:

```text
GET /api/customers
GET /api/customers/{customer_id}/orders
```

The second endpoint returns the customer, orders, computed totals, delivery and payment
information, and nested order items. SQLite is opened in read-only mode.

Commit: `2a369cc Add read-only customer orders API`

### 5. Customer order dashboard

Added a responsive, single-page React dashboard. It supports customer selection, an order
history list, and complete details for the selected order. It was checked against the real
API at desktop and narrow-screen sizes.

Commit: `19f0c67 Add customer order dashboard`

### 6. Read-only chatbot tools

Added three customer-scoped tools that are testable without a model or network connection:

- `list_orders`
- `get_order_details`
- `get_recent_product_candidates`

The application binds the selected customer rather than accepting a customer ID from the
tool caller. Product candidates come from at most the 10 newest eligible orders and are
capped at 30 results. Python calculates the rolling cutoff for `lookback_days`; zero means
today and `null` means no date filter. Candidate results deliberately contain only an opaque
order ID, name, description, and order timestamp. Python does not perform product text search
or ranking; the model compares the user's wording with these candidates.

### 7. History-preserving conversation loop

Added an OpenRouter-compatible model adapter and a Python conversation loop. The loop keeps
the complete canonical history—including system, user, assistant tool-call, tool-result, and
assistant response messages—and resends it on each model request. Hidden tool results retain
order IDs even when the customer-facing answer does not mention them, allowing follow-up
questions without separate active-order state.

The selected customer is supplied by the application whenever it executes tools and is not
part of the model-visible tool arguments. Product candidates return `order_id` directly, so
the model can call `get_order_details` without a separate candidate-resolution tool.

A controlled live OpenRouter smoke test used the fictional `CUS-001` data. The model found
the recently purchased headphones, fetched their order details, answered the price, and then
answered a delivery-status follow-up from the preserved message history.

### 8. Dashboard chatbot integration

Added `POST /api/chat` as the boundary between the dashboard and conversation loop. The
browser sends the selected customer, message, and an optional opaque conversation ID. The
backend owns the complete canonical history, binds every conversation to one customer, and
returns only the conversation ID and customer-facing answer. Unknown conversations and
attempts to reuse a conversation for another customer are rejected before calling the model.

Added a chat panel to the customer dashboard with sending, error, empty, and reset states.
Changing customers starts a fresh conversation, and internal tool messages and order IDs are
not sent to the browser. A live browser test verified a product-price question, a delivery
follow-up using preserved history, and conversation reset on customer change. The layout was
also verified at desktop and mobile widths.

### 9. Tabbed workspace and live activity

Separated the order overview and assistant into customer-workspace tabs, so the chatbot is
available without scrolling past the order tables. Switching tabs preserves the visible chat;
changing customers still starts a fresh conversation. The tabs support mouse and keyboard
navigation and adapt to narrow screens.

Added `POST /api/chat/stream`, which sends newline-delimited events while the conversation
loop runs. Statuses are tied to real activity: understanding the question, fetching orders,
looking for matching products, or fetching order details. The stream exposes only friendly
status text and the final public response; internal tool arguments, results, and history stay
on the backend. The existing non-streaming endpoint remains available.

### 10. Selected Operations Console interface

Explored three professional interface directions on `codex/ui-concepts` and selected the
Operations Console structure with the Service Desk's near-black, warm-neutral, and orange
palette. Ported that design into the real React dashboard while preserving the live API,
customer isolation, conversation history, and streamed activity statuses.

Customer identity and aggregate metrics now appear only in Overview. Assistant begins with a
neutral, customer-aware welcome state and uses a persistent activity rail for the current
request. The interface follows the system light/dark preference. Assistant messages render a
restricted Markdown subset, including bold emphasis, without accepting raw model HTML. The
standalone prototypes were removed after the port and remain recoverable from commit
`cfb063b`.

### 11. Simplified support interface copy

Simplified the interface language so the workspace emphasizes the customer task instead of
implementation details. The application is now branded as Support Console, the assistant
uses a single descriptive heading, and redundant demo and read-only labels were removed from
the top bar, message composer, and activity rail. The composer footer now keeps its send
action aligned to the right.

Frontend linting, the TypeScript production build, and whitespace checks pass after the
cleanup.

## Current functionality

- Rebuild a consistent local database from checked-in SQL.
- List fictional customers.
- Retrieve only the orders belonging to one customer.
- Show order status, dates, address, payment method, items, quantities, prices, and totals.
- Switch between customers and orders in the dashboard.
- Execute three customer-scoped, read-only order tools without a language model.
- Produce lean recent-product candidates using an optional rolling date window.
- Run a bounded model/tool loop while preserving the complete internal message history.
- Continue follow-up conversations using earlier hidden tool results.
- Chat with the assistant from the selected customer's dashboard.
- Start a fresh conversation explicitly or by changing customers.
- Switch between order and assistant tabs without losing the current chat.
- See live, tool-backed activity while the assistant works.
- Follow the operating system's light or dark appearance automatically.
- Render safe emphasis, lists, and inline code in assistant messages.
- Reject invalid database quantities and prices.
- Return `404` for an unknown customer.

The Python database, repository, API, tool, configuration, model-adapter, and conversation
suite currently contains 43 passing tests. The frontend passes dependency checks, linting,
and a TypeScript production build.

## Running the project

Install the Python environment and rebuild the database:

```bash
uv sync
uv run python scripts/reset_database.py
```

Start the API in one terminal:

```bash
uv run uvicorn order_support.api:app --reload
```

Install and start the dashboard in another terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://127.0.0.1:5173`. Interactive API documentation is available at
`http://127.0.0.1:8000/docs`.

Run verification:

```bash
uv run python -m unittest discover -s tests -v
cd frontend
pnpm peers check
pnpm lint
pnpm build
```

## Current limitations

- Complete history is intentionally unbounded for the first version; long conversations will
  eventually require summarization or compaction.
- Conversation sessions are held only in backend memory and are lost when the API restarts.
- In-memory conversation sessions do not yet expire automatically.
- Orders have one delivery schedule; split shipments are unsupported.
- A customer change must begin a fresh internal history so previous customer tool results do
  not remain in model context.
- There is no tracking history, payment status, invoice content, cancellation process,
  refund process, return process, or support-ticket model.
- The dashboard and API currently run as separate development processes.
- Authentication is not implemented; the customer selector is for fictional demo data.

## Recommended next milestone

Exercise the read-only portions of the target sample conversations and additional natural-
language variations. Use the results to identify tool or prompt gaps, then agree on explicit
completion criteria for the first read-only version.

## Later roadmap

1. Test natural-language variations and read-only portions of the sample conversations.
2. Define completion criteria for the first read-only version.
3. Only then expand the data model and tools for split shipments, cancellations, refunds,
   returns, address changes, invoices, and support tickets.
