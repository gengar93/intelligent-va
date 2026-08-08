PRAGMA foreign_keys = ON;

BEGIN;

INSERT INTO customers (customer_id, full_name, email, created_at) VALUES
('CUS-001', 'Aarav Sharma', 'aarav.sharma@example.test', '2026-01-10T09:00:00+05:30'),
('CUS-002', 'Meera Iyer', 'meera.iyer@example.test', '2026-02-15T10:00:00+05:30'),
('CUS-003', 'Kabir Khan', 'kabir.khan@example.test', '2026-03-01T11:00:00+05:30'),
('CUS-004', 'Diya Patel', 'diya.patel@example.test', '2026-03-18T12:00:00+05:30'),
('CUS-005', 'Rohan Mehta', 'rohan.mehta@example.test', '2026-04-02T13:00:00+05:30');

INSERT INTO addresses (address_id, customer_id, label, recipient_name, line_1, line_2, city, state, postal_code) VALUES
('ADDR-001-HOME', 'CUS-001', 'home', 'Aarav Sharma', '22 Lakeview Apartments', 'Koramangala', 'Bengaluru', 'Karnataka', '560034'),
('ADDR-002-HOME', 'CUS-002', 'home', 'Meera Iyer', '8 Palm Grove', 'Adyar', 'Chennai', 'Tamil Nadu', '600020'),
('ADDR-003-HOME', 'CUS-003', 'home', 'Kabir Khan', '51 Crescent Residency', 'Bandra West', 'Mumbai', 'Maharashtra', '400050'),
('ADDR-003-OFFICE', 'CUS-003', 'office', 'Kabir Khan', '14 Park View Road', 'Indiranagar', 'Bengaluru', 'Karnataka', '560038'),
('ADDR-004-HOME', 'CUS-004', 'home', 'Diya Patel', '17 Riverfront Towers', 'Navrangpura', 'Ahmedabad', 'Gujarat', '380009'),
('ADDR-005-HOME', 'CUS-005', 'home', 'Rohan Mehta', '33 Green Park', 'Hauz Khas', 'New Delhi', 'Delhi', '110016');

INSERT INTO products (product_id, sku, name, category, description) VALUES
('PROD-HEADPHONES', 'NB-H100-BLK', 'NoiseBeat H100 Headphones', 'Audio', 'Wireless over-ear headphones'),
('PROD-COFFEE', 'BP-CM20-SLV', 'BrewPro Coffee Maker', 'Kitchen Appliances', '1.2 litre drip coffee maker'),
('PROD-BACKPACK', 'UT-BP45-GRN', 'UrbanTrail Backpack', 'Bags', '25 litre everyday backpack'),
('PROD-BOTTLE', 'SS-B750-BLU', 'SteelSip Bottle', 'Drinkware', '750 ml insulated bottle'),
('PROD-LAMP', 'RL-DESK-BLK', 'ReadLite Desk Lamp', 'Home Office', 'Five-level LED desk lamp'),
('PROD-NOTEBOOK', 'PN-A5-5PK', 'PaperNest A5 Notebook Set', 'Stationery', 'Set of five A5 notebooks'),
('PROD-MIXER', 'HC-MIX-750', 'HomeChef Mixer', 'Kitchen Appliances', '750 watt mixer grinder'),
('PROD-RAIN-JACKET', 'NP-RJ-L-NVY', 'NorthPeak Rain Jacket', 'Clothing', 'Waterproof hooded rain jacket'),
('PROD-CASUAL-JACKET', 'CC-CJ-M-BGE', 'CottonCloud Casual Jacket', 'Clothing', 'Lightweight cotton casual jacket');

