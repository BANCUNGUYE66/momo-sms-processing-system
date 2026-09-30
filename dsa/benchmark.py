"""Performance Benchmarking Module for Linear Search vs Dictionary Lookup.

Measures and compares the efficiency of:
- Linear Search (scanning list of transaction dicts)
- Dictionary Lookup (hash table key lookup)

Runs performance tests across 20+ transaction IDs and prints a detailed Markdown benchmark table.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dsa.search import build_transaction_dict, dictionary_lookup, linear_search
from dsa.xml_parser import convert_xml_to_json, parse_xml_to_dict_list

DEFAULT_JSON_PATH = Path("data/processed/transactions.json")
DEFAULT_XML_PATH = Path("data/raw/modified_sms_v2.xml")


def load_dataset(
    json_path: Path = DEFAULT_JSON_PATH,
    xml_path: Path = DEFAULT_XML_PATH
) -> List[Dict[str, Any]]:
    """Loads transaction records from JSON export file or parses raw XML dataset."""
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    if xml_path.exists():
        return convert_xml_to_json(xml_path, json_path)

    raise FileNotFoundError(f"Neither '{json_path}' nor '{xml_path}' could be found.")


def benchmark_search_methods(
    transactions_list: List[Dict[str, Any]],
    sample_ids: List[int],
    repetitions: int = 1000
) -> Dict[str, Any]:
    """Runs high-precision timing benchmarks comparing Linear Search vs Dictionary Lookup.

    Args:
        transactions_list: List of transaction dictionaries.
        sample_ids: List of target transaction IDs to search for (minimum 20 recommended).
        repetitions: Number of repeated search cycles per ID for timing accuracy.

    Returns:
        Benchmark statistical summary dictionary.
    """
    transactions_dict = build_transaction_dict(transactions_list)
    results = []

    total_linear_ns = 0
    total_dict_ns = 0
    total_linear_scans = 0
    total_dict_scans = 0

    for target_id in sample_ids:
        # Benchmark Linear Search over repeated runs
        start_linear = time.perf_counter_ns()
        for _ in range(repetitions):
            record_lin, iterations_lin = linear_search(transactions_list, target_id)
        end_linear = time.perf_counter_ns()

        linear_duration_ns = (end_linear - start_linear) / repetitions

        # Benchmark Dictionary Lookup over repeated runs
        start_dict = time.perf_counter_ns()
        for _ in range(repetitions):
            record_dict, iterations_dict = dictionary_lookup(transactions_dict, target_id)
        end_dict = time.perf_counter_ns()

        dict_duration_ns = (end_dict - start_dict) / repetitions

        speedup = (linear_duration_ns / dict_duration_ns) if dict_duration_ns > 0 else 1.0

        total_linear_ns += linear_duration_ns
        total_dict_ns += dict_duration_ns
        total_linear_scans += iterations_lin
        total_dict_scans += iterations_dict

        results.append({
            "target_id": target_id,
            "found": record_lin is not None,
            "linear_scans": iterations_lin,
            "linear_time_ns": round(linear_duration_ns, 2),
            "linear_time_us": round(linear_duration_ns / 1000.0, 3),
            "dict_scans": iterations_dict,
            "dict_time_ns": round(dict_duration_ns, 2),
            "dict_time_us": round(dict_duration_ns / 1000.0, 3),
            "speedup_factor": round(speedup, 2),
        })

    num_ids = len(sample_ids)
    avg_linear_ns = total_linear_ns / num_ids
    avg_dict_ns = total_dict_ns / num_ids
    overall_speedup = (avg_linear_ns / avg_dict_ns) if avg_dict_ns > 0 else 1.0

    return {
        "dataset_size": len(transactions_list),
        "sample_size": num_ids,
        "repetitions_per_id": repetitions,
        "avg_linear_time_ns": round(avg_linear_ns, 2),
        "avg_linear_time_us": round(avg_linear_ns / 1000.0, 3),
        "avg_dict_time_ns": round(avg_dict_ns, 2),
        "avg_dict_time_us": round(avg_dict_ns / 1000.0, 3),
        "avg_linear_scans": round(total_linear_scans / num_ids, 1),
        "overall_speedup_factor": round(overall_speedup, 2),
        "individual_results": results,
    }


def format_markdown_table(summary: Dict[str, Any]) -> str:
    """Formats benchmark results into a clean Markdown report table."""
    lines = []
    lines.append(f"### Performance Benchmark Summary ({summary['sample_size']} Records Analyzed)")
    lines.append(f"- **Total Dataset Records**: {summary['dataset_size']}")
    lines.append(f"- **Repetitions per Search**: {summary['repetitions_per_id']} runs")
    lines.append(f"- **Average Linear Search Time**: `{summary['avg_linear_time_us']} µs` ({summary['avg_linear_time_ns']} ns)")
    lines.append(f"- **Average Dictionary Lookup Time**: `{summary['avg_dict_time_us']} µs` ({summary['avg_dict_time_ns']} ns)")
    lines.append(f"- **Overall Speedup Factor**: **{summary['overall_speedup_factor']}x faster** using Dictionary Lookup\n")

    lines.append("| Target ID | Found | Linear Scans | Linear Time (µs) | Dict Scans | Dict Time (µs) | Speedup Factor |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for item in summary["individual_results"]:
        found_str = "Yes" if item["found"] else "No"
        lines.append(
            f"| `{item['target_id']}` | {found_str} | {item['linear_scans']} | "
            f"`{item['linear_time_us']} µs` | {item['dict_scans']} | "
            f"`{item['dict_time_us']} µs` | **{item['speedup_factor']}x** |"
        )

    return "\n".join(lines)


def run_benchmark_suite(
    json_path: Path = DEFAULT_JSON_PATH,
    xml_path: Path = DEFAULT_XML_PATH
) -> Dict[str, Any]:
    """Loads data, selects 20+ distributed sample IDs, runs benchmarks, and prints results."""
    transactions = load_dataset(json_path, xml_path)
    total_records = len(transactions)

    # Select 20 sample IDs evenly distributed across beginning, middle, end, and 1 non-existent ID
    if total_records >= 20:
        step = max(1, total_records // 19)
        sample_ids = [transactions[i]["id"] for i in range(0, total_records, step)[:19]]
        sample_ids.append(999999)  # Non-existent ID test case
    else:
        sample_ids = [tx["id"] for tx in transactions]
        sample_ids.append(999999)

    summary = benchmark_search_methods(transactions, sample_ids, repetitions=500)
    report_table = format_markdown_table(summary)
    print(report_table)
    return summary


if __name__ == "__main__":
    run_benchmark_suite()
