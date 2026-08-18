# Project Journal

Last updated: 18 August 2026

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

### 22. Downloadable invoice PDF

Invoice generation now yields a real, downloadable PDF rather than a placeholder URL. A new
customer-scoped route, `GET /api/customers/{id}/orders/{order_id}/invoice.pdf`, renders the
stored invoice snapshot on demand — no file is persisted — and returns it as an
`application/pdf` attachment; a foreign customer or an order without an invoice returns 404.
The PDF (`order_support/invoice_pdf.py`, rendered with `fpdf2`) uses the warm "Atelier" style:
bundled IBM Plex fonts (SIL OFL, under `order_support/fonts/`) so the rupee glyph and
appearance are identical on any host, an accent masthead, a line-item card, and totals. Long
item names truncate with an ellipsis so a row can never overflow. `document_url` now points at
this route (in both the seed data and freshly generated invoices), so the assistant's own link
resolves. The Orders detail and the in-chat order card show a Download invoice action whenever
an invoice is available.

### 23. Mobile navigation drawer

Replaced the crowded mobile title-bar controls with an accessible side drawer at widths up
to 620px. The compact title bar now keeps the menu trigger, console title, and contextual
New conversation action; Orders, Tickets, and Assistant navigation move into the drawer.
The drawer footer contains the appearance control and a full customer switcher with names,
IDs, and email addresses. Selecting a section or customer closes the drawer, and the drawer
also supports backdrop dismissal, Escape, contained keyboard focus, focus restoration, and
automatic cleanup when resizing to desktop. The mobile title is centered against the viewport,
the drawer header omits redundant section copy, and its close button aligns vertically with
the title-bar actions. Active navigation uses the same tinted color treatment as the rest of
the app without an additional indicator. The existing desktop navigation is unchanged.

Verification: frontend lint and production build pass. Browser checks at 320px and 375px
confirmed a non-overflowing title bar, drawer navigation, theme and customer controls,
successful customer switching, the Assistant-only New conversation action, and Escape
dismissal. A 1280px check confirmed the desktop tabs, theme control, and customer switcher
remain visible while the mobile trigger remains hidden. No browser console warnings or errors
were reported. Follow-up browser measurement confirmed the mobile title lands exactly at the
viewport midpoint and the drawer close and New conversation buttons share the same top offset.
There is not yet an automated frontend interaction-test suite, so these drawer
behaviors are currently covered by lint, TypeScript compilation, and browser verification.

### 24. Live demo database reset

Added a guarded `POST /api/demo/reset` endpoint and matching dashboard controls so a presenter
can restore the original seeded records without restarting the API or frontend. The desktop
header uses a compact reset icon, while the mobile drawer exposes a labeled Reset demo data
action. After confirmation, the frontend aborts active chat work, resets local conversation and
workspace state, reloads the first customer, returns to Orders, and shows a success toast. The
backend atomically replaces the SQLite file and clears in-memory conversations; a generation
counter prevents a streamed turn that began before the reset from restoring stale history.

The API now creates a seeded database only when its configured file is missing, so the custom
`scripts.run_api` launcher and its tests were removed. Normal development startup is the direct
Uvicorn command and no longer destroys demo changes on every server restart. The standalone
`scripts.reset_database` command remains available for terminal use.

Verification: all 96 Python tests pass, including new coverage for missing-database startup,
seed restoration, and conversation invalidation. Frontend lint and production build pass. A
live browser flow generated an invoice, reset the demo, confirmed the original open ticket was
restored, and verified both desktop and mobile reset controls with no console errors. The reset
endpoint is intentionally unauthenticated for this local POC and must not be exposed publicly
without access control.

### 25. Config-driven OpenRouter model selection — backend

Moved model choice out of `.env` and into the checked-in `config/models.toml` catalog. The
catalog contains Gemini 3.7 Flash as the default plus GLM 5.2, Qwen 3.7 Flash, GPT-5.6 Luna,
and GPT OSS 120B, all using their OpenRouter Nitro variants. Environment configuration now
contains only the OpenRouter API key and optional base URL.

