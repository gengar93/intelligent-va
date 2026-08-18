PRAGMA foreign_keys = ON;

BEGIN;

INSERT INTO customers (customer_id, name, email) VALUES
    ('CUS-001', 'Aarav Sharma', 'aarav.sharma@example.test'),
    ('CUS-002', 'Emily Carter', 'emily.carter@example.test'),
    ('CUS-003', 'Marcus Johnson', 'marcus.johnson@example.test'),
    ('CUS-004', 'Sofia Rodriguez', 'sofia.rodriguez@example.test'),
    ('CUS-005', 'Ethan Brooks', 'ethan.brooks@example.test');

INSERT INTO products (product_id, sku, name, description, image_url) VALUES
    ('PROD-HEADSET', 'NV-H100-BLK', 'Nova H100 Wireless Headset', 'Wireless over-ear headset with a noise-cancelling microphone', '/products/headphones.svg'),
    ('PROD-MONITOR', 'NV-M27-4K', 'NovaView 27-inch 4K Monitor', '27-inch 4K IPS monitor with USB-C connectivity', '/products/monitor.svg'),
    ('PROD-KEYBOARD', 'NV-K80-RGB', 'NovaType K80 Mechanical Keyboard', 'Compact mechanical keyboard with hot-swappable switches', '/products/keyboard.svg'),
    ('PROD-MOUSE', 'NV-M60-WL', 'NovaPoint M60 Wireless Mouse', 'Ergonomic wireless mouse with programmable controls', '/products/mouse.svg'),
    ('PROD-WEBCAM', 'NV-CAM-4K', 'NovaCam 4K Webcam', '4K webcam with autofocus and dual microphones', '/products/webcam.svg'),
    ('PROD-DOCK', 'NV-DOCK-12', 'NovaDock 12-in-1 USB-C Dock', 'USB-C docking station with dual-display support', '/products/dock.svg'),
    ('PROD-SSD', 'NV-SSD-1T', 'NovaDrive 1TB Portable SSD', 'USB 3.2 portable solid-state drive', '/products/ssd.svg'),
    ('PROD-SPEAKERS', 'NV-SP20-BLK', 'NovaSound SP20 Desktop Speakers', 'Compact stereo desktop speakers', '/products/speakers.svg'),
    ('PROD-MIC', 'NV-MIC-PRO', 'NovaMic Pro USB Microphone', 'Cardioid USB microphone for calls and streaming', '/products/microphone.svg'),
    ('PROD-HUB', 'NV-HUB-7', 'NovaHub 7-port USB-C Hub', 'Portable USB-C hub with HDMI and card reader', '/products/hub.svg');

