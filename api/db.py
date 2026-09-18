from etl.load_db import init_db
from etl.config import DB_PATH


def get_db_connection():
    """Return a SQLite connection with the relational schema applied."""
    return init_db(DB_PATH)
