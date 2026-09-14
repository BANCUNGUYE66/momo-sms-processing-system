import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    timestamp TEXT,
    amount REAL,
    category TEXT,
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def init_db(db_path: Path):
    """Initializes SQLite database and tables."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()

def load_transactions(db_path: Path, transactions: List[Dict[str, Any]]) -> int:
    """Inserts transactions into SQLite database."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    count = 0
    for tx in transactions:
        cursor.execute(
            """
            INSERT INTO transactions (sender, timestamp, amount, category, raw_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tx.get("sender"), tx.get("timestamp"), tx.get("amount"), tx.get("category"), tx.get("raw_text"))
        )
        count += 1

    conn.commit()
    conn.close()
    logger.info(f"Loaded {count} transactions into SQLite database at {db_path}")
    return count
