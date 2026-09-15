# MoMo SMS Processing System — Database Design Document

**Course**: Enterprise Software Development  
**Project**: MoMo SMS Data Processing & Analytics System  
**Document**: Database Design & Implementation Report  
**Author**: Jean de Dieu Tuyishime (Architecture / QA)  
**Team Lead**: Aimable  
**Team Members**: Aimable, Richard, Jean de Dieu Tuyishime, Eloi  

---

## 1. Executive Overview

This document presents the complete database design and implementation for the Mobile Money (MoMo) SMS Processing System. The database translates raw XML mobile money transaction logs into a 3NF-compliant relational database schema using MySQL 8.0. The architecture is optimized for high-throughput transaction ingestion, referential integrity, automated reporting, and analytical data visualization.

---

## 2. Section 1: Entity Relationship Diagram (ERD) & Design Rationale

### 2.1 Entity Relationship Diagram (ERD)
The system ERD consists of five core domain entities:
1. `Users` (Wallet holders, customers, merchants, agents)
2. `Transaction_Categories` (Classification rules for MoMo payments)
3. `User_Category_Preferences` (Junction entity resolving Many-to-Many M:N relationship)
4. `Transactions` (Central record of parsed financial transactions)
5. `System_Logs` (Isolated audit log tracking pipeline operations)

*(Embed your ERD Diagram image `docs/erd_diagram.pdf` / `docs/erd_diagram.png` here)*

### 2.2 Design Rationale & Justification (257 Words)

The MoMo SMS Data Processing System database architecture is designed to translate unstructured Mobile Money SMS transaction records into a 3NF-compliant relational database. The schema prioritizes data normalization, referential integrity, query performance, and analytical scalability.

1. **Entity Identification & Data Normalization**:
   The schema centers on four domain entities: `Users`, `Transactions`, `Transaction_Categories`, and `System_Logs`. Normalizing user details into a dedicated `Users` entity eliminates redundant sender and receiver data. Each user can participate in multiple transactions as a sender or receiver, represented through dual 1:M relationships (`sender_id` and `receiver_id` foreign keys referencing the `Users` primary key).

2. **Transaction Categorization & Analytical Aggregations**:
   Transactions are classified by linking each transaction record to a `Transaction_Categories` entity via a 1:M foreign key relationship (`category_id`). Pre-defining explicit categories (e.g., Peer Payment, Cash In, Airtime, Transfer) optimizes SQL aggregation queries, accelerates summary reporting, and ensures consistent transaction classification.

3. **Resolving Many-to-Many (M:N) Relationships**:
   To support individual user notification preferences across various transaction categories, a Many-to-Many (M:N) relationship exists between `Users` and `Transaction_Categories`. This is cleanly resolved using a dedicated junction table, `User_Category_Preferences`, featuring composite primary keys (`user_id`, `category_id`) and explicit foreign key constraints, preserving 3NF relational purity.

4. **Auditability & System Health Monitoring**:
   The `System_Logs` entity isolates operational logging, XML parsing exceptions, and dead-letter queue events from financial transaction storage. This architectural decoupling ensures high-volume diagnostic logging does not degrade transaction processing speeds while maintaining complete system auditability.

Overall, this entity-relationship design guarantees strict referential integrity, eliminates data anomalies, and provides an efficient foundation for enterprise mobile money analytics.

---

## 3. Section 2: Data Dictionary

### Table 1: `users`
Stores registered Mobile Money users, merchants, and agents.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT AUTO_INCREMENT` | `PRIMARY KEY` | Unique primary identifier for each user |
| `phone_number` | `VARCHAR(20)` | `NOT NULL, UNIQUE` | Normalized mobile phone number (`+250...`) |
| `name` | `VARCHAR(100)` | `NOT NULL` | Full display name of the account holder |
| `user_type` | `ENUM('personal', 'merchant', 'agent')` | `DEFAULT 'personal'` | Role classification of wallet holder |
| `wallet_balance` | `DECIMAL(15,2)` | `CHECK (wallet_balance >= 0.00)` | Current wallet balance in RWF |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Account registration timestamp |

---

### Table 2: `transaction_categories`
Defines transaction categories for classifying MoMo SMS payments.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT AUTO_INCREMENT` | `PRIMARY KEY` | Unique category identifier |
| `category_name` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Name of category (e.g., Peer Payment) |
| `tx_type` | `ENUM('payment', 'transfer', 'deposit', 'airtime')` | `NOT NULL` | High-level transaction type |
| `description` | `TEXT` | Optional | Category description and keyword rules |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Timestamp when category was added |

---

### Table 3: `user_category_preferences` (Junction Table)
Resolves Many-to-Many (M:N) relationship between Users and Transaction Categories.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | `INT` | `PK, FK (users.id)` | Foreign key referencing `users.id` |
| `category_id` | `INT` | `PK, FK (transaction_categories.id)` | Foreign key referencing `transaction_categories.id` |
| `notification_enabled` | `BOOLEAN` | `DEFAULT TRUE` | Alert preference toggle |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Setting creation timestamp |

---

