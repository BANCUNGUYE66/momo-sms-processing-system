-- =============================================================================
-- MoMo SMS Processing System — SQLite sample data
-- Author: Eloi (Database Developer)
-- Requires: schema.sql already applied
-- =============================================================================

-- Sample users (at least 5 realistic wallet holders)
INSERT OR IGNORE INTO users (phone_number, name, user_type, wallet_balance) VALUES
    ('+250788111111', 'Eloi Mizero',              'personal',  18500.00),
    ('+250788222222', 'Aimable Bancunguye',       'personal',  42000.00),
    ('+250788333333', 'Richard Niyonzima',        'personal',   7600.00),
    ('+250788444444', 'Jean de Dieu Tuyishime',   'personal',   980.00),
    ('+250788999999', 'MTN MoMo Agent',           'agent',    500000.00),
    ('+250788555555', 'Kigali Mini Mart',         'merchant',  88000.00);

-- Notification preferences (M:N junction — at least 5 rows)
INSERT OR IGNORE INTO user_category_preferences (user_id, category_id, notification_enabled)
SELECT u.id, c.id, pref.enabled
FROM (
    SELECT '+250788111111' AS phone, 'TRANSFER' AS code, 1 AS enabled UNION ALL
    SELECT '+250788111111', 'RECEIVE',  1 UNION ALL
    SELECT '+250788111111', 'AIRTIME',  0 UNION ALL
    SELECT '+250788222222', 'PAYMENT',  1 UNION ALL
    SELECT '+250788333333', 'CASH_OUT', 1 UNION ALL
    SELECT '+250788444444', 'RECEIVE',  1
) AS pref
JOIN users u ON u.phone_number = pref.phone
JOIN transaction_categories c ON c.code = pref.code;

-- Sample transactions (at least 5 realistic MoMo SMS records)
INSERT OR IGNORE INTO transactions (
    transaction_ref, sender_id, receiver_id, category_id,
    amount, fee_charged, closing_balance, timestamp, status, raw_text
)
SELECT
    '76662021700',
    s.id, r.id, c.id,
    3000.00, 0.00, 21500.00,
    '2024-05-10 16:30:51', 'completed',
    'You have received 3000 RWF from Aimable Bancunguye (250788222222) at 2024-05-10 16:30:51. Financial Transaction Id: 76662021700.'
FROM users s, users r, transaction_categories c
WHERE s.phone_number = '+250788222222'
  AND r.phone_number = '+250788111111'
  AND c.code = 'RECEIVE';

INSERT OR IGNORE INTO transactions (
    transaction_ref, sender_id, receiver_id, category_id,
    amount, fee_charged, closing_balance, timestamp, status, raw_text
)
SELECT
    '73214484437',
    s.id, r.id, c.id,
    1500.00, 20.00, 20000.00,
    '2024-05-10 16:31:39', 'completed',
    'You have transferred 1500 RWF to Richard Niyonzima (250788333333) at 2024-05-10 16:31:39. Fee was 20 RWF. Financial Transaction Id: 73214484437.'
FROM users s, users r, transaction_categories c
WHERE s.phone_number = '+250788111111'
  AND r.phone_number = '+250788333333'
  AND c.code = 'TRANSFER';

INSERT OR IGNORE INTO transactions (
    transaction_ref, sender_id, receiver_id, category_id,
    amount, fee_charged, closing_balance, timestamp, status, raw_text
)
SELECT
    '81009923411',
    s.id, r.id, c.id,
    5000.00, 0.00, 93000.00,
    '2024-05-11 09:15:00', 'completed',
    'Payment of 5000 RWF to Kigali Mini Mart completed at 2024-05-11 09:15:00. Financial Transaction Id: 81009923411.'
FROM users s, users r, transaction_categories c
WHERE s.phone_number = '+250788222222'
  AND r.phone_number = '+250788555555'
  AND c.code = 'PAYMENT';

INSERT OR IGNORE INTO transactions (
    transaction_ref, sender_id, receiver_id, category_id,
    amount, fee_charged, closing_balance, timestamp, status, raw_text
)
SELECT
    '90211455622',
    s.id, r.id, c.id,
    1000.00, 0.00, 19000.00,
    '2024-05-11 11:20:10', 'completed',
    'You bought airtime of 1000 RWF on 2024-05-11 11:20:10. Financial Transaction Id: 90211455622.'
FROM users s, users r, transaction_categories c
WHERE s.phone_number = '+250788111111'
  AND r.phone_number = '+250788999999'
  AND c.code = 'AIRTIME';

INSERT OR IGNORE INTO transactions (
    transaction_ref, sender_id, receiver_id, category_id,
    amount, fee_charged, closing_balance, timestamp, status, raw_text
)
SELECT
    '99341122334',
    s.id, r.id, c.id,
    20000.00, 200.00, 55600.00,
    '2024-05-12 14:00:00', 'completed',
    'You have withdrawn 20000 RWF from agent MTN MoMo Agent. Fee 200 RWF. Financial Transaction Id: 99341122334.'
FROM users s, users r, transaction_categories c
WHERE s.phone_number = '+250788333333'
  AND r.phone_number = '+250788999999'
  AND c.code = 'CASH_OUT';

-- Sample system logs
INSERT OR IGNORE INTO system_logs (log_level, module_name, message, timestamp) VALUES
    ('INFO',    'xml_parser',      'XML payload successfully parsed. Total raw records: 5',           '2024-05-12 14:05:00'),
    ('INFO',    'clean_normalize', 'Normalized phone numbers to +250 international format',           '2024-05-12 14:05:01'),
    ('INFO',    'categorize',      'Successfully categorized 5 transactions across 5 categories',     '2024-05-12 14:05:02'),
    ('INFO',    'load_db',         'Loaded 5 transactions into SQLite table transactions',            '2024-05-12 14:05:03'),
    ('WARNING', 'dead_letter',     'Skipped 0 malformed XML elements',                                '2024-05-12 14:05:04');
