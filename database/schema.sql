PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    image_url TEXT
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    status TEXT NOT NULL CHECK (
        status IN ('processing', 'shipped', 'delivered', 'cancelled')
    ),
    placed_at TEXT NOT NULL,
    estimated_delivery_date TEXT,
    delivered_at TEXT,
    currency TEXT NOT NULL CHECK (length(currency) = 3),
    delivery_address TEXT NOT NULL,
    payment_method_display TEXT NOT NULL,
    CHECK (status != 'delivered' OR delivered_at IS NOT NULL)
);

CREATE TABLE order_items (
    order_item_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_minor INTEGER NOT NULL CHECK (unit_price_minor >= 0)
);

CREATE TABLE tickets (
    ticket_id TEXT PRIMARY KEY,
    ticket_type TEXT NOT NULL CHECK (
        ticket_type IN ('invoice_generation')
    ),
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    status TEXT NOT NULL CHECK (
        status IN ('queued', 'in_progress', 'completed', 'failed', 'cancelled')
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    failure_reason TEXT,
    CHECK (
        (status = 'completed' AND completed_at IS NOT NULL)
        OR (status != 'completed' AND completed_at IS NULL)
    ),
    CHECK (
        (status = 'failed' AND failure_reason IS NOT NULL)
        OR (status != 'failed' AND failure_reason IS NULL)
    )
);

CREATE TABLE ticket_status_history (
    ticket_status_history_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    from_status TEXT CHECK (
        from_status IS NULL
        OR from_status IN ('queued', 'in_progress', 'completed', 'failed', 'cancelled')
    ),
    to_status TEXT NOT NULL CHECK (
        to_status IN ('queued', 'in_progress', 'completed', 'failed', 'cancelled')
    ),
    changed_at TEXT NOT NULL,
    note TEXT
);

CREATE TABLE invoices (
    invoice_id TEXT PRIMARY KEY,
    invoice_number TEXT NOT NULL UNIQUE,
    order_id TEXT NOT NULL UNIQUE REFERENCES orders(order_id),
    generation_ticket_id TEXT NOT NULL UNIQUE REFERENCES tickets(ticket_id),
    issued_at TEXT NOT NULL,
    billing_name TEXT NOT NULL,
    billing_address TEXT NOT NULL,
    currency TEXT NOT NULL CHECK (length(currency) = 3),
    subtotal_minor INTEGER NOT NULL CHECK (subtotal_minor >= 0),
    tax_minor INTEGER NOT NULL CHECK (tax_minor >= 0),
    total_minor INTEGER NOT NULL CHECK (total_minor >= 0),
    document_url TEXT,
    CHECK (total_minor = subtotal_minor + tax_minor)
);

CREATE TABLE invoice_items (
    invoice_item_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    source_order_item_id TEXT REFERENCES order_items(order_item_id),
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_minor INTEGER NOT NULL CHECK (unit_price_minor >= 0),
    tax_minor INTEGER NOT NULL CHECK (tax_minor >= 0),
    line_total_minor INTEGER NOT NULL CHECK (line_total_minor >= 0),
    CHECK (line_total_minor = quantity * unit_price_minor + tax_minor)
);

CREATE INDEX idx_orders_customer_placed
ON orders(customer_id, placed_at DESC);

CREATE INDEX idx_order_items_order
ON order_items(order_id);

CREATE INDEX idx_tickets_order_created
ON tickets(order_id, created_at DESC);

CREATE UNIQUE INDEX idx_tickets_one_active_invoice_request_per_order
ON tickets(order_id)
WHERE ticket_type = 'invoice_generation'
  AND status IN ('queued', 'in_progress');

CREATE INDEX idx_ticket_status_history_ticket_changed
ON ticket_status_history(ticket_id, changed_at);

CREATE INDEX idx_invoice_items_invoice
ON invoice_items(invoice_id);

CREATE TRIGGER validate_invoice_generation_ticket
BEFORE INSERT ON invoices
BEGIN
    SELECT CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM tickets
            WHERE ticket_id = NEW.generation_ticket_id
              AND order_id = NEW.order_id
              AND ticket_type = 'invoice_generation'
              AND status = 'completed'
        )
        THEN RAISE(ABORT, 'invoice requires a completed generation ticket for its order')
    END;
END;