### Table 4: `transactions`
Main transaction table storing cleaned and extracted MoMo SMS records.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT AUTO_INCREMENT` | `PRIMARY KEY` | Unique transaction identifier |
| `transaction_ref` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Reference code (e.g., `76662021700`) |
| `sender_id` | `INT` | `FK (users.id)` | Foreign key referencing sender user |
| `receiver_id` | `INT` | `FK (users.id), NULLABLE` | Foreign key referencing receiver user |
| `category_id` | `INT` | `FK (transaction_categories.id)` | Foreign key referencing category |
| `amount` | `DECIMAL(12,2)` | `CHECK (amount > 0.00)` | Monetary value in RWF |
| `fee_charged` | `DECIMAL(10,2)` | `CHECK (fee_charged >= 0.00)` | Service fee charged |
| `closing_balance` | `DECIMAL(15,2)` | Optional | Wallet balance after transaction |
| `timestamp` | `DATETIME` | `NOT NULL` | Date and time transaction took place |
| `status` | `ENUM('completed', 'failed', 'pending')` | `DEFAULT 'completed'` | Transaction execution status |
| `raw_text` | `TEXT` | `NOT NULL` | Unaltered original XML/SMS text body |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Ingestion timestamp |

---

### Table 5: `system_logs`
Audit log for tracking ETL processing events, warnings, and errors.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT AUTO_INCREMENT` | `PRIMARY KEY` | Unique log entry identifier |
| `log_level` | `ENUM('INFO', 'WARNING', 'ERROR')` | `NOT NULL` | Severity level of the logged event |
| `module_name` | `VARCHAR(50)` | `NOT NULL` | Ingestion component module |
| `message` | `TEXT` | `NOT NULL` | Detailed log message string |
| `timestamp` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Event timestamp |

---

## 4. Section 3: Security & Data Integrity Rules

1. **Referential Integrity Constraints**:
   - All relationship foreign keys use explicit cascades: `sender_id` enforces `ON DELETE RESTRICT` to preserve historical transaction records, while `receiver_id` allows `ON DELETE SET NULL`.
2. **Value Domain Rules (`CHECK` Constraints)**:
   - `CONSTRAINT chk_tx_amount CHECK (amount > 0.00)`: Restricts non-positive or negative transaction amounts.
   - `CONSTRAINT chk_fee_charged CHECK (fee_charged >= 0.00)`: Prevents negative fee calculations.
   - `CONSTRAINT chk_wallet_balance CHECK (wallet_balance >= 0.00)`: Prevents invalid negative balances.
3. **Uniqueness Rules**:
   - `transaction_ref` (`VARCHAR(50) UNIQUE`) prevents duplicate transaction entry.
   - `phone_number` (`VARCHAR(20) UNIQUE`) prevents duplicate user registration.

---

## 5. Section 4: Sample Queries & Verification Screenshots

*(Paste your 5 execution screenshots under each section below)*

### Screenshot 1: Database Table List
```sql
USE momo_sms_processing_system;
SHOW TABLES;
```
*(Insert Screenshot 1 showing the list of 5 tables)*

---

### Screenshot 2: SELECT * FROM transactions;
```sql
SELECT * FROM transactions;
```
*(Insert Screenshot 2 showing sample DML rows)*

---

### Screenshot 3: JOIN Query Result
```sql
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
```
*(Insert Screenshot 3 showing joined transaction table output)*

---

### Screenshot 4: GROUP BY Aggregation Summary
```sql
SELECT 
    c.category_name,
    COUNT(t.id) AS total_count,
    SUM(t.amount) AS total_volume_rwf
FROM transaction_categories c
LEFT JOIN transactions t ON c.id = t.category_id
GROUP BY c.id, c.category_name;
```
*(Insert Screenshot 4 showing aggregate summary table)*

---

### Screenshot 5: CHECK Constraint Error Test (`amount = -500`)
```sql
INSERT INTO transactions (transaction_ref, sender_id, receiver_id, category_id, amount, timestamp, raw_text) 
VALUES ('INVALID_TEST_REF', 1, 2, 1, -500.00, NOW(), 'Test invalid negative amount');
```
*(Insert Screenshot 5 showing MySQL Action Output error: `Error Code: 3819. Check constraint 'chk_tx_amount' is violated.`)*

---

## 6. Section 5: AI Usage & Transparency Log

### Compliance Statement
This log records AI interactions in accordance with the course **AI Usage Policy**. All domain business logic, relational database schemas, and architectural designs were authored directly to satisfy project requirements. AI tools were strictly utilized for permitted syntax verification, formatting checks, and documentation grammar polishing.

### Log of AI Interactions

| Date | Contributor | Permitted Purpose | Query / Input Description | Output / Action Taken |
| :--- | :--- | :--- | :--- | :--- |
| **2026-09-14** | Jean de Dieu | Syntax & Format Checking | Checking PlantUML ERD diagram syntax formatting | Corrected `@startuml` block structure to resolve PlantUML renderer syntax warning |
| **2026-09-15** | Jean de Dieu | Documentation Grammar & Syntax | Reviewing 250–300 word ERD design rationale text for grammatical clarity | Polished technical explanation phrasing and verified word count (257 words) |
| **2026-09-15** | Jean de Dieu | MySQL Best Practices Verification | Researching MySQL 8.0 `COMMENT` syntax and `CHECK` constraint syntax | Confirmed `ENGINE=InnoDB` and `CONSTRAINT chk_... CHECK (...)` syntax compliance |
| **2026-09-15** | Jean de Dieu | Git Command Syntax Verification | Checking Git command syntax for local exclude (`.git/info/exclude`) and branch management | Applied `.git/info/exclude` configuration for local file exclusion |

