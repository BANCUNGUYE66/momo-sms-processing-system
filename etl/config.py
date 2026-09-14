import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data Paths
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "momo.xml"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "dashboard.json"
DB_PATH = DATA_DIR / "db.sqlite3"

# Logs
LOG_DIR = DATA_DIR / "logs"
ETL_LOG_PATH = LOG_DIR / "etl.log"
DEAD_LETTER_DIR = LOG_DIR / "dead_letter"

# Ensure directories exist
RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
DEAD_LETTER_DIR.mkdir(parents=True, exist_ok=True)

# Transaction Categories
CATEGORIES = {
    "TRANSFER": ["transferred to", "sent to", "transfer"],
    "RECEIVE": ["received from", "received RWF", "received cash"],
    "PAYMENT": ["paid to", "payment of", "merchant payment"],
    "CASH_OUT": ["cash power", "withdraw", "withdrawn from"],
    "AIRTIME": ["airtime", "bundle", "recharge"],
    "OTHER": []
}
