# REST API Documentation — MoMo SMS Transactions

Plain-Python REST API (built with the standard-library `http.server`, no
frameworks) exposing CRUD access to MoMo SMS transaction records parsed from
`data/raw/modified_sms_v2.xml`.

- Implementation: [`api/rest_api.py`](../api/rest_api.py), [`api/data_store.py`](../api/data_store.py), [`api/auth.py`](../api/auth.py)
- Run it: `python -m api.rest_api` (listens on `http://0.0.0.0:8001` by default)

## Authentication

Every `/transactions` endpoint requires **HTTP Basic Authentication**.

- Default demo credentials: `admin` / `momo1234` (override with the `API_USERNAME` / `API_PASSWORD` environment variables — see `.env.example`).
- Missing or invalid credentials return **401 Unauthorized** with a `WWW-Authenticate: Basic` header.

Example header: `Authorization: Basic YWRtaW46bW9tbzEyMzQ=`

### Why Basic Auth is weak

Basic Auth only base64-encodes `username:password` — it is **not encrypted**,
so anyone able to observe the connection (no TLS/HTTPS) or read server/proxy
logs can trivially decode the credentials. The same static credentials are
resent on every single request, there is no expiry, no scoping of
permissions, and no way to revoke a single client without changing the
shared password for everyone.

**Stronger alternatives:**
- **JWT (JSON Web Tokens):** server issues a signed, time-limited token after
  login; the token (not the password) is sent on each request and can carry
  scopes/roles and be revoked/expired independently of the user's password.
- **OAuth2:** delegated authorization with short-lived access tokens, refresh
  tokens, and granular scopes — the standard choice when third-party apps
  need limited access without ever seeing the user's real credentials.
- At minimum, Basic Auth should only ever be used over **HTTPS/TLS**.

## Endpoints

### `GET /transactions`

List all transactions. Supports optional `limit` and `offset` query params.

**Request**
```bash
curl -u admin:momo1234 "http://localhost:8001/transactions?limit=2"
```

**Response `200 OK`**
```json
[
  {
    "id": 1,
    "type": "RECEIVED",
    "amount": 2000.0,
    "sender": "Jane Smith",
    "receiver": "Own Account",
    "timestamp": "2024-05-10T17:30:58.724000",
    "raw_text": "You have received 2000 RWF from Jane Smith ..."
  },
  {
    "id": 2,
    "type": "PAYMENT",
    "amount": 1000.0,
    "sender": "Own Account",
    "receiver": "Jane Smith",
    "timestamp": "2024-05-10T17:31:46.754000",
    "raw_text": "TxId: 73214484437. Your payment of 1,000 RWF to Jane Smith ..."
  }
]
```

**Errors:** `401 Unauthorized` (bad/missing credentials)

---

### `GET /transactions/{id}`

Fetch a single transaction by id.

**Request**
```bash
curl -u admin:momo1234 http://localhost:8001/transactions/1
```

**Response `200 OK`**
```json
{
  "id": 1,
  "type": "RECEIVED",
  "amount": 2000.0,
  "sender": "Jane Smith",
  "receiver": "Own Account",
  "timestamp": "2024-05-10T17:30:58.724000",
  "raw_text": "You have received 2000 RWF from Jane Smith ..."
}
```

**Errors:**
- `400 Bad Request` — id is not an integer
- `401 Unauthorized` — bad/missing credentials
- `404 Not Found` — no transaction with that id

---

### `POST /transactions`

Create a new transaction. Required fields: `amount`, `sender`, `receiver`.
Optional: `type` (default `"OTHER"`), `timestamp` (default: now), `raw_text`.

**Request**
```bash
curl -u admin:momo1234 -X POST http://localhost:8001/transactions \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "sender": "Alice", "receiver": "Bob", "type": "TRANSFER"}'
```

**Response `201 Created`**
```json
{
  "id": 1694,
  "type": "TRANSFER",
  "amount": 5000.0,
  "sender": "Alice",
  "receiver": "Bob",
  "timestamp": "2026-09-25T09:00:00.000000",
  "raw_text": ""
}
```

**Errors:**
- `400 Bad Request` — invalid JSON, missing required fields, or non-numeric `amount`
- `401 Unauthorized` — bad/missing credentials

---

### `PUT /transactions/{id}`

Update an existing transaction. Any subset of `type`, `amount`, `sender`,
`receiver`, `timestamp`, `raw_text` may be sent; only provided fields change.

**Request**
```bash
curl -u admin:momo1234 -X PUT http://localhost:8001/transactions/1694 \
  -H "Content-Type: application/json" \
  -d '{"amount": 7500}'
```

**Response `200 OK`**
```json
{
  "id": 1694,
  "type": "TRANSFER",
  "amount": 7500.0,
  "sender": "Alice",
  "receiver": "Bob",
  "timestamp": "2026-09-25T09:00:00.000000",
  "raw_text": ""
}
```

**Errors:**
- `400 Bad Request` — id not an integer, invalid JSON, or non-numeric `amount`
- `401 Unauthorized` — bad/missing credentials
- `404 Not Found` — no transaction with that id

---

### `DELETE /transactions/{id}`

Delete a transaction.

**Request**
```bash
curl -u admin:momo1234 -X DELETE http://localhost:8001/transactions/1694
```

**Response:** `204 No Content` (empty body)

**Errors:**
- `400 Bad Request` — id not an integer
- `401 Unauthorized` — bad/missing credentials
- `404 Not Found` — no transaction with that id

## Error code summary

| Code | Meaning                                              |
| ---- | ----------------------------------------------------- |
| 200  | Success (GET, PUT)                                     |
| 201  | Resource created (POST)                                |
| 204  | Resource deleted, no body (DELETE)                     |
| 400  | Malformed request (bad id, bad JSON, missing/invalid field) |
| 401  | Missing or invalid Basic Auth credentials              |
| 404  | Transaction id not found                               |
| 405  | HTTP method not supported on that path                 |