Added `GET /api/model-options`, which exposes stable IDs and display labels without leaking
upstream slugs or provider-routing details. Both chat endpoints accept optional `model_id` and
`route_id`; omission remains compatible with the current frontend by selecting catalog
defaults. Conversations are bound to their starting model and route so hidden reasoning and
tool history cannot accidentally cross model configurations. The same selection is available
to the evaluation runner through `--model` and `--route`.

Each catalog route may contain a validated OpenRouter `provider` table, including `only`,
`order`, fallback, throughput, latency, quantization, and privacy controls. The client passes
that table through only on the selected route. It no longer universally disables parallel
tool calls because not every configured model advertises that parameter. Streaming now
reassembles and preserves OpenRouter reasoning fields for subsequent tool-call turns; these
fields remain internal and are not exposed as chain-of-thought in the public API.

Verification: all 104 Python tests pass. New tests cover the exact checked-in Nitro catalog,
invalid catalog/default/provider data, safe option exposure, request validation, conversation
binding, provider forwarding, and preservation of streamed reasoning details. Frontend model
selection is intentionally deferred to the next milestone.

### 26. Composer model selection — frontend

Moved New conversation out of the title bar and into a two-level assistant composer inspired
by the supplied Claude mobile reference while retaining the app's existing visual language.
The textarea occupies the upper row; the footer places New conversation at the left and the
model selector plus Send at the right. No microphone or inactive voice affordance was added.

The dashboard loads its catalog from `GET /api/model-options`, initializes the backend default,
and includes `model_id` and `route_id` in every streamed chat request. Provider-route selection
appears only when the selected model defines multiple routes, avoiding a redundant Nitro-only
control today. Changing either selection clears the transcript, starts a fresh conversation,
and confirms the change with a toast. New conversation and selection controls are disabled
while a response is streaming.

Verification: frontend lint and production build pass. Browser checks at 1280px, 375px, and
320px confirmed the responsive composer, selector options, centered mobile title, absence of
the old title-bar action, and no horizontal overflow. Model switching selected GLM 5.2 and
showed the fresh-conversation toast. The 375px dark-mode pass confirmed the new surface and
controls remain legible. No browser console errors were reported.

### 27. Assistant scope, suggestions, and order-card guardrails

Reworked the system prompt around a compact, explicit capability boundary. The assistant now
distinguishes supported order and invoice questions, order-related but unsupported actions,
mixed requests, and unrelated questions. It is instructed not to call tools or answer the
unrelated content for an off-topic request, and it must not imply that unsupported changes
such as cancellation, refund, rescheduling, address editing, or invoice emailing occurred.

Follow-up suggestions are now optional rather than forced: the model may return zero to three,
must ground each one in the supported capabilities and known order state, and must avoid both
unsupported actions and facts already answered. An explicit empty list remains empty, and
missing or malformed metadata no longer produces generic fallback suggestions.

Order cards are now reserved for explicit requests to show an order, a broad order summary or
receipt, and multi-order presentation or comparison. Focused answers about status, delivery
date, address, payment method, an item, price, total, or invoice should remain short and omit
the card. The backend no longer infers a card merely because `get_order_details` was used
internally; only valid model metadata can request one.

Set GPT-5.6 Luna as the checked-in default model for the demo. Added deterministic evaluation
coverage for declining an unrelated cooking question without tool calls and answering a
focused payment-method question, plus unit coverage for the capability policy, prompt-size
ceiling, empty metadata behavior, and the three-suggestion limit.

Verification: all 108 Python tests pass. A live OpenRouter evaluation was not run because it
would make billable external model calls; GPT-5.6 Luna should be the primary target for the
next live evaluation pass.

### 28. Clickable invoice links in assistant answers

