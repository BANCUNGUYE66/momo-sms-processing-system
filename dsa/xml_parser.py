"""XML Parser and JSON Exporter for MoMo SMS records.

Parses raw XML files containing <sms> nodes into structured JSON objects
(list of dictionaries) with extracted fields: id, type, amount, sender,
receiver, timestamp, and raw_text.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

DEFAULT_XML_PATH = Path("data/raw/modified_sms_v2.xml")
DEFAULT_JSON_OUTPUT = Path("data/processed/transactions.json")

# Regular expression rules for transaction type classification and entity extraction
_TYPE_PATTERNS = [
    (re.compile(r"received .*?from (?P<sender>[A-Za-z .'-]+?)\s*\(", re.IGNORECASE), "RECEIVED"),
    (re.compile(r"bank deposit of", re.IGNORECASE), "DEPOSIT"),
    (re.compile(r"transferred to (?P<receiver>[A-Za-z .'-]+?)\s*\(", re.IGNORECASE), "TRANSFER"),
    (re.compile(r"payment of [\d,]+\s*RWF to Airtime", re.IGNORECASE), "AIRTIME"),
    (re.compile(r"payment of [\d,]+\s*RWF to (?P<receiver>[A-Za-z .'-]+?)\s*\d", re.IGNORECASE), "PAYMENT"),
    (re.compile(r"transaction of [\d,]+\s*RWF by (?P<sender>[A-Za-z .'-]+?)\s+on your MOMO account", re.IGNORECASE), "PAYMENT"),
]

_AMOUNT_RE = re.compile(r"([\d,]+)\s*RWF", re.IGNORECASE)


def extract_amount(body: str) -> Optional[float]:
    """Extracts monetary amount in RWF from the SMS body."""
    match = _AMOUNT_RE.search(body)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def extract_type_and_parties(body: str) -> Dict[str, Optional[str]]:
    """Extracts transaction type, sender, and receiver from the SMS body."""
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


def normalize_timestamp(date_ms: str) -> str:
    """Converts millisecond epoch timestamp string into ISO 8601 format."""
    try:
        if date_ms and date_ms.isdigit():
            return datetime.fromtimestamp(int(date_ms) / 1000.0).isoformat()
    except Exception:
        pass
    return datetime.now().isoformat()


def parse_xml_to_dict_list(xml_path: Path | str) -> List[Dict[str, Any]]:
    """Parses an XML file containing <sms> elements into a list of transaction dictionaries.

    Args:
        xml_path: Path to the XML file.

    Returns:
        List of transaction dictionaries.
    """
    path = Path(xml_path)
    if not path.exists():
        raise FileNotFoundError(f"XML dataset file not found: {path}")

    try:
        tree = ET.parse(str(path))
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML syntax in file {path}: {e}") from e

    transactions: List[Dict[str, Any]] = []
    # Search for all <sms> elements anywhere in the tree
    sms_elements = root.findall(".//sms")
    if not sms_elements:
        # Fallback to direct children if tree structure differs
        sms_elements = list(root)

    for index, sms in enumerate(sms_elements, start=1):
        body = sms.get("body", "")
        info = extract_type_and_parties(body)
        transactions.append({
            "id": index,
            "type": info["type"],
            "amount": extract_amount(body),
            "sender": info["sender"],
            "receiver": info["receiver"],
            "timestamp": normalize_timestamp(sms.get("date", "")),
            "raw_text": body.strip(),
        })

    return transactions


def convert_xml_to_json(
    xml_path: Path | str = DEFAULT_XML_PATH,
    output_json_path: Path | str = DEFAULT_JSON_OUTPUT
) -> List[Dict[str, Any]]:
    """Parses XML transaction dataset and exports the parsed records into a formatted JSON file.

    Args:
        xml_path: Path to input XML dataset.
        output_json_path: Target path for the JSON export file.

    Returns:
        The list of parsed transaction dictionaries.
    """
    xml_p = Path(xml_path)
    json_p = Path(output_json_path)

    transactions = parse_xml_to_dict_list(xml_p)

    json_p.parent.mkdir(parents=True, exist_ok=True)
    with open(json_p, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2, ensure_ascii=False)

    print(f"[XML Parser] Successfully parsed {len(transactions)} records from '{xml_p}' -> '{json_p}'")
    return transactions


if __name__ == "__main__":
    input_xml = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XML_PATH
    output_json = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_JSON_OUTPUT
    convert_xml_to_json(input_xml, output_json)
