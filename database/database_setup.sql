-- =============================================================================
-- MoMo SMS Processing System - Database Setup Script
-- Author: Jean de Dieu Tuyishime (Jtuyishime6)
-- Role: Architecture / QA
-- Target Engine: MySQL 8.0+
-- Database: momo_sms_processing_system
-- =============================================================================

CREATE DATABASE IF NOT EXISTS momo_sms_processing_system
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE momo_sms_processing_system;

-- -----------------------------------------------------------------------------
-- 1. Table: users
-- Core entity representing wallet holders, customers, merchants, and agents.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique primary identifier for each user',
    phone_number VARCHAR(20) NOT NULL UNIQUE COMMENT 'Normalized mobile phone number (+250 format)',
    name VARCHAR(100) NOT NULL COMMENT 'Full name or business display name of the account holder',
    user_type ENUM('personal', 'merchant', 'agent') DEFAULT 'personal' COMMENT 'Role classification of the account holder',
    wallet_balance DECIMAL(15,2) DEFAULT 0.00 COMMENT 'Current mobile wallet balance in RWF',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp when user account was registered',
    INDEX idx_users_phone (phone_number),
    INDEX idx_users_type (user_type),
    CONSTRAINT chk_wallet_balance CHECK (wallet_balance >= 0.00)
) ENGINE=InnoDB COMMENT='Stores registered Mobile Money users and wallet holders';

-- -----------------------------------------------------------------------------
-- 2. Table: transaction_categories
-- Classification entity defining transaction types and descriptions.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaction_categories (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique category identifier',
    category_name VARCHAR(50) NOT NULL UNIQUE COMMENT 'Name of the transaction category (e.g. Peer Payment)',
    tx_type ENUM('payment', 'transfer', 'deposit', 'airtime') NOT NULL COMMENT 'High-level financial transaction type',
    description TEXT COMMENT 'Detailed description of the transaction category',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp when category was created',
    INDEX idx_category_name (category_name),
    INDEX idx_tx_type (tx_type)
) ENGINE=InnoDB COMMENT='Defines categories for classifying MoMo transactions';

-- -----------------------------------------------------------------------------
-- 3. Table: user_category_preferences
-- Junction table resolving Many-to-Many (M:N) relationship between Users and Categories.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_category_preferences (
    user_id INT NOT NULL COMMENT 'Foreign key referencing users table',
    category_id INT NOT NULL COMMENT 'Foreign key referencing transaction_categories table',
    notification_enabled BOOLEAN DEFAULT TRUE COMMENT 'Whether user wants instant SMS/Push alert for category',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp when preference was set',
    PRIMARY KEY (user_id, category_id),
    CONSTRAINT fk_ucp_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ucp_category FOREIGN KEY (category_id) REFERENCES transaction_categories(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_ucp_user (user_id),
    INDEX idx_ucp_category (category_id)
) ENGINE=InnoDB COMMENT='Junction table resolving M:N relationship between users and categories';

-- -----------------------------------------------------------------------------
-- 4. Table: transactions
-- Main transaction table storing parsed and normalized MoMo SMS records.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique transaction record identifier',
    transaction_ref VARCHAR(50) NOT NULL UNIQUE COMMENT 'Financial transaction reference code (e.g. 76662021700)',
    sender_id INT NOT NULL COMMENT 'Foreign key referencing sender user record',
    receiver_id INT DEFAULT NULL COMMENT 'Foreign key referencing receiver user record (NULL if external/service)',
    category_id INT NOT NULL COMMENT 'Foreign key referencing category classification',
    amount DECIMAL(12,2) NOT NULL COMMENT 'Monetary value of the transaction in RWF',
    fee_charged DECIMAL(10,2) DEFAULT 0.00 COMMENT 'Service fee charged for the transaction',
    closing_balance DECIMAL(15,2) DEFAULT NULL COMMENT 'Account closing balance after transaction completed',
    timestamp DATETIME NOT NULL COMMENT 'Exact date and time transaction took place',
    status ENUM('completed', 'failed', 'pending') DEFAULT 'completed' COMMENT 'Status of the transaction',
    raw_text TEXT NOT NULL COMMENT 'Unaltered original XML/SMS message body string',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'System ingestion timestamp',
    CONSTRAINT fk_tx_sender FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_tx_receiver FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_tx_category FOREIGN KEY (category_id) REFERENCES transaction_categories(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_tx_amount CHECK (amount > 0.00),
    CONSTRAINT chk_fee_charged CHECK (fee_charged >= 0.00),
    INDEX idx_tx_ref (transaction_ref),
    INDEX idx_tx_sender (sender_id),
    INDEX idx_tx_receiver (receiver_id),
    INDEX idx_tx_category (category_id),
    INDEX idx_tx_timestamp (timestamp)
) ENGINE=InnoDB COMMENT='Main transaction records extracted and cleaned from MoMo XML';

-- -----------------------------------------------------------------------------
-- 5. Table: system_logs
-- Isolated audit and diagnostic log table for pipeline events and errors.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique log entry identifier',
    log_level ENUM('INFO', 'WARNING', 'ERROR') NOT NULL COMMENT 'Severity level of the logged event',
    module_name VARCHAR(50) NOT NULL COMMENT 'System component module (e.g. xml_parser, clean_normalize)',
    message TEXT NOT NULL COMMENT 'Detailed log message string',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp when log entry occurred',
    INDEX idx_log_level (log_level),
    INDEX idx_log_module (module_name),
    INDEX idx_log_timestamp (timestamp)
) ENGINE=InnoDB COMMENT='Audit log for tracking ETL processing events, warnings, and errors';

