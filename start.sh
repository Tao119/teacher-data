#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting FastAPI backend..."
cd "$ROOT"
PYTHONPATH=src:apps/api/src .venv/bin/uvicorn teacher_data_api.main:app \
  --host 0.0.0.0 --port 8000 --reload \
  --reload-dir src --reload-dir apps/api/src &
API_PID=$!

echo "Starting Next.js frontend..."
cd "$ROOT/apps/web"
npm run dev -- --hostname 0.0.0.0 &
WEB_PID=$!

echo ""
echo "  API: http://localhost:8000"
echo "  Web: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $API_PID $WEB_PID 2>/dev/null; exit" INT TERM
wait
