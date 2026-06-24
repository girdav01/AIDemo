#!/usr/bin/env bash
# Launch the TrendAI Vision One AI Security Challenge booth app.
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then set -a; . ./.env; set +a; fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

# Persist passports + leaderboard to SQLite so a restart doesn't wipe the board.
export BOOTH_PERSIST="${BOOTH_PERSIST:-1}"
export BOOTH_DB="${BOOTH_DB:-booth_state.db}"

if ! python3 -c "import fastapi" >/dev/null 2>&1; then
  echo "Installing dependencies…"
  python3 -m pip install -r requirements.txt
fi

echo "Booth app:    http://localhost:${PORT}/"
echo "Big screen:   http://localhost:${PORT}/screen"
exec python3 -m uvicorn app.main:app --host "$HOST" --port "$PORT"
