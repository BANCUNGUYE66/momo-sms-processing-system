import os
import tempfile
from etl.parse_xml import parse_momo_xml

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<smses count="1">
    <sms protocol="0" address="+250788123456" date="1620000000000" type="1" subject="null" body="You have received 15000 RWF from John." toa="null" sc_toa="null" service_center="null" read="1" status="-1" locked="0" date_sent="0" readable_date="May 3, 2021 10:00:00 AM" contact_name="John" />
</smses>
"""

def test_parse_momo_xml():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".xml") as tmp:
        tmp.write(SAMPLE_XML)
        tmp_path = tmp.name

    try:
        records = parse_momo_xml(tmp_path)
        assert len(records) == 1
        assert records[0]["address"] == "+250788123456"
        assert "15000 RWF" in records[0]["body"]
    finally:
        os.remove(tmp_path)
