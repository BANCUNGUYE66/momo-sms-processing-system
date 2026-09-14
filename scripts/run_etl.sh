#!/usr/bin/env bash
# Execute MoMo SMS ETL pipeline
set -e

XML_PATH="${1:-data/raw/momo.xml}"

echo "Running MoMo SMS ETL Pipeline..."
python etl/run.py --xml "$XML_PATH"
