# MoMo SMS Processing System — DSA Integration & Performance Analysis

**Course**: Enterprise Software Development  
**Project**: MoMo SMS Data Processing & Analytics System  
**Author**: Jean de Dieu Tuyishime (XML Parsing & DSA Specialist)  
**Team**: Aimable (Lead), Jean de Dieu Tuyishime, Eloi  

---

## 1. Executive Summary

This document details the design, implementation, and empirical evaluation of the Data Structures & Algorithms (DSA) module (`dsa/`) developed for the MoMo SMS Data Processing System. The module translates unstructured XML mobile money transaction logs into structured JSON objects and compares the efficiency of **Linear Search ($O(n)$)** versus **Dictionary Lookup ($O(1)$)** for transaction retrieval.

---

## 2. XML Data Parsing & JSON Conversion (`dsa/xml_parser.py`)

### 2.1 Parsing Architecture
The parsing engine (`dsa/xml_parser.py`) processes raw XML exports containing `<sms>` nodes (such as `data/raw/modified_sms_v2.xml`) using Python's standard `xml.etree.ElementTree`. 

Each SMS text body is evaluated against regular expression rules to extract:
1. **Transaction ID**: Unique sequential integer assigned during ingestion.
2. **Transaction Type**: Categorized into `RECEIVED`, `PAYMENT`, `TRANSFER`, `DEPOSIT`, or `AIRTIME`.
3. **Monetary Amount**: Extracted in Rwandan Francs (`RWF`) and cast to `DECIMAL`/`float`.
4. **Parties Involved**: Sender and receiver names extracted or mapped to `Own Account`, `Bank`, or `Airtime`.
5. **Timestamp**: Millisecond epoch dates (`date="1715351458724"`) converted to standard ISO 8601 strings.
6. **Raw Text**: Preserved original message body for auditability.

### 2.2 Sample Exported JSON Object
Executing `python -m dsa.xml_parser` parses **1,691 XML records** and exports them to `data/processed/transactions.json`:

```json
[
  {
    "id": 1,
    "type": "RECEIVED",
    "amount": 2000.0,
    "sender": "Jane Smith",
    "receiver": "Own Account",
    "timestamp": "2024-05-10T16:30:58.724000",
    "raw_text": "You have received 2000 RWF from Jane Smith (*********013) on your mobile money account at 2024-05-10 16:30:51. Message from sender: . Your new balance:2000 RWF. Financial Transaction Id: 76662021700."
  },
  {
    "id": 2,
    "type": "PAYMENT",
    "amount": 1000.0,
    "sender": "Own Account",
    "receiver": "Samuel Carter",
    "timestamp": "2024-05-10T16:31:46.754000",
    "raw_text": "TxId: 73214484437. Your payment of 1,000 RWF to Samuel Carter 12845 has been completed at 2024-05-10 16:31:39. Your new balance: 1,000 RWF. Fee was 0 RWF."
  }
]
```

---

## 3. Data Structures & Search Algorithms (`dsa/search.py`)

### 3.1 Linear Search ($O(n)$)
Linear search iterates through a sequential array (`list[dict]`) from index $0$ to $n-1$, inspecting the `id` field of each dictionary until a match is found or the end of the array is reached.

- **Best-Case Time Complexity**: $O(1)$ — Target record is at index $0$.
- **Average-Case Time Complexity**: $O(n)$ — Target record is in the middle ($\approx n/2$ iterations).
- **Worst-Case Time Complexity**: $O(n)$ — Target record is at index $n-1$ or not present ($n$ iterations).
- **Auxiliary Space Complexity**: $O(1)$ — No additional data structures allocated.

### 3.2 Dictionary Lookup ($O(1)$)
Dictionary lookup builds an indexed Python dictionary (`dict[int, dict]`) mapping transaction `id` directly to its record reference using an underlying Hash Table.

