# Project Journal

Last updated: 13 August 2026

## Goal

Build an order-support chatbot incrementally. A customer can ask about orders and invoice
status, and can request invoice generation. The conversations in `sample_conversations/`
describe the longer-term experience, including actions such as cancellations, returns,
address changes, and support tickets.

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
FastAPI API
      |
      v
Python repository
      |
      v
Local SQLite database

Customer-scoped chatbot tools
      |
      +-----> Python repository

Conversation loop
      |-----> OpenRouter model
      |
      +-----> Customer-scoped chatbot tools
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

### Invoice generation data model

Invoice requests are represented as generic `tickets` whose initial supported type is
`invoice_generation`. The current status is stored on the ticket for efficient reads, while
`ticket_status_history` records every transition for auditability. A partial unique index
prevents more than one queued or in-progress invoice request for the same order.

An `invoice` is created only after generation succeeds. It has a one-to-one relationship
with an order for this version and links back to the ticket that generated it. Billing
identity, address, totals, and `invoice_items` are stored snapshots, so later changes to
customer, product, or order data do not change what repository reads return. The current
`document_url` is deliberately a mock path; actual PDF generation is outside this milestone.

### Technology

- SQLite for the local database because it requires no database server.
- Python 3.12 managed with `uv`.
- FastAPI for the HTTP API and chat boundary.
- One narrowly scoped SQLite write transaction for idempotent invoice requests; ordinary
  repository queries still open the database in read-only mode.
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

### 12. Streamed assistant responses

Extended the existing NDJSON chat stream so model-generated text is sent to the browser as
it arrives. The OpenRouter adapter now reassembles streamed text and fragmented tool calls
into the complete assistant message required for conversation history. The API emits text
deltas before its authoritative result event, and the dashboard creates and updates one
assistant message incrementally. Failed requests remove any partial response so the user can
retry cleanly.

The model, conversation, and API tests cover text deltas, fragmented tool-call arguments,
and the browser-facing event sequence. All 45 Python tests pass. Frontend linting and the
TypeScript production build also pass.

### 13. Deterministic assistant evaluation baseline

Added a deterministic evaluation layer before introducing subjective model judging. Five
scenarios derived from the read-only portions of the target conversations cover product
resolution, cancelled and latest orders, a follow-up that relies on conversation history,
and refusal of an unsupported delivery change. Exact checks enforce required tool sequences
and answer facts, the read-only tool allowlist, absence of customer IDs in tool arguments,
and customer isolation across tool arguments, tool results, and answer order IDs. The runner
reports structured JSON, includes answers for failure diagnosis, supports filtering by
scenario name, and records the configured model.

One live baseline run passed the five scenarios and six evaluated turns. Tightening the
refusal check initially exposed an evaluator false negative for the phrase “not able”; after
adding that legitimate alternative and a regression test, a fresh focused live run passed.
This is a one-run baseline, not yet evidence of consistency across nondeterministic model
runs. All 54 Python tests and whitespace checks pass.

### 14. Invoice generation data model

Added ticket lifecycle, ticket status history, invoice, and invoice-item tables. Seed data
covers completed, in-progress, and failed generation cases. The completed example exposes a
mock document URL. Customer-scoped repository reads return either an issued invoice with its
snapshot items or the latest invoice-generation ticket for an order.

Database constraints reject duplicate active requests, unbalanced invoice totals, invalid
statuses, and invalid monetary or quantity values. An invoice also requires a completed
generation ticket for the same order. Actual ticket creation, state-changing application
services, API/tool exposure, and PDF generation remain future work.

### 15. Invoice chatbot tools

Added `get_invoice`, which returns a single current state spanning invoice availability and
the latest generation ticket, and `request_invoice`, which creates a queued generation
ticket. Invoice status is always refreshed from the database instead of being inferred from
conversation history. Available invoices return their mock document URL.

Request creation uses a customer-scoped `BEGIN IMMEDIATE` transaction. It returns an
existing invoice or active ticket instead of creating another one, including when two
requests arrive concurrently. Failed and cancelled tickets remain preserved and a later
request creates a new ticket. Each new ticket also receives its initial status-history row.
The deterministic evaluator permits this single supported write tool while continuing to
reject unrelated actions and cross-customer order access.

