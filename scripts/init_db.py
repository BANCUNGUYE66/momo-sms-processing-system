#!/usr/bin/env python3
"""Create (and optionally seed) the SQLite database for the MoMo SMS system."""

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from etl.config import DB_PATH  # noqa: E402
from etl.load_db import init_db, seed_db  # noqa: E402


def _print_summary(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        print(f"SQLite database: {db_path}")
        print("Tables:")
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) AS n FROM {table['name']}").fetchone()["n"]
            print(f"  - {table['name']}: {count} row(s)")
        views = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
        ).fetchall()
        if views:
            print("Views:")
            for view in views:
                print(f"  - {view['name']}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the MoMo SQLite database")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Load sample users, transactions, preferences, and logs after creating the schema",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(DB_PATH),
        help="Path to the SQLite file (default: data/db.sqlite3)",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if args.seed:
        seed_db(db_path)
        print("Schema applied and sample data loaded.")
    else:
        conn = init_db(db_path)
        conn.close()
        print("Schema applied.")

    _print_summary(db_path)


if __name__ == "__main__":
    main()
