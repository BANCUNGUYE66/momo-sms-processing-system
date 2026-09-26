#!/usr/bin/env bash
# Run the plain-Python (http.server) REST API with Basic Auth
set -e

echo "Starting MoMo REST API (Basic Auth) on http://${REST_API_HOST:-0.0.0.0}:${REST_API_PORT:-8001} ..."
python -m api.rest_api