### 16. Cancelled-order invoice eligibility

New invoice requests are rejected for cancelled orders when no active request exists. The
tool returns `not_eligible` with reason `order_cancelled`, allowing the assistant to explain
the outcome without inventing payment or tax rules. The eligibility decision happens inside
the same write transaction as request creation.

An invoice that was generated before cancellation remains available, and a queued or
in-progress request continues to report its normal status. Failed ticket history is
preserved, but a cancelled order cannot create a retry ticket.

### 17. Ticket management and mock invoice completion

Added a customer-scoped Tickets tab that lists queued and in-progress invoice-generation
tickets. An operator can complete one with `Generate Invoice`; the UI shows success, removes
the ticket from the open queue, and refreshes the Orders data in place. The Orders list and
selected-order details now show the current invoice status, including `Available` immediately
after generation without a browser-page reload. Successful assistant turns also refresh the
workspace, so a newly requested invoice appears in Tickets without reloading.

The new completion endpoint runs under `BEGIN IMMEDIATE`. It snapshots the customer name,
delivery address, currency, order items, and totals into the invoice tables, uses zero added
tax to match the existing mock invoice convention, records any queued-to-in-progress
transition, completes the ticket, and appends its completion history. All writes commit or
roll back together. Ticket lookup and completion remain customer-scoped, and closed tickets
cannot be processed again. Generated documents remain symbolic mock URLs; no PDF bytes are
created yet.

Verification covered repository and API behavior, customer isolation, both open ticket
states, invoice snapshots, history transitions, and automatic endpoint refresh. A live UI
check confirmed the ticket count changed from one to zero and the order status changed to
`Available` without a page reload; the demo database was reset afterward.

### 18. Clean database on each demo run

Added `scripts.run_api` as the normal local API launcher. It rebuilds the default SQLite
database from the checked-in schema and seed data once before starting Uvicorn with hot
reload. The reset deliberately happens in the launcher rather than during FastAPI import,
so application imports, tests, and hot-reload child processes do not unexpectedly erase
state. Starting Uvicorn directly remains an intentional non-resetting escape hatch.

Launcher tests mutate a temporary database, confirm seeded invoice data is restored before
the server runner is called, and verify the expected local host, port, app target, and reload
configuration.

### 19. "Atelier" editorial redesign

Replaced the previous console interface with a hand-crafted editorial design (Fraunces and
Inter typography, a warm paper and terracotta palette, hairline borders). Added product
images to the data model — `products.image_url` flows through the repository and API and is
rendered on orders and chat cards, with a neutral placeholder when an image is missing.
Added an order status stepper and a Tickets history view (completed, failed, and cancelled)
backed by a new `GET /api/customers/{id}/tickets/closed` endpoint, which subsumes the
previously recommended ticket-history milestone. Three self-contained design mockups and the
stream contract that guided the build are kept under `mockups/`.

### 20. Rich agent stream and modern agentic chat

Extended `/api/chat/stream` to a v2 protocol: typed `tool_call` and `tool_result` events
carrying real arguments, returned JSON, and measured elapsed time; reasoning-versus-answer
segment classification; a prompted one-sentence narration before each tool call; and a
trailing machine-read metadata block that is suppressed from the visible stream and parsed
into database-hydrated order cards and follow-up suggestions, with rule-based fallbacks when
the model omits it. Card contents always come from the database, never from model text, so a
card cannot show a wrong price. The assistant tab was reworked into a full-screen, single
reading column in the style of modern coding assistants: tool calls stream inline as compact
expandable rows, narration and answer render Markdown live as tokens arrive, and the whole
trace collapses into an expandable element once the final answer is ready.

### 21. Chat latency and reliability hardening

Capped each upstream model request at 30 seconds, replacing the SDK's 600-second default so a
slow or overloaded OpenRouter provider fails fast. Narrowed the conversation lock so it is
held only while reading session history and writing the result, never across the model
stream; an aborted request — for example from switching customers mid-response, which the
dashboard allows — can no longer hold the lock and delay the customer's next message. Longer
turns (roughly 10–15 seconds) remain dominated by sequential multi-round tool calling and by
provider routing variance for the configured flash model, neither of which is a defect.

## Current functionality

