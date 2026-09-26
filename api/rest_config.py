"""Configuration for the plain-Python (http.server) REST API."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Dataset used to seed the in-memory transaction store.
XML_DATA_PATH = Path(os.getenv("MODIFIED_XML_PATH", BASE_DIR / "data" / "raw" / "modified_sms_v2.xml"))

# Basic Auth credentials (override via environment variables in real deployments).
API_USERNAME = os.getenv("API_USERNAME", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "momo1234")

# Distinct env var names from the FastAPI app's API_HOST/API_PORT so both can run together.
API_HOST = os.getenv("REST_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("REST_API_PORT", "8001"))
