# AI Usage & Transparency Log

**Project**: MoMo SMS Processing System  
**Contributor**: Jean de Dieu Tuyishime (Jtuyishime6)  
**Role**: Architecture / QA  
**Date**: September 15, 2026  

---

## 1. Compliance Statement
This log records all AI interactions conducted in accordance with the course **AI Usage Policy**. All domain business logic, relational database schemas, and architectural designs were authored directly to satisfy project requirements. AI tools were strictly utilized for permitted syntax verification, formatting checks, and documentation grammar polishing.

---

## 2. Log of AI Interactions

| Date | Tool | Permitted Purpose | Query / Input Description | Output / Action Taken |
| :--- | :--- | :--- | :--- | :--- |
| **2026-09-14** | AI Assistant | Syntax & Format Checking | Checking PlantUML ERD diagram syntax formatting | Corrected `@startuml` block structure to resolve PlantUML renderer syntax warning |
| **2026-09-15** | AI Assistant | Documentation Grammar & Syntax | Reviewing 250–300 word ERD design rationale text for grammatical clarity | Polished technical explanation phrasing and verified word count (257 words) |
| **2026-09-15** | AI Assistant | MySQL Best Practices Verification | Researching MySQL 8.0 `COMMENT` syntax and `CHECK` constraint syntax | Confirmed `ENGINE=InnoDB` and `CONSTRAINT chk_... CHECK (...)` syntax compliance |
| **2026-09-15** | AI Assistant | Git Command Syntax Verification | Checking Git command syntax for local exclude (`.git/info/exclude`) and branch management | Applied `.git/info/exclude` configuration for local file exclusion |

---

## 3. Attribution & Code Marking
- **SQL DDL / DML (`database/database_setup.sql`)**: Author-designed 3NF relational schema. AI used strictly for verifying MySQL constraint syntax.
- **JSON Schemas (`examples/json_schemas.json`)**: Author-designed serialization mappings. AI used for JSON syntax formatting validation.
- **ERD Design (`docs/erd_diagram.pdf`)**: Author-designed entity relationships. AI used for verifying PlantUML rendering syntax.