Made the invoice response contract explicit: whenever `get_invoice` reports an available
document, the assistant must include `[Download invoice](document_url)` using the exact
database-backed URL returned by the tool. A raw path or a statement that the invoice is
available without the link is no longer considered sufficient.

Enabled links in final assistant Markdown while keeping the surface narrowly guarded. Only a
relative invoice-PDF path for the currently selected customer and a single safe order-ID path
segment becomes clickable; any other model-generated destination is rendered as plain text.
Invoice links use the existing accent palette and remain legible in light and dark themes.

Verification: all 108 Python tests pass, and frontend lint plus the TypeScript production build
pass. The prompt has assertions for the exact download-link contract. A live GPT-5.6 Luna test
with fictional order `ORD-1042` called `get_invoice`, returned no order card, and produced the
expected `[Download invoice](/api/customers/CUS-001/orders/ORD-1042/invoice.pdf)` answer.

### 29. US computer-parts demo dataset and Order VA branding

Reworked the fictional demo for a US computer-parts producer. The application and invoice
PDFs are branded as Order VA, monetary and date formatting use US conventions, every seeded
order and invoice uses USD, and the hard-coded invoice seller is the fictional Nova
Components, Inc. in Austin, Texas.

Expanded the seed data from three customers and five orders to five customers and 20 orders.
The customer list deliberately mixes one Indian-origin name with a diverse set of US names.
Each customer has four orders containing computer products such as monitors, keyboards,
headsets, webcams, docks, SSDs, microphones, and hubs. Added matching line-art SVG thumbnails
for the expanded catalog and rewrote the five target sample conversations so their products,
addresses, payment methods, dates, and dollar amounts remain consistent with the US demo.

The invoice scenarios are intentionally distributed across the 20 orders: four invoices are
available, four requests are queued or in progress, two requests have failed, and ten orders
have no invoice request. A database test protects this exact distribution.

Verification: all 109 Python tests pass. Frontend linting and the TypeScript production build
pass. The seeded database was rebuilt successfully. A generated invoice PDF was rendered to
an image and visually checked for Order VA branding, US seller identity, US address and date
formatting, dollar values, alignment, and legibility.

### 30. Ambiguous monitor invoice demo data

Added a second monitor product, the NovaView 24-inch FHD Monitor, alongside the existing
NovaView 27-inch 4K Monitor. Sofia Rodriguez now owns both models in separate recent orders:
`ORD-1130` has the 27-inch monitor and an available invoice, while `ORD-1132` has the 24-inch
monitor and no invoice request. This creates a deliberate product-resolution ambiguity for
demonstrating that Order VA can ask which monitor the customer means before handling an
invoice request.

The second model is a distinct row in the products table and reuses the established monitor
thumbnail. The overall invoice distribution remains unchanged. A database regression test
protects the two product names, order IDs, customer ownership, and differing invoice states.

Verification: all 110 Python tests pass. Frontend linting and the TypeScript production build
pass, and the seeded database rebuild succeeds.

## Current functionality

- Rebuild a consistent local database from checked-in SQL.
- Create the seeded database automatically when the API starts without one.
- Reset demo data and conversations from the running dashboard without restarting the app.
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
- Select a configured OpenRouter model and optional provider route per conversation, with a
  backward-compatible catalog default.
- Continue follow-up conversations using earlier hidden tool results.
- Chat with the assistant from the selected customer's dashboard.
- Start a fresh conversation explicitly or by changing customers.
- Choose the model from the assistant composer; models and conditional provider routes come
  from the backend catalog, and changing either begins a fresh conversation.
- Switch between order, ticket, and assistant tabs without losing the current chat.
- Use a compact, keyboard-accessible mobile drawer to navigate, change appearance, and switch
  customers without crowding the title bar.
- See invoice status on each order and refresh it immediately after ticket completion.
- See live, tool-backed activity while the assistant works.
- Inspect the assistant's streamed tool calls, arguments, and returned results inline, then
  collapse the whole reasoning trace once the final answer is ready.