- **Construction Time Complexity**: $O(n)$ — One-time pass to populate the hash map.
- **Lookup Time Complexity**: $O(1)$ average/amortized case — Direct hash value computation ($h(k) \pmod m$) and bucket index access.
- **Worst-Case Lookup Complexity**: $O(n)$ — Severe hash collision degradation (extremely rare in Python's SipHash algorithm).
- **Space Complexity**: $O(n)$ memory to store the hash table bucket array.

---

## 4. Empirical Performance Benchmarking (`dsa/benchmark.py`)

### 4.1 Benchmark Setup & Methodology
- **Dataset**: 1,691 parsed MoMo SMS transaction records.
- **Sample Target Selection**: 20 target IDs distributed across the dataset (beginning, middle, end array positions, plus 1 non-existent ID test case `999999`).
- **Timing Tool**: `time.perf_counter_ns()` executed over **500 repetitions per ID** to eliminate system jitter.

### 4.2 Benchmark Results Table (20 Sample Records)

| Target ID | Record Found | Linear Scans | Linear Time (µs) | Dict Scans | Dict Time (µs) | Speedup Factor |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `1` | Yes | 1 | `0.595 µs` | 1 | `0.463 µs` | **1.28x** |
| `90` | Yes | 90 | `10.383 µs` | 1 | `0.221 µs` | **46.94x** |
| `179` | Yes | 179 | `22.582 µs` | 1 | `0.165 µs` | **137.03x** |
| `268` | Yes | 268 | `33.580 µs` | 1 | `0.163 µs` | **206.52x** |
| `357` | Yes | 357 | `40.509 µs` | 1 | `0.155 µs` | **261.01x** |
| `446` | Yes | 446 | `58.705 µs` | 1 | `0.150 µs` | **390.32x** |
| `535` | Yes | 535 | `103.440 µs` | 1 | `0.180 µs` | **574.67x** |
| `624` | Yes | 624 | `100.806 µs` | 1 | `0.161 µs` | **626.12x** |
| `713` | Yes | 713 | `98.026 µs` | 1 | `0.156 µs` | **627.57x** |
| `802` | Yes | 802 | `171.868 µs` | 1 | `1.353 µs` | **127.06x** |
| `891` | Yes | 891 | `181.467 µs` | 1 | `0.189 µs` | **958.11x** |
| `980` | Yes | 980 | `161.287 µs` | 1 | `0.531 µs` | **303.86x** |
| `1069` | Yes | 1069 | `222.196 µs` | 1 | `0.163 µs` | **1366.52x** |
| `1158` | Yes | 1158 | `220.751 µs` | 1 | `0.152 µs` | **1450.40x** |
| `1247` | Yes | 1247 | `243.183 µs` | 1 | `0.159 µs` | **1529.45x** |
| `1336` | Yes | 1336 | `362.077 µs` | 1 | `0.161 µs` | **2254.53x** |
| `1425` | Yes | 1425 | `465.841 µs` | 1 | `0.515 µs` | **904.90x** |
| `1514` | Yes | 1514 | `598.133 µs` | 1 | `0.156 µs` | **3834.19x** |
| `1603` | Yes | 1603 | `269.661 µs` | 1 | `0.174 µs` | **1548.00x** |
| `999999` (Missing) | No | 1691 | `358.687 µs` | 1 | `0.384 µs` | **934.57x** |

### 4.3 Benchmark Summary Statistics
- **Total Dataset Size**: 1,691 records
- **Average Linear Search Execution Time**: `186.19 µs` (186,188.83 ns)
- **Average Dictionary Lookup Execution Time**: `0.28 µs` (287.53 ns)
- **Overall Performance Gain**: **647.55x faster** using Dictionary Lookup.

---

## 5. Rubric Reflection & Technical Analysis

### Reflection 1: Why is Dictionary Lookup faster than Linear Search?
1. **Hash Table Direct Indexing ($O(1)$)**:
   A Python dictionary uses an underlying hash table. When searching for `target_id`, Python evaluates `hash(target_id) % table_capacity` to compute the exact memory address bucket where the pointer resides. This operation takes constant $O(1)$ time regardless of whether the dataset contains 10 records or 10,000,000 records.
2. **Sequential Traversal Overhead ($O(n)$)**:
   In contrast, Linear Search must sequentially traverse the array. For each element, Python must perform pointer dereferencing, dictionary key lookup (`tx["id"]`), and integer equality evaluation. As target IDs appear deeper in the array (e.g., index 1514), the number of CPU instructions scales linearly with array depth.
3. **Cache Line & CPU Execution Efficiency**:
   Dictionary lookup executes in a fixed number of CPU clock cycles (~1-2 memory jumps), whereas linear search causes repeated cache misses and loop branch predictions for large array scans.

---

### Reflection 2: What other Data Structures or Algorithms could improve search efficiency?

1. **Binary Search on a Sorted Array ($O(\log n)$)**:
   - *Mechanics*: If transactions are stored in a contiguous array sorted by `id` or `timestamp`, Binary Search repeatedly divides the search interval in half.
   - *Efficiency*: Requires $O(\log_2 n)$ operations ($\approx 11$ comparisons for 1,691 records vs up to 1,691 for linear search).
   - *Tradeoff*: Excellent space efficiency ($O(1)$ extra memory), but array insertions require $O(n)$ shift operations.

2. **Self-Balancing Binary Search Trees (AVL / Red-Black Trees) ($O(\log n)$)**:
   - *Mechanics*: Maintains ordered transactions in a balanced tree structure where every left node is smaller and right node is larger.
   - *Efficiency*: Guarantees $O(\log n)$ search, insertion, and deletion times.
   - *Use Case*: Ideal for dynamic streaming datasets where records are frequently added or deleted while maintaining range queries.

3. **B-Trees & B+ Trees (Database Disk Indexing)**:
   - *Mechanics*: Multi-way search trees optimized for reading and writing large blocks of memory/disk storage.
   - *Efficiency*: Reduces disk I/O operations to $O(\log_B n)$, where $B$ is the block branching factor (e.g. 100-1000 keys per node).
   - *Use Case*: Standard data structure behind relational database primary keys (MySQL InnoDB `PRIMARY KEY` indexes).

4. **Multi-Attribute Secondary Hash Indexes**:
   - *Mechanics*: In addition to primary key `dict[id -> tx]`, maintaining auxiliary dictionaries such as `dict[sender -> list[tx]]` or `dict[category -> list[tx]]`.
   - *Efficiency*: Enables $O(1)$ retrieval for non-ID queries (e.g., retrieving all payments made to "Samuel Carter").

---

## 6. Integration with REST API (`api/data_store.py`)

The REST API implemented in `api/data_store.py` leverages this dictionary lookup architecture (`TransactionStore` class):

```python
class TransactionStore:
    def __init__(self, xml_path: Path):
        seed = parse_transactions_from_xml(xml_path)
        # Pre-indexes transactions into a Python dict for O(1) GET/PUT/DELETE operations
        self._by_id: Dict[int, Dict[str, Any]] = {tx["id"]: tx for tx in seed}

    def get(self, tx_id: int) -> Optional[Dict[str, Any]]:
        return self._by_id.get(tx_id)  # O(1) instant lookup
```

This guarantees that API requests (`GET /transactions/{id}`, `PUT /transactions/{id}`, `DELETE /transactions/{id}`) execute in constant time $O(1)$, ensuring high scalability under concurrent HTTP traffic.
