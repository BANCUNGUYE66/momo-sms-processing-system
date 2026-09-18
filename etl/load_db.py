import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from etl.config import BASE_DIR, CATEGORIES

logger = logging.getLogger(__name__)

SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
SEED_PATH = BASE_DIR / "database" / "seed.sql"

TX_TYPE_BY_CODE = {
    "TRANSFER": "transfer",
    "RECEIVE": "deposit",
    "PAYMENT": "payment",
    "CASH_OUT": "withdrawal",
    "AIRTIME": "airtime",
    "OTHER": "other",
}

CATEGORY_NAME_BY_CODE = {
    "TRANSFER": "Wallet Transfer",
    "RECEIVE": "Incoming Transfer",
    "PAYMENT": "Merchant Payment",
    "CASH_OUT": "Cash Out",
    "AIRTIME": "Airtime Top-up",
    "OTHER": "Uncategorized",
}


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys and WAL enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _has_legacy_flat_schema(conn: sqlite3.Connection) -> bool:
    """Detect the original single-table transactions schema (sender TEXT, no FKs)."""
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='transactions'"
    ).fetchone()
    if not exists:
        return False
    columns = {row[1] for row in conn.execute("PRAGMA table_info(transactions)")}
    return "sender_id" not in columns


def init_db(db_path: Path) -> sqlite3.Connection:
    """Create tables, indexes, default categories, and the analytics view."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"SQLite schema not found: {SCHEMA_PATH}")

    conn = connect(db_path)
    if _has_legacy_flat_schema(conn):
        logger.warning("Replacing legacy single-table SQLite schema with relational schema")
        conn.close()
        db_path.unlink(missing_ok=True)
        conn = connect(db_path)

    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    _ensure_known_categories(conn)
    conn.commit()
    logger.info("Initialized SQLite schema at %s", db_path)
    return conn


def seed_db(db_path: Path) -> None:
    """Load sample users, preferences, transactions, and logs."""
    if not SEED_PATH.exists():
        raise FileNotFoundError(f"SQLite seed file not found: {SEED_PATH}")

    conn = init_db(db_path)
    try:
        existing_users = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        if existing_users:
            logger.info("Sample data already present in %s; skipping seed", db_path)
            return
        conn.executescript(SEED_PATH.read_text(encoding="utf-8"))
        conn.commit()
        logger.info("Loaded sample data into %s", db_path)
    finally:
        conn.close()


def _ensure_known_categories(conn: sqlite3.Connection) -> None:
    """Keep lookup rows in sync with etl/config.py CATEGORIES."""
    for code in CATEGORIES:
        conn.execute(
            """
            INSERT INTO transaction_categories (code, category_name, tx_type, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(code) DO NOTHING
            """,
            (
                code,
                CATEGORY_NAME_BY_CODE.get(code, code.title()),
                TX_TYPE_BY_CODE.get(code, "other"),
                f"Auto-registered category for ETL code {code}",
            ),
        )


def _log_event(conn: sqlite3.Connection, level: str, module_name: str, message: str) -> None:
    conn.execute(
        """
        INSERT INTO system_logs (log_level, module_name, message)
        VALUES (?, ?, ?)
        """,
        (level, module_name, message),
    )


def get_or_create_user(
    conn: sqlite3.Connection,
    phone_number: str,
    name: Optional[str] = None,
    user_type: str = "personal",
) -> int:
    """Return the users.id for a phone number, inserting the row if needed."""
    normalized = (phone_number or "").strip() or "UNKNOWN"
    row = conn.execute(
        "SELECT id FROM users WHERE phone_number = ?",
        (normalized,),
    ).fetchone()
    if row:
        return int(row["id"])

    display_name = (name or "").strip() or normalized
    cursor = conn.execute(
        """
        INSERT INTO users (phone_number, name, user_type)
        VALUES (?, ?, ?)
        """,
        (normalized, display_name, user_type),
    )
    return int(cursor.lastrowid)


def get_category_id(conn: sqlite3.Connection, code: str) -> int:
    """Resolve an ETL category code to transaction_categories.id."""
    lookup = (code or "OTHER").strip().upper()
    row = conn.execute(
        "SELECT id FROM transaction_categories WHERE code = ?",
        (lookup,),
    ).fetchone()
    if row:
        return int(row["id"])

    cursor = conn.execute(
        """
        INSERT INTO transaction_categories (code, category_name, tx_type, description)
        VALUES (?, ?, ?, ?)
        """,
        (
            lookup,
            CATEGORY_NAME_BY_CODE.get(lookup, lookup.title()),
            TX_TYPE_BY_CODE.get(lookup, "other"),
            f"Inserted from ETL for unknown code {lookup}",
        ),
    )
    return int(cursor.lastrowid)


def _extract_transaction_row(tx: Dict[str, Any]) -> Optional[Tuple[Any, ...]]:
    amount = tx.get("amount")
    try:
        amount_value = float(amount) if amount is not None else None
    except (TypeError, ValueError):
        amount_value = None

    if amount_value is None or amount_value <= 0:
        return None

    fee = tx.get("fee_charged") or 0.00
    try:
        fee_value = float(fee)
    except (TypeError, ValueError):
        fee_value = 0.00

    return (
        tx.get("transaction_ref"),
        amount_value,
        max(fee_value, 0.00),
        tx.get("closing_balance"),
        tx.get("timestamp"),
        tx.get("status") or "completed",
        (tx.get("raw_text") or "").strip(),
    )


def load_transactions(db_path: Path, transactions: List[Dict[str, Any]]) -> int:
    """Insert cleaned ETL records into the relational SQLite schema."""
    conn = init_db(db_path)
    inserted = 0
    skipped = 0

    try:
        for tx in transactions:
            payload = _extract_transaction_row(tx)
            if payload is None:
                skipped += 1
                _log_event(
                    conn,
                    "WARNING",
                    "load_db",
                    f"Skipped SMS with invalid amount: {(tx.get('raw_text') or '')[:120]}",
                )
                continue

            sender_id = get_or_create_user(conn, tx.get("sender") or "UNKNOWN")
            receiver_phone = tx.get("receiver")
            receiver_id = get_or_create_user(conn, receiver_phone) if receiver_phone else None
            category_id = get_category_id(conn, tx.get("category") or "OTHER")

            transaction_ref, amount, fee, closing_balance, timestamp, status, raw_text = payload

            try:
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO transactions (
                        transaction_ref, sender_id, receiver_id, category_id,
                        amount, fee_charged, closing_balance, timestamp, status, raw_text
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        transaction_ref,
                        sender_id,
                        receiver_id,
                        category_id,
                        amount,
                        fee,
                        closing_balance,
                        timestamp,
                        status,
                        raw_text,
                    ),
                )
                if cursor.rowcount:
                    inserted += 1
            except sqlite3.IntegrityError as exc:
                skipped += 1
                _log_event(conn, "ERROR", "load_db", f"Integrity error while inserting transaction: {exc}")

        _log_event(
            conn,
            "INFO",
            "load_db",
            f"Loaded {inserted} transactions into SQLite ({skipped} skipped) at {db_path}",
        )
        conn.commit()
        logger.info("Loaded %s transactions into SQLite database at %s", inserted, db_path)
        return inserted
    finally:
        conn.close()
