from etl.clean_normalize import normalize_phone_number, extract_amount, clean_record

def test_normalize_phone_number():
    assert normalize_phone_number("250788123456") == "+250788123456"
    assert normalize_phone_number("0788123456") == "+250788123456"
    assert normalize_phone_number("+250788123456") == "+250788123456"

def test_extract_amount():
    assert extract_amount("You received 25,000 RWF from Jane.") == 25000.0
    assert extract_amount("Payment of RWF 5000 to Merchant.") == 5000.0
    assert extract_amount("No amount here") is None

def test_clean_record():
    raw = {
        "address": "0788123456",
        "date": "1620000000000",
        "body": "Transferred 1000 RWF to Alice."
    }
    cleaned = clean_record(raw)
    assert cleaned["sender"] == "+250788123456"
    assert cleaned["amount"] == 1000.0
    assert cleaned["raw_text"] == "Transferred 1000 RWF to Alice."
