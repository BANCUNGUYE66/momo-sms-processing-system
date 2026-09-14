from etl.config import CATEGORIES

def categorize_transaction(text: str) -> str:
    """Categorizes a transaction based on SMS content keywords."""
    text_lower = text.lower()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return "OTHER"
