#!/usr/bin/env bash
# Rebuild data/processed/dashboard.json from DB or raw data
set -e

echo "Rebuilding dashboard.json..."
python etl/run.py