INSERT INTO orders (
    order_id, customer_id, status, placed_at, estimated_delivery_date,
    delivered_at, currency, delivery_address, payment_method_display
) VALUES
    ('ORD-1042', 'CUS-001', 'shipped', '2026-08-14T10:20:00-04:00', '2026-08-21', NULL, 'USD', '418 W 22nd St, New York, NY 10011', 'Visa ending in 1842'),
    ('ORD-1038', 'CUS-001', 'cancelled', '2026-08-05T08:35:00-04:00', '2026-08-10', NULL, 'USD', '418 W 22nd St, New York, NY 10011', 'Visa ending in 1842'),
    ('ORD-1110', 'CUS-001', 'delivered', '2026-07-24T15:05:00-04:00', '2026-07-30', '2026-07-30T13:42:00-04:00', 'USD', '418 W 22nd St, New York, NY 10011', 'Visa ending in 1842'),
    ('ORD-1121', 'CUS-001', 'processing', '2026-08-01T11:45:00-04:00', '2026-08-24', NULL, 'USD', '418 W 22nd St, New York, NY 10011', 'Visa ending in 1842'),

    ('ORD-1087', 'CUS-002', 'processing', '2026-08-16T09:15:00-05:00', '2026-08-23', NULL, 'USD', '2634 N Orchard St, Chicago, IL 60614', 'Mastercard ending in 6208'),
    ('ORD-1095', 'CUS-002', 'delivered', '2026-08-01T12:30:00-05:00', '2026-08-08', '2026-08-08T15:42:00-05:00', 'USD', '2634 N Orchard St, Chicago, IL 60614', 'Mastercard ending in 6208'),
    ('ORD-1114', 'CUS-002', 'shipped', '2026-08-12T16:10:00-05:00', '2026-08-20', NULL, 'USD', '2634 N Orchard St, Chicago, IL 60614', 'Mastercard ending in 6208'),
    ('ORD-1124', 'CUS-002', 'cancelled', '2026-07-19T10:00:00-05:00', '2026-07-25', NULL, 'USD', '2634 N Orchard St, Chicago, IL 60614', 'Mastercard ending in 6208'),

    ('ORD-1064', 'CUS-003', 'delivered', '2026-07-26T11:10:00-07:00', '2026-08-03', '2026-08-03T13:15:00-07:00', 'USD', '782 Valencia St, San Francisco, CA 94110', 'Visa ending in 7710'),
    ('ORD-1071', 'CUS-003', 'delivered', '2026-07-15T14:25:00-07:00', '2026-07-22', '2026-07-22T11:05:00-07:00', 'USD', '782 Valencia St, San Francisco, CA 94110', 'Visa ending in 7710'),
    ('ORD-1118', 'CUS-003', 'shipped', '2026-08-13T09:40:00-07:00', '2026-08-20', NULL, 'USD', '782 Valencia St, San Francisco, CA 94110', 'Visa ending in 7710'),
    ('ORD-1127', 'CUS-003', 'processing', '2026-08-17T16:55:00-07:00', '2026-08-25', NULL, 'USD', '782 Valencia St, San Francisco, CA 94110', 'Visa ending in 7710'),

    ('ORD-1130', 'CUS-004', 'delivered', '2026-07-29T13:20:00-04:00', '2026-08-05', '2026-08-05T14:18:00-04:00', 'USD', '1217 E 6th St, Austin, TX 78702', 'Amex ending in 3005'),
    ('ORD-1131', 'CUS-004', 'shipped', '2026-08-11T10:35:00-05:00', '2026-08-19', NULL, 'USD', '1217 E 6th St, Austin, TX 78702', 'Amex ending in 3005'),
    ('ORD-1132', 'CUS-004', 'processing', '2026-08-18T08:10:00-05:00', '2026-08-26', NULL, 'USD', '1217 E 6th St, Austin, TX 78702', 'Amex ending in 3005'),
    ('ORD-1133', 'CUS-004', 'cancelled', '2026-07-10T17:45:00-05:00', '2026-07-17', NULL, 'USD', '1217 E 6th St, Austin, TX 78702', 'Amex ending in 3005'),

    ('ORD-1140', 'CUS-005', 'delivered', '2026-08-02T11:30:00-07:00', '2026-08-09', '2026-08-09T16:22:00-07:00', 'USD', '905 NE 43rd Ave, Portland, OR 97213', 'Discover ending in 4481'),
    ('ORD-1141', 'CUS-005', 'shipped', '2026-08-10T14:05:00-07:00', '2026-08-19', NULL, 'USD', '905 NE 43rd Ave, Portland, OR 97213', 'Discover ending in 4481'),
    ('ORD-1142', 'CUS-005', 'processing', '2026-08-17T09:25:00-07:00', '2026-08-24', NULL, 'USD', '905 NE 43rd Ave, Portland, OR 97213', 'Discover ending in 4481'),
    ('ORD-1143', 'CUS-005', 'delivered', '2026-07-21T12:40:00-07:00', '2026-07-28', '2026-07-28T10:50:00-07:00', 'USD', '905 NE 43rd Ave, Portland, OR 97213', 'Discover ending in 4481');

INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price_minor) VALUES
    ('ITEM-1042-1', 'ORD-1042', 'PROD-HEADSET', 1, 12999),
    ('ITEM-1038-1', 'ORD-1038', 'PROD-MONITOR', 1, 32999),
    ('ITEM-1110-1', 'ORD-1110', 'PROD-KEYBOARD', 1, 8999),
    ('ITEM-1110-2', 'ORD-1110', 'PROD-MOUSE', 1, 5999),
    ('ITEM-1121-1', 'ORD-1121', 'PROD-WEBCAM', 1, 10999),
    ('ITEM-1087-1', 'ORD-1087', 'PROD-DOCK', 1, 15999),
    ('ITEM-1087-2', 'ORD-1087', 'PROD-HUB', 1, 4999),
    ('ITEM-1095-1', 'ORD-1095', 'PROD-MONITOR', 1, 32999),
    ('ITEM-1114-1', 'ORD-1114', 'PROD-WEBCAM', 1, 10999),
    ('ITEM-1114-2', 'ORD-1114', 'PROD-MIC', 1, 13999),
    ('ITEM-1124-1', 'ORD-1124', 'PROD-SPEAKERS', 1, 7999),
    ('ITEM-1064-1', 'ORD-1064', 'PROD-KEYBOARD', 2, 8999),
    ('ITEM-1071-1', 'ORD-1071', 'PROD-HEADSET', 1, 12999),
    ('ITEM-1118-1', 'ORD-1118', 'PROD-SSD', 1, 11999),
    ('ITEM-1118-2', 'ORD-1118', 'PROD-HUB', 1, 4999),
    ('ITEM-1127-1', 'ORD-1127', 'PROD-MIC', 1, 13999),
    ('ITEM-1130-1', 'ORD-1130', 'PROD-MONITOR', 1, 32999),
    ('ITEM-1130-2', 'ORD-1130', 'PROD-WEBCAM', 1, 10999),
    ('ITEM-1131-1', 'ORD-1131', 'PROD-DOCK', 1, 15999),
    ('ITEM-1132-1', 'ORD-1132', 'PROD-MOUSE', 1, 5999),
    ('ITEM-1132-2', 'ORD-1132', 'PROD-KEYBOARD', 1, 8999),
    ('ITEM-1133-1', 'ORD-1133', 'PROD-SPEAKERS', 1, 7999),
    ('ITEM-1140-1', 'ORD-1140', 'PROD-SSD', 2, 11999),
    ('ITEM-1141-1', 'ORD-1141', 'PROD-HEADSET', 1, 12999),
    ('ITEM-1141-2', 'ORD-1141', 'PROD-HUB', 1, 4999),
    ('ITEM-1142-1', 'ORD-1142', 'PROD-MONITOR', 1, 32999),
    ('ITEM-1143-1', 'ORD-1143', 'PROD-WEBCAM', 1, 10999);

