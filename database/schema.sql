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
    description TEXT
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

CREATE INDEX idx_orders_customer_placed
ON orders(customer_id, placed_at DESC);

CREATE INDEX idx_order_items_order
ON order_items(order_id);
