"""In-memory transaction store for the plain REST API.

Seeds itself from the raw MoMo SMS XML dataset. This parser is intentionally
self-contained (kept separate from etl/ and the upcoming dsa/ module) so the
REST API can be developed, tested, and reviewed independently. Once the
dedicated dsa/ parsing module produces a canonical JSON export, this loader
can be pointed at that file instead.
"""
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

from api.rest_config import XML_DATA_PATH

# Ordered (pattern, type) rules; first pattern that matches the SMS body wins.
_TYPE_PATTERNS = [
    (re.compile(r"received .*?from (?P<sender>[A-Za-z .'-]+?)\s*\(", re.IGNORECASE), "RECEIVED"),
    (re.compile(r"bank deposit of", re.IGNORECASE), "DEPOSIT"),
    (re.compile(r"transferred to (?P<receiver>[A-Za-z .'-]+?)\s*\(", re.IGNORECASE), "TRANSFER"),
    (re.compile(r"payment of [\d,]+\s*RWF to Airtime", re.IGNORECASE), "AIRTIME"),
    (re.compile(r"payment of [\d,]+\s*RWF to (?P<receiver>[A-Za-z .'-]+?)\s*\d", re.IGNORECASE), "PAYMENT"),
    (re.compile(r"transaction of [\d,]+\s*RWF by (?P<sender>[A-Za-z .'-]+?)\s+on your MOMO account", re.IGNORECASE), "PAYMENT"),
]

_AMOUNT_RE = re.compile(r"([\d,]+)\s*RWF", re.IGNORECASE)


def _extract_amount(body: str) -> Optional[float]:
    match = _AMOUNT_RE.search(body)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _extract_type_and_parties(body: str) -> Dict[str, Optional[str]]:
    for pattern, tx_type in _TYPE_PATTERNS:
        match = pattern.search(body)
        if match:
            groups = match.groupdict()
            sender = groups.get("sender", "").strip() if groups.get("sender") else None
            receiver = groups.get("receiver", "").strip() if groups.get("receiver") else None
            if tx_type == "RECEIVED":
                receiver = "Own Account"
            elif tx_type == "DEPOSIT":
                sender, receiver = "Bank", "Own Account"
            elif tx_type == "AIRTIME":
                sender, receiver = "Own Account", "Airtime"
            elif tx_type == "TRANSFER" and sender is None:
                sender = "Own Account"
            elif tx_type == "PAYMENT" and sender is None and receiver:
                sender = "Own Account"
            elif tx_type == "PAYMENT" and receiver is None and sender:
                receiver = "Own Account"
            return {"type": tx_type, "sender": sender, "receiver": receiver}
    return {"type": "OTHER", "sender": None, "receiver": None}


def _normalize_timestamp(date_ms: str) -> str:
    try:
        if date_ms and date_ms.isdigit():
            return datetime.fromtimestamp(int(date_ms) / 1000.0).isoformat()
    except Exception:
        pass
    return datetime.now().isoformat()


def parse_transactions_from_xml(xml_path: Path) -> List[Dict[str, Any]]:
    """Parses <sms> nodes from the MoMo XML export into transaction dicts."""
    path = Path(xml_path)
    if not path.exists():
        return []

    transactions: List[Dict[str, Any]] = []
    try:
        root = ET.parse(str(path)).getroot()
    except ET.ParseError:
        return []

    for next_id, sms in enumerate(root.findall(".//sms"), start=1):
        body = sms.get("body", "")
        info = _extract_type_and_parties(body)
        transactions.append({
            "id": next_id,
            "type": info["type"],
            "amount": _extract_amount(body),
            "sender": info["sender"],
            "receiver": info["receiver"],
            "timestamp": _normalize_timestamp(sms.get("date", "")),
            "raw_text": body.strip(),
        })
    return transactions


class TransactionStore:
    """Thread-safe CRUD store keyed by id for O(1) lookups."""

    def __init__(self, xml_path: Path = XML_DATA_PATH):
        self._lock = threading.Lock()
        seed = parse_transactions_from_xml(xml_path)
        self._by_id: Dict[int, Dict[str, Any]] = {tx["id"]: tx for tx in seed}
        self._next_id = (max(self._by_id.keys(), default=0)) + 1

    def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        with self._lock:
            items = [self._by_id[key] for key in sorted(self._by_id.keys())]
        if offset:
            items = items[offset:]
        if limit is not None:
            items = items[:limit]
        return items

    def get(self, tx_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._by_id.get(tx_id)

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            tx_id = self._next_id
            self._next_id += 1
            record = {
                "id": tx_id,
                "type": data.get("type", "OTHER"),
                "amount": data.get("amount"),
                "sender": data.get("sender"),
                "receiver": data.get("receiver"),
                "timestamp": data.get("timestamp") or datetime.now().isoformat(),
                "raw_text": data.get("raw_text", ""),
            }
            self._by_id[tx_id] = record
            return record

    def update(self, tx_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            existing = self._by_id.get(tx_id)
            if existing is None:
                return None
            for field in ("type", "amount", "sender", "receiver", "timestamp", "raw_text"):
                if field in data:
                    existing[field] = data[field]
            return existing

    def delete(self, tx_id: int) -> bool:
        with self._lock:
            return self._by_id.pop(tx_id, None) is not None


store = TransactionStore()
