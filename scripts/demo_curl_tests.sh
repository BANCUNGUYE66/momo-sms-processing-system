#!/usr/bin/env bash
# Demo/validation script for the REST API (GET/POST/PUT/DELETE + Basic Auth).
# Usage: start the server first (python -m api.rest_api), then run this script.
set -uo pipefail

BASE_URL="${1:-http://localhost:8001}"
USER="admin"
PASS="momo1234"

echo "=== 1) GET /transactions (no credentials) -> expect 401 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$BASE_URL/transactions"

echo
echo "=== 2) GET /transactions (wrong credentials) -> expect 401 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -u wrong:pass "$BASE_URL/transactions"

echo
echo "=== 3) GET /transactions (authorized) -> expect 200 ==="
curl -s -u "$USER:$PASS" "$BASE_URL/transactions?limit=2"
echo

echo
echo "=== 4) GET /transactions/1 -> expect 200 ==="
curl -s -u "$USER:$PASS" "$BASE_URL/transactions/1"
echo

echo
echo "=== 5) POST /transactions (valid) -> expect 201 ==="
curl -s -o /tmp/post_resp.json -w "HTTP %{http_code}\n" -u "$USER:$PASS" -X POST "$BASE_URL/transactions" \
  -H "Content-Type: application/json" \
  -d '{"amount": 12000, "sender": "Aimable", "receiver": "Richard", "type": "TRANSFER"}'
cat /tmp/post_resp.json
NEW_ID=$(python3 -c "import json;print(json.load(open('/tmp/post_resp.json'))['id'])")
echo
echo "Created id: $NEW_ID"

echo
echo "=== 6) POST /transactions (missing required field) -> expect 400 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -u "$USER:$PASS" -X POST "$BASE_URL/transactions" \
  -H "Content-Type: application/json" \
  -d '{"amount": 500}'

echo
echo "=== 7) PUT /transactions/$NEW_ID (update amount) -> expect 200 ==="
curl -s -w "\nHTTP %{http_code}\n" -u "$USER:$PASS" -X PUT "$BASE_URL/transactions/$NEW_ID" \
  -H "Content-Type: application/json" \
  -d '{"amount": 20000}'

echo
echo "=== 8) PUT /transactions/999999 (nonexistent id) -> expect 404 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -u "$USER:$PASS" -X PUT "$BASE_URL/transactions/999999" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1}'

echo
echo "=== 9) DELETE /transactions/$NEW_ID -> expect 204 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -u "$USER:$PASS" -X DELETE "$BASE_URL/transactions/$NEW_ID"

echo
echo "=== 10) GET /transactions/$NEW_ID after delete -> expect 404 ==="
curl -s -w "\nHTTP %{http_code}\n" -u "$USER:$PASS" "$BASE_URL/transactions/$NEW_ID"

echo
echo "=== 11) DELETE /transactions/999999 (already gone) -> expect 404 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -u "$USER:$PASS" -X DELETE "$BASE_URL/transactions/999999"

echo
echo "Done. Review the HTTP codes above against the expectations in each section header."