- Read streamed answers and narration as live Markdown while tokens arrive.
- Receive database-backed order cards and suggested follow-up questions after a reply.
- Keep off-topic requests, unsupported actions, follow-up suggestions, and order-card display
  within the documented order-and-invoice support boundary.
- Render product images on orders and chat cards, with a placeholder when one is missing.
- Review completed, failed, and cancelled invoice tickets in a Tickets history view.
- Download a generated invoice as a styled PDF from the Orders detail or the in-chat card.
- Open a database-backed invoice download link directly from a focused assistant answer.
- Cap each upstream model request at 30 seconds.
- Read model-generated answers as they stream into the conversation.
- Run deterministic, customer-isolated evaluations against the configured model.
- Follow the operating system's light or dark appearance automatically.
- Render safe emphasis, lists, and inline code in assistant messages.
- Reject invalid database quantities and prices.
- Return `404` for an unknown customer.

The Python database, repository, API, tool, configuration, model-adapter, and conversation
suite currently contains 110 passing tests. The frontend passes linting and a TypeScript
production build.

## Running the project

Install the Python environment:

```bash
uv sync
```

Start the API in one terminal. It creates the seeded database if the file does not exist and
otherwise preserves the current demo state:

```bash
uv run uvicorn order_support.api:app --reload
```

Use the dashboard's Reset demo data action while the app is running, or run
`uv run python -m scripts.reset_database` to reset from a terminal.

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
uv run python -m scripts.run_evaluations --model gpt-5-6-luna --route nitro
```

## Current limitations

- Complete history is intentionally unbounded for the first version; long conversations will
  eventually require summarization or compaction.
- Conversation sessions are held only in backend memory and are lost when the API restarts.
- In-memory conversation sessions do not yet expire automatically.
- Orders have one delivery schedule; split shipments are unsupported.
- A customer change must begin a fresh internal history so previous customer tool results do
  not remain in model context.
- Invoice generation creates a database snapshot and a downloadable styled PDF, but does not
  perform billing/tax integration: tax is always zero and the seller entity on the PDF is a
  hard-coded placeholder.
- There is no tracking history, payment status, cancellation process, refund process, or
  return process.
- Some chat turns take roughly 10–15 seconds; this is sequential multi-round tool calling
  plus OpenRouter provider routing variance. The backend now supports provider-pinned routes,
  but the checked-in catalog currently defines only Nitro automatic routes.
- The checked-in catalog currently defines one Nitro automatic route for each model, so the
  conditional provider-route selector is not visible until another route is configured.
- The dashboard and API currently run as separate development processes.
- Tool selection and execution still happen before the useful final answer begins streaming.
- Deterministic answer checks currently use explicit accepted phrases and can require careful
  updates when valid wording changes.
- The live evaluation baseline has only one run per scenario; repeated-run consistency,
  broader paraphrase coverage, human review, and a calibrated LLM judge are not implemented.
- Scope and follow-up relevance still depend on model instruction-following. Follow-ups remain
  free-form text rather than backend-enforced intent identifiers, so live multi-run evaluation
  is still needed even though empty and missing metadata now fail safely.
- Authentication is not implemented; the customer selector and destructive demo-reset endpoint
  are only appropriate for local fictional demo data.

## Recommended next milestone

Run the expanded evaluation catalog repeatedly against GPT-5.6 Luna, including human review of
card display and follow-up relevance. If prompt-only follow-up controls remain inconsistent,
replace free-form suggestions with backend-rendered supported intent identifiers. Separately,
provider-pinned routes could reduce tail latency.

## Later roadmap

1. Add paraphrases and repeated-run reporting to the deterministic evaluation catalog.
2. Define completion criteria and calibrate an LLM judge against human-reviewed examples.
3. Expand the support workflow to split shipments, cancellations, refunds, returns, and
   address changes after choosing the next invoice-document milestone.