INSERT INTO product_attributes (product_id, attribute_name, attribute_value) VALUES
('PROD-HEADPHONES', 'connectivity', 'Bluetooth 5.4'),
('PROD-HEADPHONES', 'warranty', '1 year'),
('PROD-COFFEE', 'capacity', '1.2 litres'),
('PROD-BACKPACK', 'capacity', '25 litres'),
('PROD-BOTTLE', 'capacity', '750 ml'),
('PROD-LAMP', 'brightness_levels', '5'),
('PROD-NOTEBOOK', 'pack_size', '5 notebooks'),
('PROD-MIXER', 'power', '750 watts'),
('PROD-RAIN-JACKET', 'care', 'Machine wash cold on a gentle cycle; close all zippers; do not tumble dry'),
('PROD-CASUAL-JACKET', 'care', 'Machine wash cold with similar colours');

INSERT INTO orders (order_id, customer_id, status, placed_at, currency, subtotal_minor, shipping_minor, tax_minor, discount_minor, total_minor, delivery_address_id) VALUES
('ORD-1042', 'CUS-001', 'shipped', '2026-08-04T14:20:00+05:30', 'INR', 749800, 0, 0, 0, 749800, 'ADDR-001-HOME'),
('ORD-1038', 'CUS-001', 'cancelled', '2026-07-28T10:05:00+05:30', 'INR', 429900, 0, 0, 0, 429900, 'ADDR-001-HOME'),
('ORD-1087', 'CUS-002', 'partially_shipped', '2026-08-07T09:15:00+05:30', 'INR', 329900, 9900, 0, 0, 339800, 'ADDR-002-HOME'),
('ORD-1103', 'CUS-003', 'partially_shipped', '2026-08-03T16:45:00+05:30', 'INR', 354700, 0, 0, 0, 354700, 'ADDR-003-HOME'),
('ORD-1095', 'CUS-004', 'delivered', '2026-08-01T12:30:00+05:30', 'INR', 519900, 0, 0, 0, 519900, 'ADDR-004-HOME'),
('ORD-1064', 'CUS-005', 'delivered', '2026-07-26T11:10:00+05:30', 'INR', 639800, 0, 0, 0, 639800, 'ADDR-005-HOME'),
('ORD-1071', 'CUS-005', 'delivered', '2026-07-22T15:25:00+05:30', 'INR', 249900, 0, 0, 0, 249900, 'ADDR-005-HOME');

INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price_minor, line_total_minor) VALUES
('ITEM-1042-1', 'ORD-1042', 'PROD-HEADPHONES', 1, 749800, 749800),
('ITEM-1038-1', 'ORD-1038', 'PROD-COFFEE', 1, 429900, 429900),
('ITEM-1087-1', 'ORD-1087', 'PROD-BACKPACK', 1, 240000, 240000),
('ITEM-1087-2', 'ORD-1087', 'PROD-BOTTLE', 1, 89900, 89900),
('ITEM-1103-1', 'ORD-1103', 'PROD-LAMP', 1, 189900, 189900),
('ITEM-1103-2', 'ORD-1103', 'PROD-NOTEBOOK', 1, 164800, 164800),
('ITEM-1095-1', 'ORD-1095', 'PROD-MIXER', 1, 519900, 519900),
('ITEM-1064-1', 'ORD-1064', 'PROD-RAIN-JACKET', 2, 319900, 639800),
('ITEM-1071-1', 'ORD-1071', 'PROD-CASUAL-JACKET', 1, 249900, 249900);

INSERT INTO order_item_attributes (order_item_id, attribute_name, attribute_value) VALUES
('ITEM-1042-1', 'color', 'Black'),
('ITEM-1038-1', 'color', 'Silver'),
('ITEM-1087-1', 'color', 'Forest Green'),
('ITEM-1087-2', 'color', 'Blue'),
('ITEM-1103-1', 'color', 'Black'),
('ITEM-1103-2', 'color', 'Earth tones'),
('ITEM-1064-1', 'color', 'Navy'),
('ITEM-1064-1', 'size', 'L'),
('ITEM-1071-1', 'color', 'Beige'),
('ITEM-1071-1', 'size', 'M');

