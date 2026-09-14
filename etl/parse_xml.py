import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def parse_momo_xml(xml_path: str) -> List[Dict[str, Any]]:
    """
    Parses MoMo SMS XML data and extracts raw message records.
    Handles missing files and parsing errors gracefully.
    """
    path = Path(xml_path)
    if not path.exists():
        logger.warning(f"XML file not found at {xml_path}. Returning empty list.")
        return []

    records = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for sms in root.findall(".//sms"):
            record = {
                "address": sms.get("address", ""),
                "date": sms.get("date", ""),
                "type": sms.get("type", ""),
                "body": sms.get("body", ""),
                "readable_date": sms.get("readable_date", "")
            }
            records.append(record)

        logger.info(f"Successfully parsed {len(records)} SMS records from {xml_path}")
    except ET.ParseError as e:
        logger.error(f"XML Parse Error in {xml_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while parsing XML: {e}")

    return records
