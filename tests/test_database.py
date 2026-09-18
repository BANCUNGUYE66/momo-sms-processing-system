import sqlite3
from pathlib import Path

import pytest

from etl.load_db import init_db, load_transactions, seed_db

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
REQUIRED_TABLES = {
    "users",
    "transaction_categories",
    "user_category_preferences",
    "transactions",
    "system_logs",
}


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "momo.sqlite3"


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def test_schema_file_defines_required_tables():
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    for table in REQUIRED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
    assert "FOREIGN KEY" in sql
    assert "CHECK" in sql
    assert "CREATE VIEW IF NOT EXISTS v_transaction_details" in sql


def test_init_db_creates_tables_and_default_categories(db_path: Path):
    init_db(db_path)
    conn = _connect(db_path)
    try:
        names = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        assert REQUIRED_TABLES <= names

        codes = {
            row["code"]
            for row in conn.execute("SELECT code FROM transaction_categories")
        }
        assert {"TRANSFER", "RECEIVE", "PAYMENT", "CASH_OUT", "AIRTIME", "OTHER"} <= codes

        view = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name='v_transaction_details'"
        ).fetchone()
        assert view is not None
    finally:
        conn.close()


def test_seed_db_loads_related_sample_rows(db_path: Path):
    seed_db(db_path)
    conn = _connect(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] >= 5
        assert conn.execute("SELECT COUNT(*) AS n FROM transactions").fetchone()["n"] >= 5
        assert conn.execute("SELECT COUNT(*) AS n FROM user_category_preferences").fetchone()["n"] >= 5
        assert conn.execute("SELECT COUNT(*) AS n FROM system_logs").fetchone()["n"] >= 5

        joined = conn.execute(
            """
            SELECT t.transaction_ref, s.name AS sender_name, c.code
            FROM transactions t
            JOIN users s ON s.id = t.sender_id
            JOIN transaction_categories c ON c.id = t.category_id
            WHERE t.transaction_ref = '76662021700'
            """
        ).fetchone()
        assert joined is not None
        assert joined["sender_name"] == "Aimable Bancunguye"
        assert joined["code"] == "RECEIVE"
    finally:
        conn.close()


def test_foreign_key_rejects_unknown_category(db_path: Path):
    init_db(db_path)
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT INTO users (phone_number, name) VALUES (?, ?)",
            ("+250788000000", "Test User"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO transactions (
                    sender_id, category_id, amount, timestamp, raw_text
                ) VALUES (1, 999, 1000, '2024-05-10 10:00:00', 'invalid category fk')
                """
            )
            conn.commit()
    finally:
        conn.close()


def test_check_constraint_rejects_non_positive_amount(db_path: Path):
    seed_db(db_path)
    conn = _connect(db_path)
    try:
        sender_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()["id"]
        category_id = conn.execute("SELECT id FROM transaction_categories LIMIT 1").fetchone()["id"]
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO transactions (
                    sender_id, category_id, amount, timestamp, raw_text
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (sender_id, category_id, 0, "2024-05-10 10:00:00", "zero amount"),
            )
            conn.commit()
    finally:
        conn.close()


def test_load_transactions_maps_etl_records_to_relations(db_path: Path):
    records = [
        {
            "sender": "+250788123456",
            "timestamp": "2024-05-10T16:30:51",
            "amount": 15000.0,
            "category": "RECEIVE",
            "raw_text": "You have received 15000 RWF from John.",
        },
        {
            "sender": "+250788123456",
            "timestamp": "2024-05-10T16:31:00",
            "amount": None,
            "category": "OTHER",
            "raw_text": "This SMS has no amount.",
        },
    ]

    inserted = load_transactions(db_path, records)
    assert inserted == 1

    conn = _connect(db_path)
    try:
        row = conn.execute("SELECT * FROM v_transaction_details").fetchone()
        assert row["sender"] == "+250788123456"
        assert row["category"] == "RECEIVE"
        assert row["amount"] == 15000.0

        warning = conn.execute(
            "SELECT COUNT(*) AS n FROM system_logs WHERE log_level = 'WARNING'"
        ).fetchone()["n"]
        assert warning >= 1
    finally:
        conn.close()