INSERT INTO payments (payment_id, order_id, method_type, provider, display_reference, amount_minor, currency, status, paid_at) VALUES
('PAY-1042', 'ORD-1042', 'card', 'Visa', 'Visa ending in 1842', 749800, 'INR', 'captured', '2026-08-04T14:21:00+05:30'),
('PAY-1038', 'ORD-1038', 'card', 'Visa', 'Visa ending in 1842', 429900, 'INR', 'captured', '2026-07-28T10:06:00+05:30'),
('PAY-1087', 'ORD-1087', 'upi', 'UPI', 'UPI account', 339800, 'INR', 'captured', '2026-08-07T09:16:00+05:30'),
('PAY-1103', 'ORD-1103', 'card', 'Visa', 'Visa ending in 3066', 354700, 'INR', 'captured', '2026-08-03T16:46:00+05:30'),
('PAY-1095', 'ORD-1095', 'upi', 'UPI', 'UPI account', 519900, 'INR', 'captured', '2026-08-01T12:31:00+05:30'),
('PAY-1064', 'ORD-1064', 'card', 'Mastercard', 'Mastercard ending in 7710', 639800, 'INR', 'captured', '2026-07-26T11:11:00+05:30'),
('PAY-1071', 'ORD-1071', 'card', 'Mastercard', 'Mastercard ending in 7710', 249900, 'INR', 'captured', '2026-07-22T15:26:00+05:30');

INSERT INTO shipments (shipment_id, order_id, status, carrier, tracking_number, delivery_address_id, estimated_delivery_start, estimated_delivery_end, shipped_at, delivered_at, delivered_to) VALUES
('SHP-1042', 'ORD-1042', 'in_transit', 'BlueDart', 'BD-8829104', 'ADDR-001-HOME', '2026-08-11T10:00:00+05:30', '2026-08-11T14:00:00+05:30', '2026-08-07T09:20:00+05:30', NULL, NULL),
('SHP-1087-BOTTLE', 'ORD-1087', 'in_transit', 'Delhivery', 'DL-1087002', 'ADDR-002-HOME', '2026-08-09T09:00:00+05:30', '2026-08-09T18:00:00+05:30', '2026-08-07T18:00:00+05:30', NULL, NULL),
('SHP-1087-BACKPACK', 'ORD-1087', 'preparing', NULL, NULL, 'ADDR-002-HOME', NULL, NULL, NULL, NULL, NULL),
('SHP-1103-LAMP', 'ORD-1103', 'in_transit', 'BlueDart', 'BD-1103001', 'ADDR-003-HOME', '2026-08-10T09:00:00+05:30', '2026-08-10T18:00:00+05:30', '2026-08-07T15:00:00+05:30', NULL, NULL),
('SHP-1103-NOTEBOOK', 'ORD-1103', 'preparing', NULL, NULL, 'ADDR-003-OFFICE', '2026-08-12T09:00:00+05:30', '2026-08-12T18:00:00+05:30', NULL, NULL, NULL),
('SHP-1095', 'ORD-1095', 'delivered', 'Ecom Express', 'EC-1095001', 'ADDR-004-HOME', '2026-08-08T09:00:00+05:30', '2026-08-08T18:00:00+05:30', '2026-08-05T12:00:00+05:30', '2026-08-08T15:42:00+05:30', 'reception/security'),
('SHP-1064', 'ORD-1064', 'delivered', 'Delhivery', 'DL-6631098', 'ADDR-005-HOME', '2026-08-03T09:00:00+05:30', '2026-08-03T18:00:00+05:30', '2026-07-30T10:00:00+05:30', '2026-08-03T13:15:00+05:30', 'customer'),
('SHP-1071', 'ORD-1071', 'delivered', 'BlueDart', 'BD-1071001', 'ADDR-005-HOME', '2026-07-27T09:00:00+05:30', '2026-07-27T18:00:00+05:30', '2026-07-24T10:00:00+05:30', '2026-07-27T16:42:00+05:30', 'customer');

