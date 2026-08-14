PRAGMA foreign_keys = ON;

BEGIN;

INSERT INTO customers (customer_id, name, email) VALUES
    ('CUS-001', 'Aarav Sharma', 'aarav.sharma@example.test'),
    ('CUS-002', 'Meera Iyer', 'meera.iyer@example.test'),
    ('CUS-003', 'Kabir Khan', 'kabir.khan@example.test');

INSERT INTO products (product_id, sku, name, description, image_url) VALUES
    ('PROD-HEADPHONES', 'NB-H100-BLK', 'NoiseBeat H100 Headphones', 'Wireless over-ear headphones', '/products/headphones.svg'),
    ('PROD-COFFEE', 'BP-CM20-SLV', 'BrewPro Coffee Maker', '1.2 litre drip coffee maker', '/products/coffee-maker.svg'),
    ('PROD-BACKPACK', 'UT-BP45-GRN', 'UrbanTrail Backpack', '25 litre everyday backpack', '/products/backpack.svg'),
    ('PROD-BOTTLE', 'SS-B750-BLU', 'SteelSip Bottle', '750 ml insulated bottle', '/products/bottle.svg'),
    ('PROD-MIXER', 'HC-MIX-750', 'HomeChef Mixer', '750 watt mixer grinder', '/products/mixer.svg'),
    ('PROD-JACKET', 'NP-RJ-L-NVY', 'NorthPeak Rain Jacket', 'Waterproof hooded rain jacket', '/products/jacket.svg');

INSERT INTO orders (
    order_id,
    customer_id,
    status,
    placed_at,
    estimated_delivery_date,
    delivered_at,
    currency,
    delivery_address,
    payment_method_display
) VALUES
    (
        'ORD-1042',
        'CUS-001',
        'shipped',
        '2026-08-04T14:20:00+05:30',
        '2026-08-11',
        NULL,
        'INR',
        '22 Lakeview Apartments, Koramangala, Bengaluru 560034',
        'Visa ending in 1842'
    ),
    (
        'ORD-1038',
        'CUS-001',
        'cancelled',
        '2026-07-28T10:05:00+05:30',
        '2026-08-02',
        NULL,
        'INR',
        '22 Lakeview Apartments, Koramangala, Bengaluru 560034',
        'Visa ending in 1842'
    ),
    (
        'ORD-1087',
        'CUS-002',
        'processing',
        '2026-08-07T09:15:00+05:30',
        '2026-08-12',
        NULL,
        'INR',
        '8 Palm Grove, Adyar, Chennai 600020',
        'UPI account'
    ),
    (
        'ORD-1095',
        'CUS-002',
        'delivered',
        '2026-08-01T12:30:00+05:30',
        '2026-08-08',
        '2026-08-08T15:42:00+05:30',
        'INR',
        '8 Palm Grove, Adyar, Chennai 600020',
        'UPI account'
    ),
    (
        'ORD-1064',
        'CUS-003',
        'delivered',
        '2026-07-26T11:10:00+05:30',
        '2026-08-03',
        '2026-08-03T13:15:00+05:30',
        'INR',
        '51 Crescent Residency, Bandra West, Mumbai 400050',
        'Mastercard ending in 7710'
    );

INSERT INTO order_items (
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price_minor
) VALUES
    ('ITEM-1042-1', 'ORD-1042', 'PROD-HEADPHONES', 1, 749800),
    ('ITEM-1038-1', 'ORD-1038', 'PROD-COFFEE', 1, 429900),
    ('ITEM-1087-1', 'ORD-1087', 'PROD-BACKPACK', 1, 249900),
    ('ITEM-1087-2', 'ORD-1087', 'PROD-BOTTLE', 1, 89900),
    ('ITEM-1095-1', 'ORD-1095', 'PROD-MIXER', 1, 519900),
    ('ITEM-1064-1', 'ORD-1064', 'PROD-JACKET', 2, 319900);

INSERT INTO tickets (
    ticket_id,
    ticket_type,
    order_id,
    status,
    created_at,
    updated_at,
    completed_at,
    failure_reason
) VALUES
    (
        'TKT-7001',
        'invoice_generation',
        'ORD-1042',
        'completed',
        '2026-08-08T10:02:00+05:30',
        '2026-08-08T10:04:00+05:30',
        '2026-08-08T10:04:00+05:30',
        NULL
    ),
    (
        'TKT-7002',
        'invoice_generation',
        'ORD-1087',
        'in_progress',
        '2026-08-11T11:14:00+05:30',
        '2026-08-11T11:15:00+05:30',
        NULL,
        NULL
    ),
    (
        'TKT-7003',
        'invoice_generation',
        'ORD-1064',
        'failed',
        '2026-08-11T12:20:00+05:30',
        '2026-08-11T12:21:00+05:30',
        NULL,
        'Billing address could not be validated'
    );

INSERT INTO ticket_status_history (
    ticket_status_history_id,
    ticket_id,
    from_status,
    to_status,
    changed_at,
    note
) VALUES
    ('TSH-9001', 'TKT-7001', NULL, 'queued', '2026-08-08T10:02:00+05:30', 'Customer requested invoice'),
    ('TSH-9002', 'TKT-7001', 'queued', 'in_progress', '2026-08-08T10:03:00+05:30', 'Generator claimed ticket'),
    ('TSH-9003', 'TKT-7001', 'in_progress', 'completed', '2026-08-08T10:04:00+05:30', 'Invoice INV-2026-00481 issued'),
    ('TSH-9010', 'TKT-7002', NULL, 'queued', '2026-08-11T11:14:00+05:30', 'Customer requested invoice'),
    ('TSH-9011', 'TKT-7002', 'queued', 'in_progress', '2026-08-11T11:15:00+05:30', 'Generator claimed ticket'),
    ('TSH-9020', 'TKT-7003', NULL, 'queued', '2026-08-11T12:20:00+05:30', 'Customer requested invoice'),
    ('TSH-9021', 'TKT-7003', 'queued', 'in_progress', '2026-08-11T12:20:30+05:30', 'Generator claimed ticket'),
    ('TSH-9022', 'TKT-7003', 'in_progress', 'failed', '2026-08-11T12:21:00+05:30', 'Billing address could not be validated');

INSERT INTO invoices (
    invoice_id,
    invoice_number,
    order_id,
    generation_ticket_id,
    issued_at,
    billing_name,
    billing_address,
    currency,
    subtotal_minor,
    tax_minor,
    total_minor,
    document_url
) VALUES (
    'INV-481',
    'INV-2026-00481',
    'ORD-1042',
    'TKT-7001',
    '2026-08-08T10:04:00+05:30',
    'Aarav Sharma',
    '22 Lakeview Apartments, Koramangala, Bengaluru 560034',
    'INR',
    749800,
    0,
    749800,
    '/mock-invoices/INV-2026-00481.pdf'
);

INSERT INTO invoice_items (
    invoice_item_id,
    invoice_id,
    source_order_item_id,
    description,
    quantity,
    unit_price_minor,
    tax_minor,
    line_total_minor
) VALUES (
    'INI-481-1',
    'INV-481',
    'ITEM-1042-1',
    'NoiseBeat H100 Headphones',
    1,
    749800,
    0,
    749800
);

COMMIT;
