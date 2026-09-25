"""HTTP Basic Authentication helpers for the plain REST API.

Basic Auth is used here to satisfy the assignment requirement, but it is a
weak scheme: credentials are only base64-encoded (not encrypted) and are
resent on every request, so anyone who can see the traffic (no TLS) or read
server logs can recover the username/password. See docs/api_docs.md for a
full discussion and stronger alternatives (JWT, OAuth2).
"""
import base64
import hmac
from typing import Optional, Tuple

from api.rest_config import API_USERNAME, API_PASSWORD


def parse_basic_auth_header(header_value: Optional[str]) -> Optional[Tuple[str, str]]:
    """Decodes an 'Authorization: Basic <base64>' header into (username, password)."""
    if not header_value or not header_value.startswith("Basic "):
        return None
    encoded = header_value[len("Basic "):].strip()
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return None
    if ":" not in decoded:
        return None
    username, password = decoded.split(":", 1)
    return username, password


def is_authorized(header_value: Optional[str]) -> bool:
    """Validates an Authorization header against the configured credentials."""
    credentials = parse_basic_auth_header(header_value)
    if credentials is None:
        return False
    username, password = credentials
    # Use constant-time comparisons to avoid leaking credential info via timing.
    return hmac.compare_digest(username, API_USERNAME) and hmac.compare_digest(password, API_PASSWORD)
