#!/usr/bin/env bash
# Serve static dashboard frontend locally
PORT="${1:-8000}"

echo "Serving dashboard on http://localhost:$PORT ..."
python -m http.server "$PORT"
