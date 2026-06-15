#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "============================================"
echo "        𓂀  THE EYE — Setup Script"
echo "============================================"

# ---- System dependencies ----
echo "[1/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv nodejs npm nmap whois sqlite3 >/dev/null 2>&1

# ---- Optional OSINT tools (skip gracefully if fail) ----
echo "[2/6] Installing optional OSINT tools..."
pip3 install sherlock theHarvester 2>/dev/null || echo "  (sherlock/theHarvester not installed — stages skip gracefully)"

# ---- Python virtual environment ----
echo "[3/6] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[4/6] Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# ---- Frontend dependencies ----
echo "[5/6] Installing frontend dependencies..."
cd "$ROOT_DIR/frontend"
npm install --silent 2>/dev/null
cd "$ROOT_DIR"

# ---- Default .env file ----
echo "[6/6] Creating default .env (if missing)..."
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
DATABASE_URL=sqlite+aiosqlite:///./the_eye.db
GROQ_API_KEY_1=
GROQ_API_KEY_2=
OPENROUTER_API_KEY_1=
OPENROUTER_API_KEY_2=
AI_PROVIDER_PRIORITY=groq,openrouter,template
NMAP_PATH=auto
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
HEARTBEAT_SECONDS=30
PIPELINE_MAX_NEW_TARGETS=50
ENVEOF
    echo "  Created .env — edit to add API keys if desired"
fi

echo ""
echo "============================================"
echo "  Setup complete. Run:  ./start.sh"
echo "============================================"
