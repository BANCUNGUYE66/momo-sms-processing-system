# MoMo SMS Data Processing — Project Context

## What this project is
An enterprise-style pipeline that parses Mobile Money (MoMo) SMS transaction exports (XML), cleans/normalizes/categorizes them, stores them in SQLite, and displays them on a static web dashboard (with an optional FastAPI backend). Built as a team assignment (Aimable: frontend/lead, Richard: ETL, Jean de Dieu: architecture/QA, Eloi: database).

## Data flow
```
data/raw/momo.xml -> etl/parse_xml.py -> etl/clean_normalize.py -> etl/categorize.py
    -> etl/load_db.py (data/db.sqlite3) + data/processed/dashboard.json
    -> api/app.py (FastAPI, optional) -> index.html + web/chart_handler.js (Chart.js dashboard)
```

## Structure & key files
- `etl/config.py` — central paths (`data/raw/momo.xml`, `data/processed/dashboard.json`, `data/db.sqlite3`, `data/logs/etl.log`) and `CATEGORIES` keyword map (TRANSFER, RECEIVE, PAYMENT, CASH_OUT, AIRTIME, OTHER).
- `etl/parse_xml.py` — `parse_momo_xml()` reads `<sms>` nodes via stdlib `xml.etree.ElementTree`; returns `[]` and logs on missing file/parse errors (never raises).
- `etl/clean_normalize.py` — `normalize_phone_number` (-> `+250...`), `extract_amount` (regex for RWF/FRW amounts), `normalize_date` (ms epoch -> ISO), `clean_record`.
- `etl/categorize.py` — `categorize_transaction(text)`: case-insensitive keyword match against `CATEGORIES`.
- `etl/load_db.py` — creates/loads a single `transactions` table (id, sender, timestamp, amount, category, raw_text, created_at) in SQLite.
- `etl/run.py` — CLI orchestrator: parse -> clean -> categorize -> load DB -> export `dashboard.json`. Run via `scripts/run_etl.sh [xml_path]`.
- `api/app.py`, `api/db.py`, `api/schemas.py` — minimal FastAPI exposing `GET /transactions` and `GET /analytics`, reading directly from SQLite.
- `index.html` + `web/chart_handler.js` + `web/styles.css` — static dashboard (Chart.js CDN); fetches `data/processed/dashboard.json` and falls back to hardcoded sample data if that fetch fails. Serve via `scripts/serve_frontend.sh [port]`.
- `tests/` — pytest unit tests for `parse_xml`, `clean_normalize`, `categorize` only (no tests yet for `load_db.py` or the API).

## Conventions
- Python stdlib is preferred in ETL code (`ElementTree`, `re`, `datetime`) even though `requirements.txt` lists `lxml`/`python-dateutil`/`python-dotenv` — those are currently unused.
- Amounts are in RWF; phone numbers normalize to `+250XXXXXXXXX`.
- Virtualenv lives at `.venv/`; activate with `source .venv/bin/activate`.

## Known gaps (as of last review)
- `data/raw/` only has a `.gitkeep` — no real `momo.xml` sample is committed, so a full ETL run currently yields 0 records.
- `data/db.sqlite3` doesn't exist until the ETL pipeline is run once.
- No tests for `etl/load_db.py` or `api/app.py`.