INSERT INTO tickets (
    ticket_id, ticket_type, order_id, status, created_at, updated_at,
    completed_at, failure_reason
) VALUES
    ('TKT-7001', 'invoice_generation', 'ORD-1042', 'completed', '2026-08-15T10:02:00-04:00', '2026-08-15T10:04:00-04:00', '2026-08-15T10:04:00-04:00', NULL),
    ('TKT-7002', 'invoice_generation', 'ORD-1087', 'in_progress', '2026-08-17T11:14:00-05:00', '2026-08-17T11:15:00-05:00', NULL, NULL),
    ('TKT-7003', 'invoice_generation', 'ORD-1064', 'failed', '2026-08-05T12:20:00-07:00', '2026-08-05T12:21:00-07:00', NULL, 'Billing address could not be validated'),
    ('TKT-7004', 'invoice_generation', 'ORD-1095', 'completed', '2026-08-09T09:10:00-05:00', '2026-08-09T09:12:00-05:00', '2026-08-09T09:12:00-05:00', NULL),
    ('TKT-7005', 'invoice_generation', 'ORD-1114', 'queued', '2026-08-18T08:20:00-05:00', '2026-08-18T08:20:00-05:00', NULL, NULL),
    ('TKT-7006', 'invoice_generation', 'ORD-1118', 'in_progress', '2026-08-17T13:30:00-07:00', '2026-08-17T13:31:00-07:00', NULL, NULL),
    ('TKT-7007', 'invoice_generation', 'ORD-1143', 'failed', '2026-07-29T10:15:00-07:00', '2026-07-29T10:17:00-07:00', NULL, 'Payment record could not be reconciled'),
    ('TKT-7008', 'invoice_generation', 'ORD-1130', 'completed', '2026-08-06T11:05:00-05:00', '2026-08-06T11:07:00-05:00', '2026-08-06T11:07:00-05:00', NULL),
    ('TKT-7009', 'invoice_generation', 'ORD-1141', 'queued', '2026-08-18T07:45:00-07:00', '2026-08-18T07:45:00-07:00', NULL, NULL),
    ('TKT-7010', 'invoice_generation', 'ORD-1140', 'completed', '2026-08-10T09:30:00-07:00', '2026-08-10T09:32:00-07:00', '2026-08-10T09:32:00-07:00', NULL);

INSERT INTO ticket_status_history (
    ticket_status_history_id, ticket_id, from_status, to_status, changed_at, note
) VALUES
    ('TSH-9001', 'TKT-7001', NULL, 'queued', '2026-08-15T10:02:00-04:00', 'Customer requested invoice'),
    ('TSH-9002', 'TKT-7001', 'queued', 'in_progress', '2026-08-15T10:03:00-04:00', 'Generator claimed ticket'),
    ('TSH-9003', 'TKT-7001', 'in_progress', 'completed', '2026-08-15T10:04:00-04:00', 'Invoice INV-2026-00481 issued'),
    ('TSH-9010', 'TKT-7002', NULL, 'queued', '2026-08-17T11:14:00-05:00', 'Customer requested invoice'),
    ('TSH-9011', 'TKT-7002', 'queued', 'in_progress', '2026-08-17T11:15:00-05:00', 'Generator claimed ticket'),
    ('TSH-9020', 'TKT-7003', NULL, 'queued', '2026-08-05T12:20:00-07:00', 'Customer requested invoice'),
    ('TSH-9021', 'TKT-7003', 'queued', 'in_progress', '2026-08-05T12:20:30-07:00', 'Generator claimed ticket'),
    ('TSH-9022', 'TKT-7003', 'in_progress', 'failed', '2026-08-05T12:21:00-07:00', 'Billing address could not be validated'),
    ('TSH-9030', 'TKT-7004', NULL, 'queued', '2026-08-09T09:10:00-05:00', 'Customer requested invoice'),
    ('TSH-9031', 'TKT-7004', 'queued', 'in_progress', '2026-08-09T09:11:00-05:00', 'Generator claimed ticket'),
    ('TSH-9032', 'TKT-7004', 'in_progress', 'completed', '2026-08-09T09:12:00-05:00', 'Invoice INV-2026-00482 issued'),
    ('TSH-9040', 'TKT-7005', NULL, 'queued', '2026-08-18T08:20:00-05:00', 'Customer requested invoice'),
    ('TSH-9050', 'TKT-7006', NULL, 'queued', '2026-08-17T13:30:00-07:00', 'Customer requested invoice'),
    ('TSH-9051', 'TKT-7006', 'queued', 'in_progress', '2026-08-17T13:31:00-07:00', 'Generator claimed ticket'),
    ('TSH-9060', 'TKT-7007', NULL, 'queued', '2026-07-29T10:15:00-07:00', 'Customer requested invoice'),
    ('TSH-9061', 'TKT-7007', 'queued', 'in_progress', '2026-07-29T10:16:00-07:00', 'Generator claimed ticket'),
    ('TSH-9062', 'TKT-7007', 'in_progress', 'failed', '2026-07-29T10:17:00-07:00', 'Payment record could not be reconciled'),
    ('TSH-9070', 'TKT-7008', NULL, 'queued', '2026-08-06T11:05:00-05:00', 'Customer requested invoice'),
    ('TSH-9071', 'TKT-7008', 'queued', 'in_progress', '2026-08-06T11:06:00-05:00', 'Generator claimed ticket'),
    ('TSH-9072', 'TKT-7008', 'in_progress', 'completed', '2026-08-06T11:07:00-05:00', 'Invoice INV-2026-00483 issued'),
    ('TSH-9080', 'TKT-7009', NULL, 'queued', '2026-08-18T07:45:00-07:00', 'Customer requested invoice'),
    ('TSH-9090', 'TKT-7010', NULL, 'queued', '2026-08-10T09:30:00-07:00', 'Customer requested invoice'),
    ('TSH-9091', 'TKT-7010', 'queued', 'in_progress', '2026-08-10T09:31:00-07:00', 'Generator claimed ticket'),
    ('TSH-9092', 'TKT-7010', 'in_progress', 'completed', '2026-08-10T09:32:00-07:00', 'Invoice INV-2026-00484 issued');

