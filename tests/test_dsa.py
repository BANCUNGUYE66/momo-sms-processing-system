"""Unit tests for the DSA package: XML parsing, search algorithms, and benchmarking.
"""

import json
import tempfile
from pathlib import Path

import pytest

from dsa.benchmark import benchmark_search_methods, load_dataset
from dsa.search import build_transaction_dict, dictionary_lookup, linear_search
from dsa.xml_parser import (
    convert_xml_to_json,
    extract_amount,
    extract_type_and_parties,
    parse_xml_to_dict_list,
)

SAMPLE_XML_CONTENT = """<?xml version='1.0' encoding='utf-8'?>
<smses count="3">
  <sms date="1715351458724" body="You have received 2000 RWF from Jane Smith (*********013) on your mobile money account. Balance: 2000 RWF." />
  <sms date="1715351506754" body="TxId: 73214484437. Your payment of 1,000 RWF to Samuel Carter 12845 has been completed. Fee 0 RWF." />
  <sms date="1715445936412" body="A bank deposit of 40000 RWF has been added to your account. Balance: 40400 RWF." />
</smses>
"""


@pytest.fixture
def sample_xml_file():
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".xml", delete=False, encoding="utf-8") as tf:
        tf.write(SAMPLE_XML_CONTENT)
        tf_path = Path(tf.name)
    yield tf_path
    if tf_path.exists():
        tf_path.unlink()


def test_extract_amount():
    assert extract_amount("Payment of 1,500 RWF completed") == 1500.0
    assert extract_amount("Received 2000 RWF from Alice") == 2000.0
    assert extract_amount("No currency mentioned here") is None


def test_extract_type_and_parties():
    res1 = extract_type_and_parties("You have received 2000 RWF from Jane Smith (*********013)")
    assert res1["type"] == "RECEIVED"
    assert res1["sender"] == "Jane Smith"

    res2 = extract_type_and_parties("A bank deposit of 40000 RWF has been added")
    assert res2["type"] == "DEPOSIT"
    assert res2["sender"] == "Bank"
    assert res2["receiver"] == "Own Account"


def test_parse_xml_to_dict_list(sample_xml_file):
    records = parse_xml_to_dict_list(sample_xml_file)
    assert len(records) == 3
    assert records[0]["id"] == 1
    assert records[0]["type"] == "RECEIVED"
    assert records[0]["amount"] == 2000.0
    assert records[1]["id"] == 2
    assert records[1]["type"] == "PAYMENT"
    assert records[1]["amount"] == 1000.0
    assert records[2]["id"] == 3
    assert records[2]["type"] == "DEPOSIT"
    assert records[2]["amount"] == 40000.0


def test_convert_xml_to_json(sample_xml_file):
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False, encoding="utf-8") as tf:
        out_json_path = Path(tf.name)

    try:
        records = convert_xml_to_json(sample_xml_file, out_json_path)
        assert len(records) == 3
        assert out_json_path.exists()

        with open(out_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 3
        assert data[0]["id"] == 1
    finally:
        if out_json_path.exists():
            out_json_path.unlink()


def test_linear_search():
    sample_data = [
        {"id": 1, "type": "RECEIVED", "amount": 100.0},
        {"id": 2, "type": "PAYMENT", "amount": 200.0},
        {"id": 3, "type": "TRANSFER", "amount": 300.0},
    ]

    record, iterations = linear_search(sample_data, 2)
    assert record is not None
    assert record["id"] == 2
    assert iterations == 2

    missing, iterations_missing = linear_search(sample_data, 99)
    assert missing is None
    assert iterations_missing == 3


def test_dictionary_lookup():
    sample_data = [
        {"id": 1, "type": "RECEIVED", "amount": 100.0},
        {"id": 2, "type": "PAYMENT", "amount": 200.0},
        {"id": 3, "type": "TRANSFER", "amount": 300.0},
    ]

    tx_dict = build_transaction_dict(sample_data)
    assert len(tx_dict) == 3

    record, ops = dictionary_lookup(tx_dict, 3)
    assert record is not None
    assert record["id"] == 3
    assert ops == 1

    missing, ops_missing = dictionary_lookup(tx_dict, 99)
    assert missing is None
    assert ops_missing == 1


def test_search_parity(sample_xml_file):
    records = parse_xml_to_dict_list(sample_xml_file)
    tx_dict = build_transaction_dict(records)

    for target_id in [1, 2, 3, 99]:
        lin_res, _ = linear_search(records, target_id)
        dict_res, _ = dictionary_lookup(tx_dict, target_id)
        assert lin_res == dict_res


def test_benchmark_execution(sample_xml_file):
    records = parse_xml_to_dict_list(sample_xml_file)
    summary = benchmark_search_methods(records, sample_ids=[1, 2, 3, 99], repetitions=10)

    assert summary["dataset_size"] == 3
    assert summary["sample_size"] == 4
    assert "avg_linear_time_us" in summary
    assert "avg_dict_time_us" in summary
    assert len(summary["individual_results"]) == 4
