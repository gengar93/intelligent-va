PRAGMA foreign_keys = ON;

BEGIN;

INSERT INTO customers (customer_id, name, email) VALUES
    ('CUS-001', 'Aarav Sharma', 'aarav.sharma@example.test'),
    ('CUS-002', 'Meera Iyer', 'meera.iyer@example.test'),
    ('CUS-003', 'Kabir Khan', 'kabir.khan@example.test');

INSERT INTO products (product_id, sku, name, description) VALUES
    ('PROD-HEADPHONES', 'NB-H100-BLK', 'NoiseBeat H100 Headphones', 'Wireless over-ear headphones'),
    ('PROD-COFFEE', 'BP-CM20-SLV', 'BrewPro Coffee Maker', '1.2 litre drip coffee maker'),
    ('PROD-BACKPACK', 'UT-BP45-GRN', 'UrbanTrail Backpack', '25 litre everyday backpack'),
    ('PROD-BOTTLE', 'SS-B750-BLU', 'SteelSip Bottle', '750 ml insulated bottle'),
    ('PROD-MIXER', 'HC-MIX-750', 'HomeChef Mixer', '750 watt mixer grinder'),
    ('PROD-JACKET', 'NP-RJ-L-NVY', 'NorthPeak Rain Jacket', 'Waterproof hooded rain jacket');

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

COMMIT;