- Rebuild a consistent local database from checked-in SQL.
- Reset the demo database automatically whenever the normal local API launcher starts.
- List fictional customers.
- Retrieve only the orders belonging to one customer.
- Retrieve customer-scoped invoice snapshots and latest invoice ticket status.
- Show order status, dates, address, payment method, items, quantities, prices, and totals.
- Switch between customers and orders in the dashboard.
- Execute five customer-scoped support tools without a language model.
- Fetch fresh invoice availability and ticket status for an order.
- Idempotently create an invoice-generation request.
- List customer-scoped open invoice tickets and atomically generate a mock invoice.
- Produce lean recent-product candidates using an optional rolling date window.
- Run a bounded model/tool loop while preserving the complete internal message history.
- Continue follow-up conversations using earlier hidden tool results.
- Chat with the assistant from the selected customer's dashboard.
- Start a fresh conversation explicitly or by changing customers.
- Switch between order, ticket, and assistant tabs without losing the current chat.
- See invoice status on each order and refresh it immediately after ticket completion.
- See live, tool-backed activity while the assistant works.
- Inspect the assistant's streamed tool calls, arguments, and returned results inline, then
  collapse the whole reasoning trace once the final answer is ready.
- Read streamed answers and narration as live Markdown while tokens arrive.
- Receive database-backed order cards and suggested follow-up questions after a reply.
- Render product images on orders and chat cards, with a placeholder when one is missing.
- Review completed, failed, and cancelled invoice tickets in a Tickets history view.
- Cap each upstream model request at 30 seconds.
- Read model-generated answers as they stream into the conversation.
- Run deterministic, customer-isolated evaluations against the configured model.
- Follow the operating system's light or dark appearance automatically.
- Render safe emphasis, lists, and inline code in assistant messages.
- Reject invalid database quantities and prices.
- Return `404` for an unknown customer.

The Python database, repository, API, tool, configuration, model-adapter, and conversation
suite currently contains 93 passing tests. The frontend passes linting and a TypeScript
production build.

## Running the project

Install the Python environment:

```bash
uv sync
```

Start the API in one terminal. This command resets the demo database before every run:

```bash
uv run python -m scripts.run_api
```

Use `uv run python -m scripts.reset_database` to reset without starting the API. Directly
starting `uvicorn order_support.api:app` intentionally preserves the current database.

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

Run the live deterministic evaluation catalog, or one matching scenario:

```bash
uv run python -m scripts.run_evaluations
uv run python -m scripts.run_evaluations --scenario "latest order"
```

## Current limitations

- Complete history is intentionally unbounded for the first version; long conversations will
  eventually require summarization or compaction.
- Conversation sessions are held only in backend memory and are lost when the API restarts.
- In-memory conversation sessions do not yet expire automatically.
- Orders have one delivery schedule; split shipments are unsupported.
- A customer change must begin a fresh internal history so previous customer tool results do
  not remain in model context.
- Invoice generation creates a database snapshot and mock URL, but does not create real PDF
  content or perform billing/tax integration.
- There is no tracking history, payment status, cancellation process, refund process, or
  return process.
- Some chat turns take roughly 10–15 seconds; this is sequential multi-round tool calling
  plus OpenRouter provider routing variance, not yet addressed by provider pinning.
- The dashboard and API currently run as separate development processes.
- Tool selection and execution still happen before the useful final answer begins streaming.
- Deterministic answer checks currently use explicit accepted phrases and can require careful
  updates when valid wording changes.
- The live evaluation baseline has only one run per scenario; repeated-run consistency,
  broader paraphrase coverage, human review, and a calibrated LLM judge are not implemented.
- Authentication is not implemented; the customer selector is for fictional demo data.

## Recommended next milestone

Reduce chat tail latency by pinning OpenRouter provider routing and/or selecting a faster
tool-capable model, since multi-round tool turns currently take 10–15 seconds. Then decide
whether the next invoice milestone should generate downloadable PDF content or integrate with
an external billing system.

## Later roadmap

1. Add paraphrases and repeated-run reporting to the deterministic evaluation catalog.
2. Define completion criteria and calibrate an LLM judge against human-reviewed examples.
3. Expand the support workflow to split shipments, cancellations, refunds, returns, and
   address changes after choosing the next invoice-document milestone.
