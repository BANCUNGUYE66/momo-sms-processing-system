-- =============================================================================
-- MoMo SMS Processing System — SQLite Schema
-- Author: Eloi (Database Developer)
-- Engine: SQLite 3
-- File: data/db.sqlite3
--
-- Apply with:
--   python scripts/init_db.py
--   python scripts/init_db.py --seed
--
-- SQLite notes:
--   * Enable foreign keys on every connection: PRAGMA foreign_keys = ON;
--   * ENUM types are enforced with CHECK constraints
--   * Monetary values use NUMERIC to preserve decimal precision
--   * Timestamps are stored as ISO-8601 TEXT
-- =============================================================================

-- Enable foreign keys and WAL from the Python connection (etl/load_db.connect).
-- PRAGMA statements are kept out of this script because executescript() does
-- not reliably apply statements that return rows.

-- -----------------------------------------------------------------------------
-- 1. users
-- Wallet holders extracted from SMS metadata (customers, merchants, agents).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number    TEXT    NOT NULL UNIQUE,
    name            TEXT    NOT NULL,
    user_type       TEXT    NOT NULL DEFAULT 'personal'
                        CHECK (user_type IN ('personal', 'merchant', 'agent', 'system')),
    wallet_balance  NUMERIC NOT NULL DEFAULT 0.00
                        CHECK (wallet_balance >= 0.00),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_phone ON users (phone_number);
CREATE INDEX IF NOT EXISTS idx_users_type  ON users (user_type);

-- -----------------------------------------------------------------------------
-- 2. transaction_categories
-- Lookup table for ETL classification codes (TRANSFER, RECEIVE, ...).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaction_categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,
    category_name   TEXT    NOT NULL UNIQUE,
    tx_type         TEXT    NOT NULL
                        CHECK (tx_type IN ('payment', 'transfer', 'deposit', 'withdrawal', 'airtime', 'other')),
    description     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_categories_code     ON transaction_categories (code);
CREATE INDEX IF NOT EXISTS idx_categories_tx_type  ON transaction_categories (tx_type);

-- -----------------------------------------------------------------------------
-- 3. user_category_preferences
-- Junction table resolving the M:N relationship between users and categories.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_category_preferences (
    user_id                 INTEGER NOT NULL,
    category_id             INTEGER NOT NULL,
    notification_enabled    INTEGER NOT NULL DEFAULT 1
                                CHECK (notification_enabled IN (0, 1)),
    created_at              TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, category_id),
    FOREIGN KEY (user_id)     REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES transaction_categories (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ucp_user     ON user_category_preferences (user_id);
CREATE INDEX IF NOT EXISTS idx_ucp_category ON user_category_preferences (category_id);

-- -----------------------------------------------------------------------------
-- 4. transactions
-- Normalized MoMo SMS records after parse → clean → categorize.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_ref   TEXT    UNIQUE,
    sender_id         INTEGER NOT NULL,
    receiver_id       INTEGER,
    category_id       INTEGER NOT NULL,
    amount            NUMERIC NOT NULL
                          CHECK (amount > 0.00),
    fee_charged       NUMERIC NOT NULL DEFAULT 0.00
                          CHECK (fee_charged >= 0.00),
    closing_balance   NUMERIC
                          CHECK (closing_balance IS NULL OR closing_balance >= 0.00),
    timestamp         TEXT    NOT NULL,
    status            TEXT    NOT NULL DEFAULT 'completed'
                          CHECK (status IN ('completed', 'failed', 'pending')),
    raw_text          TEXT    NOT NULL,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (sender_id)   REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES transaction_categories (id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tx_ref       ON transactions (transaction_ref);
CREATE INDEX IF NOT EXISTS idx_tx_sender    ON transactions (sender_id);
CREATE INDEX IF NOT EXISTS idx_tx_receiver  ON transactions (receiver_id);
CREATE INDEX IF NOT EXISTS idx_tx_category  ON transactions (category_id);
CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions (timestamp);
CREATE INDEX IF NOT EXISTS idx_tx_status    ON transactions (status);

-- Prevent duplicate ingest of the same SMS when no financial reference is present.
CREATE UNIQUE INDEX IF NOT EXISTS idx_tx_raw_timestamp
    ON transactions (timestamp, raw_text);

-- -----------------------------------------------------------------------------
-- 5. system_logs
-- Isolated ETL / API diagnostic log. No FK to keep logging available if
-- transaction inserts fail.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level    TEXT    NOT NULL
                     CHECK (log_level IN ('INFO', 'WARNING', 'ERROR')),
    module_name  TEXT    NOT NULL,
    message      TEXT    NOT NULL,
    timestamp    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_log_level     ON system_logs (log_level);
CREATE INDEX IF NOT EXISTS idx_log_module    ON system_logs (module_name);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON system_logs (timestamp);

-- -----------------------------------------------------------------------------
-- Default category rows (aligned with etl/config.py CATEGORIES)
-- -----------------------------------------------------------------------------
INSERT OR IGNORE INTO transaction_categories (code, category_name, tx_type, description) VALUES
    ('TRANSFER',  'Wallet Transfer',   'transfer',    'Money sent from one personal wallet to another'),
    ('RECEIVE',   'Incoming Transfer', 'deposit',     'Money received into the wallet from another party'),
    ('PAYMENT',   'Merchant Payment',  'payment',     'Payment to a merchant or bill service'),
    ('CASH_OUT',  'Cash Out',          'withdrawal',  'Withdrawal or cash-out from a mobile money agent'),
    ('AIRTIME',   'Airtime Top-up',    'airtime',     'Airtime, bundle, or recharge purchase'),
    ('OTHER',     'Uncategorized',     'other',       'SMS records that did not match a known category rule');

-- -----------------------------------------------------------------------------
-- Analytics-friendly flattened view used by the API and dashboard queries.
-- Column aliases (sender, category) keep the existing API contract working.
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_transaction_details AS
SELECT
    t.id,
    t.transaction_ref,
    s.phone_number          AS sender,
    s.name                  AS sender_name,
    r.phone_number          AS receiver,
    r.name                  AS receiver_name,
    c.code                  AS category,
    c.category_name,
    c.tx_type,
    t.amount,
    t.fee_charged,
    t.closing_balance,
    t.timestamp,
    t.status,
    t.raw_text,
    t.created_at
FROM transactions t
JOIN users s ON s.id = t.sender_id
LEFT JOIN users r ON r.id = t.receiver_id
JOIN transaction_categories c ON c.id = t.category_id;
