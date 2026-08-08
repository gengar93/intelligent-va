# Project Journal

Last updated: 8 August 2026

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
- React, TypeScript, and Vite for the dashboard.
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

## Current functionality

- Rebuild a consistent local database from checked-in SQL.
- List fictional customers.
- Retrieve only the orders belonging to one customer.
- Show order status, dates, address, payment method, items, quantities, prices, and totals.
- Switch between customers and orders in the dashboard.
- Reject invalid database quantities and prices.
- Return `404` for an unknown customer.

The Python database, repository, and API suite currently contains 14 passing tests. The
frontend passes dependency checks, linting, and a TypeScript production build.

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

- There is no chatbot or language-model integration yet.
- There are no model-facing tools yet.
- Orders have one delivery schedule; split shipments are unsupported.
- Product lookup currently depends on normal database/API use rather than conversational
  search.
- There is no tracking history, payment status, invoice content, cancellation process,
  refund process, return process, or support-ticket model.
- The dashboard and API currently run as separate development processes.
- Authentication is not implemented; the customer selector is for fictional demo data.

## Recommended next milestone

Create a small, read-only tool layer for a future language model:

1. `list_orders` — list the selected customer's recent orders.
2. `get_order_details` — retrieve one order and its complete details.
3. `find_orders_by_product` — resolve phrases such as "headphones" or "jacket" to the
   selected customer's orders.

The application—not the model—should supply the selected customer ID. The tools should
return structured data, remain unable to modify the database, and be fully testable without
calling a language model.

## Later roadmap

After the read-only tools:

1. Select a language-model provider and implement a tool-calling loop.
2. Add explicit conversation state for the active customer and order.
3. Add a chat panel to the existing dashboard.
4. Test natural-language variations and read-only portions of the sample conversations.
5. Define completion criteria for the first read-only version.
6. Only then expand the data model and tools for split shipments, cancellations, refunds,
   returns, address changes, invoices, and support tickets.
