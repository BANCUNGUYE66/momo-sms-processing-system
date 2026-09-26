import base64
import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from api.rest_api import TransactionRequestHandler, ThreadingHTTPServer
from api.rest_config import API_USERNAME, API_PASSWORD

AUTH_HEADER = "Basic " + base64.b64encode(f"{API_USERNAME}:{API_PASSWORD}".encode()).decode()


@pytest.fixture(scope="module")
def server_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), TransactionRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def _request(url, method="GET", headers=None, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as resp:
            payload = resp.read()
            return resp.status, (json.loads(payload) if payload else None)
    except urllib.error.HTTPError as e:
        payload = e.read()
        return e.code, (json.loads(payload) if payload else None)


def test_unauthorized_without_credentials(server_url):
    status, data = _request(f"{server_url}/transactions")
    assert status == 401


def test_unauthorized_with_wrong_credentials(server_url):
    bad_header = "Basic " + base64.b64encode(b"wrong:wrong").decode()
    status, data = _request(f"{server_url}/transactions", headers={"Authorization": bad_header})
    assert status == 401


def test_list_transactions_authorized(server_url):
    status, data = _request(f"{server_url}/transactions", headers={"Authorization": AUTH_HEADER})
    assert status == 200
    assert isinstance(data, list)


def test_full_crud_cycle(server_url):
    headers = {"Authorization": AUTH_HEADER, "Content-Type": "application/json"}

    status, created = _request(
        f"{server_url}/transactions", method="POST", headers=headers,
        body={"amount": 5000, "sender": "Alice", "receiver": "Bob", "type": "TRANSFER"}
    )
    assert status == 201
    tx_id = created["id"]

    status, fetched = _request(f"{server_url}/transactions/{tx_id}", headers=headers)
    assert status == 200
    assert fetched["sender"] == "Alice"

    status, updated = _request(
        f"{server_url}/transactions/{tx_id}", method="PUT", headers=headers,
        body={"amount": 7500}
    )
    assert status == 200
    assert updated["amount"] == 7500.0

    status, _ = _request(f"{server_url}/transactions/{tx_id}", method="DELETE", headers=headers)
    assert status == 204

    status, _ = _request(f"{server_url}/transactions/{tx_id}", headers=headers)
    assert status == 404


def test_get_nonexistent_returns_404(server_url):
    status, _ = _request(f"{server_url}/transactions/999999", headers={"Authorization": AUTH_HEADER})
    assert status == 404
