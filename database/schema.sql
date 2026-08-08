PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE addresses (
    address_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    label TEXT NOT NULL,
    recipient_name TEXT NOT NULL,
    line_1 TEXT NOT NULL,
    line_2 TEXT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    country_code TEXT NOT NULL DEFAULT 'IN',
    UNIQUE (customer_id, label)
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT
);

CREATE TABLE product_attributes (
    product_id TEXT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    attribute_name TEXT NOT NULL,
    attribute_value TEXT NOT NULL,
    PRIMARY KEY (product_id, attribute_name)
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    status TEXT NOT NULL CHECK (status IN (
        'placed', 'processing', 'partially_shipped', 'shipped',
        'out_for_delivery', 'delivered', 'cancelled'
    )),
    placed_at TEXT NOT NULL,
    currency TEXT NOT NULL CHECK (length(currency) = 3),
    subtotal_minor INTEGER NOT NULL CHECK (subtotal_minor >= 0),
    shipping_minor INTEGER NOT NULL DEFAULT 0 CHECK (shipping_minor >= 0),
    tax_minor INTEGER NOT NULL DEFAULT 0 CHECK (tax_minor >= 0),
    discount_minor INTEGER NOT NULL DEFAULT 0 CHECK (discount_minor >= 0),
    total_minor INTEGER NOT NULL CHECK (total_minor >= 0),
    delivery_address_id TEXT NOT NULL REFERENCES addresses(address_id),
    CHECK (total_minor = subtotal_minor + shipping_minor + tax_minor - discount_minor)
);

CREATE TABLE order_items (
    order_item_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_minor INTEGER NOT NULL CHECK (unit_price_minor >= 0),
    line_total_minor INTEGER NOT NULL CHECK (line_total_minor = quantity * unit_price_minor)
);

-- These are snapshots of the selected variant at purchase time. Product facts can
-- change later without rewriting the historical order.
CREATE TABLE order_item_attributes (
    order_item_id TEXT NOT NULL REFERENCES order_items(order_item_id) ON DELETE CASCADE,
    attribute_name TEXT NOT NULL,
    attribute_value TEXT NOT NULL,
    PRIMARY KEY (order_item_id, attribute_name)
);

CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    method_type TEXT NOT NULL CHECK (method_type IN ('card', 'upi', 'wallet', 'cod')),
    provider TEXT NOT NULL,
    display_reference TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
    currency TEXT NOT NULL CHECK (length(currency) = 3),
    status TEXT NOT NULL CHECK (status IN ('pending', 'authorized', 'captured', 'failed', 'refunded')),
    paid_at TEXT
);

CREATE TABLE shipments (
    shipment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN (
        'preparing', 'shipped', 'in_transit', 'out_for_delivery', 'delivered', 'exception'
    )),
    carrier TEXT,
    tracking_number TEXT UNIQUE,
    delivery_address_id TEXT NOT NULL REFERENCES addresses(address_id),
    estimated_delivery_start TEXT,
    estimated_delivery_end TEXT,
    shipped_at TEXT,
    delivered_at TEXT,
    delivered_to TEXT,
    CHECK (tracking_number IS NULL OR carrier IS NOT NULL)
);

CREATE TABLE shipment_items (
    shipment_id TEXT NOT NULL REFERENCES shipments(shipment_id) ON DELETE CASCADE,
    order_item_id TEXT NOT NULL REFERENCES order_items(order_item_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (shipment_id, order_item_id)
);

CREATE TABLE shipment_events (
    shipment_event_id INTEGER PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(shipment_id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT,
    occurred_at TEXT NOT NULL
);

CREATE TABLE cancellations (
    cancellation_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    status TEXT NOT NULL CHECK (status IN ('requested', 'awaiting_approval', 'approved', 'rejected', 'completed')),
    requested_at TEXT NOT NULL,
    resolved_at TEXT,
    reason TEXT,
    expected_refund_minor INTEGER NOT NULL DEFAULT 0 CHECK (expected_refund_minor >= 0)
);

CREATE TABLE cancellation_items (
    cancellation_id TEXT NOT NULL REFERENCES cancellations(cancellation_id) ON DELETE CASCADE,
    order_item_id TEXT NOT NULL REFERENCES order_items(order_item_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (cancellation_id, order_item_id)
);

CREATE TABLE refunds (
    refund_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    cancellation_id TEXT REFERENCES cancellations(cancellation_id),
    payment_id TEXT NOT NULL REFERENCES payments(payment_id),
    status TEXT NOT NULL CHECK (status IN ('pending', 'initiated', 'completed', 'failed')),
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    currency TEXT NOT NULL CHECK (length(currency) = 3),
    initiated_at TEXT,
    expected_by TEXT,
    completed_at TEXT
);

CREATE TABLE returns (
    return_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    status TEXT NOT NULL CHECK (status IN ('requested', 'booked', 'picked_up', 'inspecting', 'approved', 'rejected', 'completed')),
    resolution TEXT NOT NULL CHECK (resolution IN ('refund', 'exchange')),
    requested_at TEXT NOT NULL,
    pickup_at TEXT,
    expected_refund_minor INTEGER CHECK (expected_refund_minor >= 0)
);

CREATE TABLE return_items (
    return_id TEXT NOT NULL REFERENCES returns(return_id) ON DELETE CASCADE,
    order_item_id TEXT NOT NULL REFERENCES order_items(order_item_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (return_id, order_item_id)
);

CREATE TABLE support_tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    order_id TEXT REFERENCES orders(order_id),
    type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('open', 'investigating', 'waiting_for_customer', 'resolved', 'closed')),
    priority TEXT NOT NULL CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    summary TEXT NOT NULL,
    preferred_resolution TEXT,
    created_at TEXT NOT NULL,
    expected_update_at TEXT
);

CREATE TABLE invoices (
    invoice_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL UNIQUE REFERENCES orders(order_id),
    invoice_number TEXT NOT NULL UNIQUE,
    issued_at TEXT NOT NULL
);

CREATE INDEX idx_orders_customer_placed ON orders(customer_id, placed_at DESC);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_shipments_order ON shipments(order_id);
CREATE INDEX idx_shipment_events_timeline ON shipment_events(shipment_id, occurred_at DESC);
CREATE INDEX idx_cancellations_order ON cancellations(order_id);
CREATE INDEX idx_refunds_order ON refunds(order_id);

CREATE VIEW order_summaries AS
SELECT
    o.order_id,
    o.customer_id,
    o.placed_at,
    o.status,
    o.currency,
    o.total_minor,
    COUNT(DISTINCT oi.order_item_id) AS distinct_item_count,
    COALESCE(SUM(oi.quantity), 0) AS total_quantity
FROM orders AS o
LEFT JOIN order_items AS oi ON oi.order_id = o.order_id
GROUP BY o.order_id;
