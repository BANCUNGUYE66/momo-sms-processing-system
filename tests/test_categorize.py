from etl.categorize import categorize_transaction

def test_categorize_transaction():
    assert categorize_transaction("Transferred to 0788123456") == "TRANSFER"
    assert categorize_transaction("You received RWF 5000") == "RECEIVE"
    assert categorize_transaction("Paid to MTN airtime bundle") in ["PAYMENT", "AIRTIME"]
    assert categorize_transaction("Random text message") == "OTHER"
