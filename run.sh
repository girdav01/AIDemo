#!/usr/bin/env bash
# Launch the TrendAI Vision One AI Security Challenge booth app.
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then set -a; . ./.env; set +a; fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

if ! python3 -c "import fastapi" >/dev/null 2>&1; then
  echo "Installing dependencies…"
  python3 -m pip install -r requirements.txt
fi

echo "Booth app:    http://localhost:${PORT}/"
echo "Big screen:   http://localhost:${PORT}/screen"
exec python3 -m uvicorn app.main:app --host "$HOST" --port "$PORT"