INSERT INTO shipment_items (shipment_id, order_item_id, quantity) VALUES
('SHP-1042', 'ITEM-1042-1', 1),
('SHP-1087-BOTTLE', 'ITEM-1087-2', 1),
('SHP-1087-BACKPACK', 'ITEM-1087-1', 1),
('SHP-1103-LAMP', 'ITEM-1103-1', 1),
('SHP-1103-NOTEBOOK', 'ITEM-1103-2', 1),
('SHP-1095', 'ITEM-1095-1', 1),
('SHP-1064', 'ITEM-1064-1', 2),
('SHP-1071', 'ITEM-1071-1', 1);

INSERT INTO shipment_events (shipment_id, status, description, location, occurred_at) VALUES
('SHP-1042', 'shipped', 'Order handed to the courier', 'Bengaluru', '2026-08-07T09:20:00+05:30'),
('SHP-1042', 'in_transit', 'Departed the Bengaluru sorting facility', 'Bengaluru', '2026-08-08T06:10:00+05:30'),
('SHP-1087-BOTTLE', 'shipped', 'Bottle handed to the courier', 'Chennai', '2026-08-07T18:00:00+05:30'),
('SHP-1103-LAMP', 'shipped', 'Desk lamp handed to the courier', 'Mumbai', '2026-08-07T15:00:00+05:30'),
('SHP-1095', 'delivered', 'Package marked delivered to reception/security', 'Ahmedabad', '2026-08-08T15:42:00+05:30'),
('SHP-1064', 'delivered', 'Package delivered to customer', 'New Delhi', '2026-08-03T13:15:00+05:30'),
('SHP-1071', 'delivered', 'Package delivered to customer', 'New Delhi', '2026-07-27T16:42:00+05:30');

INSERT INTO cancellations (cancellation_id, order_id, status, requested_at, resolved_at, reason, expected_refund_minor) VALUES
('CAN-5408', 'ORD-1038', 'completed', '2026-08-05T10:00:00+05:30', '2026-08-06T11:30:00+05:30', 'Customer requested cancellation', 429900),
('CAN-5521', 'ORD-1087', 'awaiting_approval', '2026-08-08T10:20:00+05:30', NULL, 'Customer no longer needs backpack', 249900);

INSERT INTO cancellation_items (cancellation_id, order_item_id, quantity) VALUES
('CAN-5408', 'ITEM-1038-1', 1),
('CAN-5521', 'ITEM-1087-1', 1);

INSERT INTO refunds (refund_id, order_id, cancellation_id, payment_id, status, amount_minor, currency, initiated_at, expected_by, completed_at) VALUES
('REF-1038', 'ORD-1038', 'CAN-5408', 'PAY-1038', 'initiated', 429900, 'INR', '2026-08-06T11:35:00+05:30', '2026-08-12T23:59:59+05:30', NULL);

INSERT INTO returns (return_id, order_id, status, resolution, requested_at, pickup_at, expected_refund_minor) VALUES
('RET-2916', 'ORD-1064', 'booked', 'refund', '2026-08-08T14:00:00+05:30', '2026-08-10T10:00:00+05:30', 319900);

INSERT INTO return_items (return_id, order_item_id, quantity) VALUES
('RET-2916', 'ITEM-1064-1', 1);

INSERT INTO support_tickets (ticket_id, customer_id, order_id, type, status, priority, summary, preferred_resolution, created_at, expected_update_at) VALUES
('TKT-8044', 'CUS-004', 'ORD-1095', 'delivered_not_received', 'investigating', 'high', 'Package marked delivered but not received; customer checked with security desk.', 'replacement', '2026-08-08T16:00:00+05:30', '2026-08-10T16:00:00+05:30');

INSERT INTO invoices (invoice_id, order_id, invoice_number, issued_at) VALUES
('INV-1042', 'ORD-1042', '2026-1042', '2026-08-04T14:22:00+05:30');

COMMIT;
