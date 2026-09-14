from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from api.db import get_db_connection
from api.schemas import TransactionSchema, AnalyticsSummary

app = FastAPI(
    title="MoMo SMS Data Processing API",
    description="Minimal API for querying processed Mobile Money SMS transactions and analytics.",
    version="1.0.0"
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to MoMo SMS Data Processing API", "status": "online"}

@app.get("/transactions", response_model=List[TransactionSchema])
def get_transactions(limit: int = 100, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/analytics", response_model=AnalyticsSummary)
def get_analytics():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM transactions")
    total_count, total_volume = cursor.fetchone()

    cursor.execute("SELECT category, COUNT(*) FROM transactions GROUP BY category")
    cat_rows = cursor.fetchall()
    categories = {row[0]: row[1] for row in cat_rows}

    conn.close()
    return AnalyticsSummary(
        total_transactions=total_count,
        total_volume=total_volume,
        categories=categories
    )
