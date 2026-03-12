#!/usr/bin/env bash
# deploy.sh — deploy VYUD-AI-Scheduler to the server and restart Flask
#
# Usage (run on the server):
#   bash scripts/deploy.sh
#
# Requirements:
#   - git is installed and the repo is already cloned
#   - The virtualenv (if used) is activated before running this script
#   - Flask is managed by systemd under the unit name "vyud-flask"
#     (change SERVICE_NAME below if your unit has a different name)
#
# Example (run from outside the server via SSH):
#   ssh user@your-server "cd /path/to/VYUD-AI-Scheduler && bash scripts/deploy.sh"

set -euo pipefail

SERVICE_NAME="${FLASK_SERVICE_NAME:-vyud-flask}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== VYUD-AI-Scheduler deploy ==="
echo "Repo : $REPO_DIR"
echo "Service: $SERVICE_NAME"
echo ""

cd "$REPO_DIR"

# 1. Pull latest code from main branch
echo "[1/4] Pulling latest code..."
git fetch origin
git pull --ff-only origin main
echo "      Done."

# 2. Install / update Python dependencies
echo "[2/4] Installing Python dependencies..."
pip install -r requirements.txt
echo "      Done."

# 3. Run DB migration for any NULL timestamps (idempotent)
echo "[3/4] Running NULL timestamp migration..."
python scripts/fix_null_timestamps.py
echo "      Done."

# 4. Restart Flask service
echo "[4/4] Restarting Flask service ($SERVICE_NAME)..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl restart "$SERVICE_NAME"
    echo "      Restarted."
else
    echo "      WARNING: Service '$SERVICE_NAME' is not running. Starting it now..."
    sudo systemctl start "$SERVICE_NAME"
    echo "      Started."
fi

echo ""
echo "=== Deploy complete ==="
echo "Check status: sudo systemctl status $SERVICE_NAME"
echo "Check logs  : sudo journalctl -u $SERVICE_NAME -n 50"
