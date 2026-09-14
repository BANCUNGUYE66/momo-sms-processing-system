import sqlite3
from etl.config import DB_PATH

def get_db_connection():
    """Returns a SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn
