from pydantic import BaseModel
from typing import Optional, List

class TransactionSchema(BaseModel):
    id: int
    sender: Optional[str] = None
    timestamp: str
    amount: Optional[float] = None
    category: str
    raw_text: str

class AnalyticsSummary(BaseModel):
    total_transactions: int
    total_volume: float
    categories: dict
