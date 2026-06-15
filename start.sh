#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# Activate venv
source venv/bin/activate

# Cleanup handler
cleanup() {
    echo ""
    echo "Shutting down THE EYE..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait 2>/dev/null || true
    echo "Stopped."
}
trap cleanup EXIT INT TERM

# Remove old DB on schema changes (comment out to keep data)
# rm -f the_eye.db

echo "============================================"
echo "        𓂀  THE EYE — Starting"
echo "============================================"

# Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop"
echo "============================================"

wait
