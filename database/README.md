# Order support database

This directory is the first incremental slice of the order-support application: a
normalized SQLite schema and curated fictional data. It does not connect to the old
JSON repository or chatbot yet.

## Reset the local database

```bash
python3 scripts/reset_database.py
```

This creates `data/order_support.db`. The database is generated and should not be
committed; `schema.sql` and `seed.sql` are the source of truth.

## Design choices

- Money is stored as integer minor units (`749800` means ₹7,498.00), avoiding
  floating-point rounding.
- Dates and timestamps use ISO 8601 text with an explicit offset.
- Product attributes describe generally true product facts. Order-item attributes
  snapshot the chosen variant (for example, size L and navy) at purchase time.
- An order can have multiple shipments, and `shipment_items` says exactly which
  item and quantity belongs to each shipment.
- Order, shipment, cancellation, refund, and return states are separate. One state
  must not imply another.
- Customer ownership starts at `orders.customer_id`; future read tools must always
  include the authenticated customer ID in their queries.

## Seed scenarios

The sample records intentionally match the target conversations:

- `ORD-1042`: headphones currently in transit, with an invoice.
- `ORD-1038`: completed cancellation with a refund still in progress.
- `ORD-1087`: one item shipped and one cancellation awaiting seller approval.
- `ORD-1103`: split shipment using separate home and office addresses.
- `ORD-1095`: marked delivered to security, with an investigation ticket.
- `ORD-1064` and `ORD-1071`: ambiguous jacket lookup and a one-of-two-item return.

The next slice should add a read-only repository over this database, followed by
LLM-facing tools and only then a UI.
