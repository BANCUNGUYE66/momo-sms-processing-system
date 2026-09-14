import re
from datetime import datetime
from typing import Dict, Any, Optional

def normalize_phone_number(phone_str: str) -> str:
    """Normalizes phone numbers to standard format (+250...)."""
    if not phone_str:
        return ""
    digits = re.sub(r"\D", "", phone_str)
    if digits.startswith("250") and len(digits) == 12:
        return f"+{digits}"
    elif len(digits) == 9 and digits.startswith("7"):
        return f"+250{digits}"
    return phone_str.strip()

def extract_amount(body: str) -> Optional[float]:
    """Extracts monetary amount (e.g., RWF amount) from SMS body."""
    match = re.search(r"(?:RWF|FRW|amount:?)\s*([\d,]+)", body, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(",", "")
        try:
            return float(amount_str)
        except ValueError:
            return None
    return None

def normalize_date(timestamp_ms: str) -> str:
    """Converts millisecond timestamp or date string to ISO format."""
    try:
        if timestamp_ms and timestamp_ms.isdigit():
            ts = float(timestamp_ms) / 1000.0
            return datetime.fromtimestamp(ts).isoformat()
    except Exception:
        pass
    return datetime.now().isoformat()

def clean_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """Cleans and normalizes a single raw SMS record."""
    body = raw_record.get("body", "")
    return {
        "sender": normalize_phone_number(raw_record.get("address", "")),
        "timestamp": normalize_date(raw_record.get("date", "")),
        "amount": extract_amount(body),
        "raw_text": body.strip()
    }
