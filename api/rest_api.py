"""Plain-Python REST API (http.server) for MoMo SMS transactions.

Endpoints (all require HTTP Basic Auth):
  GET    /transactions       -> list all transactions
  GET    /transactions/{id}  -> view one transaction
  POST   /transactions       -> create a new transaction
  PUT    /transactions/{id}  -> update an existing transaction
  DELETE /transactions/{id}  -> delete a transaction

Run directly with: python -m api.rest_api
"""
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from api.auth import is_authorized
from api.data_store import store
from api.rest_config import API_HOST, API_PORT

_TRANSACTIONS_ID_RE = re.compile(r"^/transactions/(?P<id>[^/]+)$")


class TransactionRequestHandler(BaseHTTPRequestHandler):
    server_version = "MoMoRestAPI/1.0"

    # -- helpers ---------------------------------------------------------
    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message})

    def _require_auth(self) -> bool:
        if is_authorized(self.headers.get("Authorization")):
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="MoMo SMS API"')
        self.send_header("Content-Type", "application/json")
        body = json.dumps({"error": "Unauthorized: invalid or missing credentials"}).encode("utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return False

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _parse_id(self, raw_id: str):
        try:
            return int(raw_id)
        except (TypeError, ValueError):
            return None

    # -- routing -----------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            # Public health-check so visiting the bare host in a browser doesn't 401.
            return self._send_json(200, {"message": "MoMo SMS REST API is running", "docs": "/transactions"})

        if not self._require_auth():
            return
        if parsed.path == "/transactions":
            query = parse_qs(parsed.query)
            limit = int(query["limit"][0]) if "limit" in query else None
            offset = int(query["offset"][0]) if "offset" in query else 0
            self._send_json(200, store.list_all(limit=limit, offset=offset))
            return

        match = _TRANSACTIONS_ID_RE.match(parsed.path)
        if match:
            tx_id = self._parse_id(match.group("id"))
            if tx_id is None:
                return self._send_error_json(400, "Transaction id must be an integer")
            record = store.get(tx_id)
            if record is None:
                return self._send_error_json(404, f"Transaction {tx_id} not found")
            return self._send_json(200, record)

        self._send_error_json(404, "Not found")

    def do_POST(self):
        if not self._require_auth():
            return
        if urlparse(self.path).path != "/transactions":
            return self._send_error_json(405, "Method not allowed on this path")

        try:
            data = self._read_json_body()
        except json.JSONDecodeError:
            return self._send_error_json(400, "Invalid JSON body")

        if "amount" not in data or "sender" not in data or "receiver" not in data:
            return self._send_error_json(400, "Fields 'amount', 'sender', and 'receiver' are required")
        try:
            data["amount"] = float(data["amount"])
        except (TypeError, ValueError):
            return self._send_error_json(400, "Field 'amount' must be numeric")

        record = store.create(data)
        self._send_json(201, record)

    def do_PUT(self):
        if not self._require_auth():
            return
        match = _TRANSACTIONS_ID_RE.match(urlparse(self.path).path)
        if not match:
            return self._send_error_json(405, "Method not allowed on this path")

        tx_id = self._parse_id(match.group("id"))
        if tx_id is None:
            return self._send_error_json(400, "Transaction id must be an integer")

        try:
            data = self._read_json_body()
        except json.JSONDecodeError:
            return self._send_error_json(400, "Invalid JSON body")

        if "amount" in data:
            try:
                data["amount"] = float(data["amount"])
            except (TypeError, ValueError):
                return self._send_error_json(400, "Field 'amount' must be numeric")

        record = store.update(tx_id, data)
        if record is None:
            return self._send_error_json(404, f"Transaction {tx_id} not found")
        self._send_json(200, record)

    def do_DELETE(self):
        if not self._require_auth():
            return
        match = _TRANSACTIONS_ID_RE.match(urlparse(self.path).path)
        if not match:
            return self._send_error_json(405, "Method not allowed on this path")

        tx_id = self._parse_id(match.group("id"))
        if tx_id is None:
            return self._send_error_json(400, "Transaction id must be an integer")

        if not store.delete(tx_id):
            return self._send_error_json(404, f"Transaction {tx_id} not found")
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A002 - matches BaseHTTPRequestHandler signature
        pass


def run(host: str = API_HOST, port: int = API_PORT) -> None:
    server = ThreadingHTTPServer((host, port), TransactionRequestHandler)
    print(f"MoMo REST API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    run()
