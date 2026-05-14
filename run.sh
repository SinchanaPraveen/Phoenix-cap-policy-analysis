#!/bin/bash
# run.sh – Start the backend and frontend concurrently.
# Usage: bash run.sh

set -e

# Resolve project root regardless of where the script is called from
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting FastAPI backend on http://localhost:8000 ..."
cd "$ROOT/backend"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Vite frontend on http://localhost:5173 ..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

# Trap Ctrl-C and kill both processes cleanly
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" SIGINT SIGTERM

wait $BACKEND_PID $FRONTEND_PID