INSERT INTO invoices (
    invoice_id, invoice_number, order_id, generation_ticket_id, issued_at,
    billing_name, billing_address, currency, subtotal_minor, tax_minor,
    total_minor, document_url
) VALUES
    ('INV-481', 'INV-2026-00481', 'ORD-1042', 'TKT-7001', '2026-08-15T10:04:00-04:00', 'Aarav Sharma', '418 W 22nd St, New York, NY 10011', 'USD', 12999, 0, 12999, '/api/customers/CUS-001/orders/ORD-1042/invoice.pdf'),
    ('INV-482', 'INV-2026-00482', 'ORD-1095', 'TKT-7004', '2026-08-09T09:12:00-05:00', 'Emily Carter', '2634 N Orchard St, Chicago, IL 60614', 'USD', 32999, 0, 32999, '/api/customers/CUS-002/orders/ORD-1095/invoice.pdf'),
    ('INV-483', 'INV-2026-00483', 'ORD-1130', 'TKT-7008', '2026-08-06T11:07:00-05:00', 'Sofia Rodriguez', '1217 E 6th St, Austin, TX 78702', 'USD', 43998, 0, 43998, '/api/customers/CUS-004/orders/ORD-1130/invoice.pdf'),
    ('INV-484', 'INV-2026-00484', 'ORD-1140', 'TKT-7010', '2026-08-10T09:32:00-07:00', 'Ethan Brooks', '905 NE 43rd Ave, Portland, OR 97213', 'USD', 23998, 0, 23998, '/api/customers/CUS-005/orders/ORD-1140/invoice.pdf');

INSERT INTO invoice_items (
    invoice_item_id, invoice_id, source_order_item_id, description, quantity,
    unit_price_minor, tax_minor, line_total_minor
) VALUES
    ('INI-481-1', 'INV-481', 'ITEM-1042-1', 'Nova H100 Wireless Headset', 1, 12999, 0, 12999),
    ('INI-482-1', 'INV-482', 'ITEM-1095-1', 'NovaView 27-inch 4K Monitor', 1, 32999, 0, 32999),
    ('INI-483-1', 'INV-483', 'ITEM-1130-1', 'NovaView 27-inch 4K Monitor', 1, 32999, 0, 32999),
    ('INI-483-2', 'INV-483', 'ITEM-1130-2', 'NovaCam 4K Webcam', 1, 10999, 0, 10999),
    ('INI-484-1', 'INV-484', 'ITEM-1140-1', 'NovaDrive 1TB Portable SSD', 2, 11999, 0, 23998);

COMMIT;
