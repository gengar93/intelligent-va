# Mockup Brief — Order Support Console redesign (POC)

You are producing ONE self-contained HTML mockup file that presents a polished redesign
of an existing customer-support web app. The current app "looks very AI-generated" and
must be replaced with a distinctive, hand-crafted, premium look. This is a visual POC —
static/lightly-interactive HTML+CSS(+tiny vanilla JS), no build step, no frameworks.

## The product
A support console used by a support agent (and demoable to an audience). A customer is
selected at the top (this stands in for "logged in as this customer" — only their data shows).
Three areas exist today and must all appear in your mockup:
1. **Orders / Overview** — the selected customer's order history + a selected order's details.
2. **Tickets** — open invoice-generation tickets, each with a "Generate Invoice" button.
3. **Assistant** — a chat interface where the user asks natural-language order questions.

## NEW features to design (all required in the mockup)
- **Order cards in chat**: when the assistant references an order, render it as a rich
  order CARD inline in the conversation (status, items, total, delivery, invoice state,
  quick actions) instead of plain text.
- **Suggested follow-ups**: after an assistant reply, show 3–4 tappable follow-up
  suggestion chips (e.g. "Where is my order?", "Email me the invoice", "Change delivery address").
- **Model thinking / reasoning view**: a screen or panel that reveals the assistant's
  reasoning + the tools it called, for an audience. Show a step timeline: reasoning text,
  tool calls with arguments, tool results, then the final answer. Tools available:
  `list_orders`, `get_order_details(order_id)`, `get_recent_product_candidates(lookback_days)`,
  `get_invoice(order_id)`, `request_invoice(order_id)`.
- A couple of tasteful, low-complexity enhancements of your own are welcome (e.g. an order
  status stepper, invoice-ready toast, empty states, keyboard hint) — keep them subtle.

## Real sample data to use (be consistent — do not invent different names)
Customers (switcher): CUS-001 Aarav Sharma · CUS-002 Meera Iyer · CUS-003 Kabir Khan.
Currency INR, format like ₹7,498.00. Region: India. Today = 14 Aug 2026.

Aarav Sharma (CUS-001):
- ORD-1042 — Shipped — placed 4 Aug 2026 — est. delivery 11 Aug 2026 —
  1× NoiseBeat H100 Headphones (SKU NB-H100-BLK) ₹7,498.00 — total ₹7,498.00 —
  Visa ending 1842 — 22 Lakeview Apartments, Koramangala, Bengaluru 560034 — invoice: Available.
- ORD-1038 — Cancelled — placed 28 Jul 2026 — 1× BrewPro Coffee Maker ₹4,299.00 —
  total ₹4,299.00 — Visa ending 1842 — invoice: Not requested.

Meera Iyer (CUS-002):
- ORD-1087 — Processing — placed 7 Aug 2026 — est. delivery 12 Aug 2026 —
  1× UrbanTrail Backpack ₹2,499.00 + 1× SteelSip Bottle ₹899.00 — total ₹3,398.00 —
  UPI account — 8 Palm Grove, Adyar, Chennai 600020 — invoice: Queued (open ticket TKT-7002).
- ORD-1095 — Delivered 8 Aug 2026 — 1× HomeChef Mixer ₹5,199.00 — total ₹5,199.00 —
  UPI — invoice: Available.

Kabir Khan (CUS-003):
- ORD-1064 — Delivered 3 Aug 2026 — 2× NorthPeak Rain Jacket ₹3,199.00 —
  total ₹6,398.00 — Mastercard ending 7710 — 51 Crescent Residency, Bandra West, Mumbai 400050 —
  invoice: Available.

Open tickets (Tickets page): TKT-7002 — Invoice for ORD-1087 — Queued — requested 8 Aug 2026 —
2 items — order total ₹3,398.00. (Show one or two tickets; button label "Generate Invoice".)

Example chat to render in the Assistant view (Meera, CUS-002):
- User: "Where is my backpack order and can I get an invoice for it?"
- Assistant thinks, calls list_orders → get_order_details(ORD-1087) → get_invoice(ORD-1087) →
  request_invoice(ORD-1087), then replies with an ORDER CARD for ORD-1087 and a short message
  ("Your UrbanTrail Backpack order is being processed, arriving ~12 Aug. I've queued your
  invoice — ticket TKT-7002."). Then suggested follow-ups.

## Hard requirements
- Single self-contained `.html` file. All CSS in a `<style>` tag. Any JS inline and minimal.
- No external JS/CSS libraries. Google Fonts `<link>` is allowed for typography polish.
- Must NOT look like generic AI/Bootstrap/Tailwind-default output: no purple-blue gradient
  hero, no default card-with-heavy-shadow-everywhere, no emoji-as-icons soup. Commit to a
  real visual identity: deliberate type scale, restrained palette, real spacing rhythm,
  inline SVG icons (simple, consistent stroke), meaningful use of one accent.
- Responsive enough to look good at ~1280px; degrade gracefully narrower.
- Support light theme at minimum; dark is a bonus if it fits the direction.
- Include all key screens in ONE page. Use a top nav to switch between Orders / Tickets /
  Assistant, plus the customer switcher. Simple JS tab switching is fine. The "thinking"
  view can be a slide-over panel or an inline expandable "Show reasoning" section on the
  assistant message — your call, make it feel premium.
- Polish the details: focus states, hover states, status colors that mean something,
  tabular numbers for money, real empty/loading treatment somewhere.

Deliver only the HTML file at the path you are told to write to. Make it genuinely
portfolio-quality and distinctive.