-- =============================================================================
-- SAMPLE DML STATEMENTS (At least 5 realistic records per table)
-- =============================================================================

-- Insert Sample Users (5 records)
INSERT INTO users (phone_number, name, user_type, wallet_balance) VALUES
('+250795963036', 'Jean de Dieu Tuyishime', 'personal', 980.00),
('+250791666666', 'Alice Mugabo', 'personal', 14500.00),
('+250790777777', 'Patrick Nzabonimana', 'personal', 3200.00),
('+250788999999', 'MTN Airtime Service', 'agent', 500000.00),
('+250791888888', 'Eric Habimana', 'personal', 12000.00);

-- Insert Sample Categories (5 records)
INSERT INTO transaction_categories (category_name, tx_type, description) VALUES
('Peer Payment', 'payment', 'Direct peer-to-peer transfer between personal accounts'),
('Wallet Transfer', 'transfer', 'Mobile wallet transfer initiated via phone number'),
('Cash In', 'deposit', 'Physical cash deposit credited to mobile wallet'),
('Airtime Top-up', 'airtime', 'Self-service airtime recharge purchase'),
('Merchant Payment', 'payment', 'Payment made to merchant for goods or services');

-- Insert Sample User Category Preferences (Junction Table - 5 records)
INSERT INTO user_category_preferences (user_id, category_id, notification_enabled) VALUES
(1, 1, TRUE),
(1, 2, TRUE),
(1, 4, FALSE),
(2, 1, TRUE),
(3, 3, TRUE);

-- Insert Sample Transactions (5 records)
INSERT INTO transactions (transaction_ref, sender_id, receiver_id, category_id, amount, fee_charged, closing_balance, timestamp, status, raw_text) VALUES
('76662021700', 2, 1, 2, 3000.00, 0.00, 3000.00, '2024-05-10 16:30:51', 'completed', 'You have received 3000 RWF from Alice Mugabo (+250791666666) on your mobile money account at 2024-05-10 16:30:51. Financial Transaction Id: 76662021700.'),
('73214484437', 1, 5, 1, 1500.00, 20.00, 1480.00, '2024-05-10 16:31:39', 'completed', 'Transferred 1500 RWF to Eric Habimana (+250791888888) at 2024-05-10 16:31:39. Fee: 20 RWF. Financial Transaction Id: 73214484437.'),
('81009923411', 3, 1, 1, 5000.00, 50.00, 8180.00, '2024-05-11 09:15:00', 'completed', 'Transferred 5000 RWF to Jean de Dieu Tuyishime (+250795963036). Financial Transaction Id: 81009923411.'),
('90211455622', 1, 4, 4, 1000.00, 0.00, 7180.00, '2024-05-11 11:20:10', 'completed', 'You bought airtime of 1000 RWF on 2024-05-11 11:20:10. Financial Transaction Id: 90211455622.'),
('99341122334', 4, 3, 3, 50000.00, 0.00, 53200.00, '2024-05-12 14:00:00', 'completed', 'Cash In of 50000 RWF received from Agent MTN Airtime Service. Financial Transaction Id: 99341122334.');

-- Insert Sample System Logs (5 records)
INSERT INTO system_logs (log_level, module_name, message) VALUES
('INFO', 'xml_parser', 'XML payload successfully parsed. Total raw records: 5'),
('INFO', 'clean_normalize', 'Normalized phone numbers to +250 international format'),
('INFO', 'categorize', 'Successfully categorized 5 transactions across 4 categories'),
('INFO', 'load_db', 'Loaded 5 transactions into MySQL database table transactions'),
('WARNING', 'dead_letter', 'Skipped 0 malformed XML elements');

-- =============================================================================
-- VERIFICATION & TESTING CRUD OPERATIONS
-- =============================================================================

-- Read: Fetch complete transaction details with sender, receiver, and category
SELECT 
    t.id AS tx_id,
    t.transaction_ref,
    s.name AS sender_name,
    s.phone_number AS sender_phone,
    COALESCE(r.name, 'External/Service') AS receiver_name,
    c.category_name,
    t.amount,
    t.fee_charged,
    t.timestamp
FROM transactions t
JOIN users s ON t.sender_id = s.id
LEFT JOIN users r ON t.receiver_id = r.id
JOIN transaction_categories c ON t.category_id = c.id
ORDER BY t.timestamp DESC;

-- Read: Aggregate total volume and count per category
SELECT 
    c.category_name,
    COUNT(t.id) AS total_count,
    SUM(t.amount) AS total_volume_rwf
FROM transaction_categories c
LEFT JOIN transactions t ON c.id = t.category_id
GROUP BY c.id, c.category_name;
