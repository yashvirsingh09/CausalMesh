#!/usr/bin/env bash
# run-dev.sh — Start CausalMesh Backend and Frontend in Development Mode

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "=================================================="
echo " Starting CausalMesh Development Environment"
echo "=================================================="

# Setup venv if missing
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "[1/3] Creating Python virtual environment..."
    cd "$BACKEND_DIR"
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Start Backend in background
echo "[2/3] Starting FastAPI Backend on http://localhost:8000..."
cd "$BACKEND_DIR"
./venv/bin/python main.py &
BACKEND_PID=$!

cleanup() {
    echo "Stopping CausalMesh backend (PID $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
}
trap cleanup EXIT

# Start Frontend
echo "[3/3] Starting Next.js Frontend on http://localhost:3001..."
cd "$FRONTEND_DIR"
npm run dev
