import argparse
import json
import logging
from etl.config import RAW_DATA_PATH, PROCESSED_DATA_PATH, DB_PATH, ETL_LOG_PATH
from etl.parse_xml import parse_momo_xml
from etl.clean_normalize import clean_record
from etl.categorize import categorize_transaction
from etl.load_db import load_transactions

# Configure Logging
logging.basicConfig(
    filename=str(ETL_LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_etl(xml_file: str):
    """Executes full ETL pipeline: Parse -> Clean -> Categorize -> Load -> Export JSON."""
    logger.info("Starting ETL Pipeline execution...")
    print(f"Reading raw SMS data from {xml_file}...")

    raw_records = parse_momo_xml(xml_file)
    processed_records = []

    for raw in raw_records:
        cleaned = clean_record(raw)
        cleaned["category"] = categorize_transaction(cleaned["raw_text"])
        processed_records.append(cleaned)

    # Load to DB
    inserted_count = load_transactions(DB_PATH, processed_records)

    # Export for Frontend
    with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(processed_records, f, indent=2)

    logger.info(f"ETL completed successfully. Total processed: {len(processed_records)}")
    print(f"ETL Pipeline completed. Processed {len(processed_records)} records -> Exported to {PROCESSED_DATA_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MoMo SMS Data Processing ETL Pipeline")
    parser.add_argument("--xml", type=str, default=str(RAW_DATA_PATH), help="Path to input momo.xml file")
    args = parser.parse_args()

    run_etl(args.xml)
