"""Data Structures & Algorithms (DSA) Search Implementations.

Implements and compares:
1. Linear Search - Scans sequentially through a list of transactions to locate a record by ID (O(n)).
2. Dictionary Lookup - Direct key lookup in a Python dictionary (hash table) by ID (O(1)).
"""

from typing import Any, Dict, List, Optional, Tuple


def linear_search(
    transactions: List[Dict[str, Any]],
    target_id: int
) -> Tuple[Optional[Dict[str, Any]], int]:
    """Scans through a list of transaction dictionaries to find a record matching target_id.

    Time Complexity: O(n) worst/average case, where n is the length of the list.
    Space Complexity: O(1) auxiliary space.

    Args:
        transactions: List of transaction dictionaries.
        target_id: The transaction ID to search for.

    Returns:
        A tuple containing (matching_transaction_or_None, iteration_count).
    """
    iterations = 0
    for tx in transactions:
        iterations += 1
        if tx.get("id") == target_id:
            return tx, iterations
    return None, iterations


def build_transaction_dict(
    transactions: List[Dict[str, Any]]
) -> Dict[int, Dict[str, Any]]:
    """Converts a list of transaction dictionaries into an indexed dictionary keyed by transaction ID.

    Time Complexity: O(n) construction time.
    Space Complexity: O(n) space to store key-value pairs in memory.

    Args:
        transactions: List of transaction dictionaries.

    Returns:
        Dictionary mapping transaction ID to transaction record.
    """
    return {tx["id"]: tx for tx in transactions if "id" in tx}


def dictionary_lookup(
    transactions_dict: Dict[int, Dict[str, Any]],
    target_id: int
) -> Tuple[Optional[Dict[str, Any]], int]:
    """Performs a direct hash-table lookup for target_id in a pre-built dictionary.

    Time Complexity: O(1) average/amortized case.
    Space Complexity: O(1) auxiliary space for the lookup call.

    Args:
        transactions_dict: Dictionary mapping ID to transaction.
        target_id: The transaction ID to look up.

    Returns:
        A tuple containing (matching_transaction_or_None, lookup_operations).
    """
    # Hash lookup requires 1 direct index evaluation
    record = transactions_dict.get(target_id)
    return record, 1
